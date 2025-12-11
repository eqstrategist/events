# ui/event_forms.py

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO

from core.utils import generate_title
from core.storage import save_events, append_audit


# --------------------------------------------------------------------
# Helper functions
# --------------------------------------------------------------------
def _get_marked_rows(df: pd.DataFrame):
    """Return only rows that represent marked/blocked dates."""
    if "Is Marked" not in df.columns:
        return pd.DataFrame(columns=df.columns)
    return df[df["Is Marked"] == True].copy()


def _is_date_blocked_for_any_trainer(df_marked: pd.DataFrame, day_date):
    """
    Legacy/global check: is this date blocked at all?
    (Used as a fallback if you are not yet doing trainer-specific blocking.)
    """
    if df_marked.empty:
        return False
    return (pd.to_datetime(df_marked["Date"]).dt.date == day_date).any()


# --------------------------------------------------------------------
# TAB 1 – NEW EVENT
# --------------------------------------------------------------------
def new_event_tab(
    df: pd.DataFrame,
    user_email: str,
    TRAINERS,
    TYPES,
    STATUSES,
    SOURCES,
    MEDIUMS,
    LOCATIONS,
    DEFAULT_TYPE,
    DEFAULT_STATUS,
    DEFAULT_SOURCE,
    DEFAULT_MEDIUM,
    DEFAULT_LOCATION,
):
    """
    TAB 1 – New Event (for admin)

    Adds a confirmation step anytime the date range is > 5 days.
    IMPORTANT: clear_on_submit=False so the form is NOT wiped on a failed submit.
    """

    st.header("Add New Event")

    # NOTE: clear_on_submit=False so we don't lose field values on failed validation
    with st.form("add_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)

        # ---------------- Date, Type, Status & Source ----------------
        with c1:
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date", value=start_date)
            st.info("💡 For single-day events, set End Date same as Start Date")

        with c2:
            type_ = st.selectbox("Type", TYPES, index=TYPES.index(DEFAULT_TYPE))

            # STATUSES[0] is "All" – for creating we skip that
            real_statuses = STATUSES[1:] if STATUSES and STATUSES[0] == "All" else STATUSES
            status = st.selectbox(
                "Status",
                real_statuses,
                index=real_statuses.index(DEFAULT_STATUS) if DEFAULT_STATUS in real_statuses else 0,
            )

            real_sources = SOURCES[1:] if SOURCES and SOURCES[0] == "All" else SOURCES
            source = st.selectbox(
                "Source",
                real_sources,
                index=real_sources.index(DEFAULT_SOURCE) if DEFAULT_SOURCE in real_sources else 0,
            )

        with c3:
            client = st.text_input("Client")
            course = st.text_input("Course / Description")
            trainer = st.multiselect(
                "Trainer Calendar",
                ["All"] + TRAINERS,
                default=None,
                help="Select 'All' to show on all trainers' calendars, or select specific trainer(s)",
            )
            medium = st.selectbox(
                "Medium",
                MEDIUMS,
                index=MEDIUMS.index(DEFAULT_MEDIUM) if DEFAULT_MEDIUM in MEDIUMS else 0,
            )

        location = st.selectbox(
            "Location",
            LOCATIONS,
            index=LOCATIONS.index(DEFAULT_LOCATION) if DEFAULT_LOCATION in LOCATIONS else 0,
        )
        billing = st.text_area("Billing Notes")
        invoiced = st.selectbox("Invoiced", ["No", "Yes"], index=0)
        notes = st.text_area("Additional Notes")

        # ---------- Date range confirmation ----------
        num_days = (end_date - start_date).days + 1
        long_range = num_days > 5

        if long_range:
            st.warning(
                f"⚠️ You selected a date range of **{num_days} days**.\n\n"
                "This will create **one event PER DAY** in that range."
            )
            confirm_long = st.checkbox(
                "I understand and want to create events for this entire date range.",
                key="confirm_add_long_range",
            )
        else:
            confirm_long = True  # no extra confirmation needed for ≤ 5 days

        submitted = st.form_submit_button("Save Event", use_container_width=True)

    # -------- Handle submission OUTSIDE the with-block --------
    if not submitted:
        return df

    # Basic validations
    if not trainer:
        st.error("❌ Please select at least one trainer!")
        return df

    if end_date < start_date:
        st.error("❌ End Date cannot be before Start Date!")
        return df

    if not confirm_long:
        # We reached here only for long ranges with unchecked confirmation
        st.error(
            "❌ Please tick the confirmation box above to create events for this long date range."
        )
        return df

    # ---------- Check for globally marked dates (legacy behaviour) ----------
    df_marked = _get_marked_rows(df)
    blocked_dates = []
    current_check = start_date
    while current_check <= end_date:
        if _is_date_blocked_for_any_trainer(df_marked, current_check):
            blocked_dates.append(current_check.strftime("%Y-%m-%d"))
        current_check += timedelta(days=1)

    if blocked_dates:
        st.error(
            "❌ Cannot create event(s)! The following date(s) are marked/blocked: "
            + ", ".join(blocked_dates)
        )
        return df

    # ---------- Create events ----------
    if "All" in trainer:
        trainer_list = ", ".join(TRAINERS)
    else:
        trainer_list = ", ".join(trainer)

    events_to_add = []
    current_date = start_date

    while current_date <= end_date:
        new_row = {
            "Date": current_date,
            "Type": type_,
            "Status": status,
            "Source": source,
            "Client": client,
            "Course/Description": course,
            "Trainer Calendar": trainer_list,
            "Medium": medium,
            "Location": location,
            "Billing": billing,
            "Invoiced": invoiced,
            "Notes": notes,
            "Date Modified": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Action Type": "Created",
            "Modified By": user_email,
            "Is Marked": False,
        }
        new_row["Title"] = generate_title(new_row)
        events_to_add.append(new_row)
        current_date += timedelta(days=1)

    df = pd.concat([df, pd.DataFrame(events_to_add)], ignore_index=True)
    save_events(df)
    append_audit(user_email, "New Event", f"{len(events_to_add)} day(s)")

    if num_days == 1:
        st.success("✅ Event added successfully!")
    else:
        st.success(f"✅ {num_days} events added successfully (one for each day)!")

    # Trigger a fresh run
    st.rerun()

    # (Won't actually be reached, but kept for clarity)
    return df


# --------------------------------------------------------------------
# TAB 2 – MANAGE EVENTS
# --------------------------------------------------------------------
def manage_events_tab(
    df: pd.DataFrame,
    user_email: str,
    TRAINERS,
    STATUSES,
    SOURCES,
    LOCATIONS,
    MEDIUMS,
    TYPES,
    RULE_BLOCK_PREVENT_DUPLICATES: bool,
):
    """
    TAB 2 – Manage Events (for admin)
    Includes:
      - Filters
      - Single event edit (with date-range confirmation > 5 days)
      - Bulk edit
      - Duplicate
      - Delete
      - NEW: Select-all for all filtered events
    """
    st.header("Manage Events")

    # ---------------- Filters ----------------
    st.subheader("🔍 Filter Events")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        use_date_range = st.checkbox("Filter by Date Range", value=False)
        if use_date_range:
            date_from = st.date_input("From Date", key="mng_date_from")
            date_to = st.date_input("To Date", key="mng_date_to")
        else:
            date_from = date_to = None

    trainer_filter = col2.selectbox("Trainer", ["All"] + TRAINERS, key="mng_trainer")
    status_filter = col3.selectbox("Status", STATUSES, key="mng_status")
    source_filter = col4.selectbox("Source", SOURCES, key="mng_source")
    client_search = col5.text_input(
        "Client", key="mng_client", placeholder="Search client..."
    )

    result = df.copy()

    if use_date_range and date_from and date_to:
        if date_to < date_from:
            st.warning("⚠️ 'To Date' cannot be before 'From Date'")
        else:
            result = result[
                (pd.to_datetime(result["Date"]).dt.date >= date_from)
                & (pd.to_datetime(result["Date"]).dt.date <= date_to)
            ]

    if trainer_filter != "All":
        # Use contains to handle multi-trainer rows
        result = result[
            result["Trainer Calendar"]
            .astype(str)
            .str.contains(trainer_filter, case=False, na=False)
        ]
    if status_filter != "All":
        result = result[result["Status"] == status_filter]
    if source_filter != "All":
        result = result[result["Source"] == source_filter]
    if client_search:
        result = result[
            result["Client"].astype(str).str.contains(client_search, case=False, na=False)
        ]

    st.write(f"**Showing {len(result)} events**")

    if len(result) == 0:
        st.info("No events found with current filters.")
        return df

    # ---------------- Selection + Download ----------------
    st.write("### Select Events for Bulk Operations")

    # 🔹 NEW: master "select all filtered events" checkbox
    select_all = st.checkbox("Select all filtered events", key="mng_select_all")

    # If "select all" is ticked, mark all row checkboxes TRUE in session_state
    # BEFORE their widgets are created. This is allowed in Streamlit.
    if select_all:
        for idx2 in result.index:
            st.session_state[f"mng_check_{idx2}"] = True

    selected_events = []
    for idx in result.index:
        col_a, col_b = st.columns([0.1, 0.9])
        with col_a:
            checked = st.checkbox("", key=f"mng_check_{idx}")
            if checked:
                selected_events.append(idx)
        with col_b:
            date_str = pd.to_datetime(result.loc[idx, "Date"]).strftime("%Y-%m-%d")
            st.write(f"**{result.loc[idx, 'Title']}** - {date_str}")

    st.divider()

    st.dataframe(result, use_container_width=True)

    towrite = BytesIO()
    result.to_excel(towrite, index=False, engine="openpyxl")
    towrite.seek(0)
    st.download_button(
        "⬇️ Download Filtered Data",
        data=towrite,
        file_name="Filtered_Events.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.divider()

    if len(selected_events) == 0:
        st.info("👆 Select events using the checkboxes above to perform bulk operations")
        return df

    st.write(f"### 🎯 {len(selected_events)} Event(s) Selected")

    # ============================ SINGLE EVENT SELECTED ============================
    if len(selected_events) == 1:
        op_tab1, op_tab2, op_tab3 = st.tabs(["✏️ Edit Event", "📋 Duplicate", "🗑️ Delete"])

        selected_idx = selected_events[0]

        # ---- Single edit ----
        with op_tab1:
            selected_event = df.loc[selected_idx]
            st.write(f"**Editing:** {selected_event['Title']}")
            st.divider()

            # Note: clear_on_submit=False; we keep it that way
            with st.form("single_edit_form", clear_on_submit=False):
                st.subheader("Edit Event Details")

                c1, c2, c3 = st.columns(3)
                with c1:
                    edit_start_date = st.date_input(
                        "Start Date",
                        value=pd.to_datetime(selected_event["Date"]).date(),
                    )
                    edit_end_date = st.date_input(
                        "End Date",
                        value=pd.to_datetime(selected_event["Date"]).date(),
                    )
                    st.info("💡 Changing dates will create separate events for each day")

                with c2:
                    edit_type = st.selectbox(
                        "Type",
                        TYPES,
                        index=TYPES.index(selected_event["Type"]),
                    )

                    real_statuses = (
                        STATUSES[1:]
                        if STATUSES and STATUSES[0] == "All"
                        else STATUSES
                    )
                    edit_status = st.selectbox(
                        "Status",
                        real_statuses,
                        index=real_statuses.index(selected_event["Status"])
                        if selected_event["Status"] in real_statuses
                        else 0,
                    )

                    real_sources = (
                        SOURCES[1:]
                        if SOURCES and SOURCES[0] == "All"
                        else SOURCES
                    )
                    edit_source = st.selectbox(
                        "Source",
                        real_sources,
                        index=real_sources.index(selected_event["Source"])
                        if selected_event["Source"] in real_sources
                        else 0,
                    )

                with c3:
                    edit_client = st.text_input(
                        "Client", value=selected_event["Client"]
                    )
                    edit_course = st.text_input(
                        "Course / Description",
                        value=selected_event["Course/Description"],
                    )

                    current_trainers = [
                        t.strip()
                        for t in str(selected_event["Trainer Calendar"]).split(",")
                        if t.strip()
                    ]
                    edit_trainer = st.multiselect(
                        "Trainer Calendar",
                        ["All"] + TRAINERS,
                        default=current_trainers if current_trainers else ["All"],
                        help="Select 'All' to show on all trainers' calendars, or select specific trainer(s)",
                    )

                    edit_medium = st.selectbox(
                        "Medium",
                        MEDIUMS,
                        index=MEDIUMS.index(selected_event["Medium"])
                        if selected_event["Medium"] in MEDIUMS
                        else 0,
                    )

                edit_location = st.selectbox(
                    "Location",
                    LOCATIONS,
                    index=LOCATIONS.index(selected_event["Location"])
                    if selected_event["Location"] in LOCATIONS
                    else 0,
                )
                edit_billing = st.text_area(
                    "Billing Notes", value=selected_event.get("Billing", "")
                )
                edit_invoiced = st.selectbox(
                    "Invoiced",
                    ["No", "Yes"],
                    index=0
                    if selected_event.get("Invoiced", "No") == "No"
                    else 1,
                )
                edit_notes = st.text_area(
                    "Additional Notes", value=selected_event.get("Notes", "")
                )

                # ---------- Date range confirmation ----------
                num_days = (edit_end_date - edit_start_date).days + 1
                long_range = num_days > 5

                if long_range:
                    st.warning(
                        f"⚠️ You selected a date range of **{num_days} days**.\n\n"
                        "This will create **one event PER DAY** in that range."
                    )
                    confirm_long = st.checkbox(
                        "I understand and want to update events for this entire date range.",
                        key="confirm_manage_single_long_range",
                    )
                else:
                    confirm_long = True

                save_btn = st.form_submit_button(
                    "💾 Save Changes", use_container_width=True
                )

            if save_btn:
                if not edit_trainer:
                    st.error("❌ Please select at least one trainer!")
                elif edit_end_date < edit_start_date:
                    st.error("❌ End Date cannot be before Start Date!")
                elif not confirm_long:
                    st.error(
                        "❌ Please tick the confirmation box above to apply this long date range."
                    )
                else:
                    # Drop original
                    df = df.drop(selected_idx).reset_index(drop=True)

                    # Determine trainers
                    if "All" in edit_trainer:
                        trainer_list = ", ".join(TRAINERS)
                    else:
                        trainer_list = ", ".join(edit_trainer)

                    events_to_add = []
                    cur = edit_start_date
                    while cur <= edit_end_date:
                        updated_row = {
                            "Date": cur,
                            "Type": edit_type,
                            "Status": edit_status,
                            "Source": edit_source,
                            "Client": edit_client,
                            "Course/Description": edit_course,
                            "Trainer Calendar": trainer_list,
                            "Medium": edit_medium,
                            "Location": edit_location,
                            "Billing": edit_billing,
                            "Invoiced": edit_invoiced,
                            "Notes": edit_notes,
                            "Date Modified": datetime.now().strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "Action Type": "Modified",
                            "Modified By": user_email,
                            "Is Marked": False,
                        }
                        updated_row["Title"] = generate_title(updated_row)
                        events_to_add.append(updated_row)
                        cur += timedelta(days=1)

                    df = pd.concat([df, pd.DataFrame(events_to_add)], ignore_index=True)
                    save_events(df)
                    append_audit(
                        user_email,
                        "Edit Event (Manage)",
                        f"{len(events_to_add)} day(s)",
                    )
                    st.success("✅ Event updated successfully!")
                    st.rerun()

        # ---- Duplicate ----
        with op_tab2:
            st.write("Duplicate this event to a single date or date range.")

            with st.form("single_duplicate_form"):
                dup_method = st.radio(
                    "Duplication method",
                    ["Single Date", "Date Range"],
                    help=(
                        "Single Date: duplicate to one specific date. "
                        "Date Range: duplicate across multiple consecutive days"
                    ),
                )

                if dup_method == "Single Date":
                    dup_date = st.date_input("Duplicate to this date")

                    dup_btn = st.form_submit_button(
                        "🔄 Duplicate Event", use_container_width=True
                    )

                    if dup_btn:
                        original = df.loc[selected_idx].copy()
                        original["Date"] = pd.Timestamp(dup_date)
                        original["Date Modified"] = datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )
                        original["Action Type"] = "Duplicated"
                        original["Modified By"] = user_email
                        original["Is Marked"] = False
                        original["Title"] = generate_title(original)

                        df = pd.concat([df, pd.DataFrame([original])], ignore_index=True)
                        save_events(df)
                        append_audit(
                            user_email,
                            "Duplicate Event",
                            f"Single date: {dup_date}",
                        )
                        st.success("✅ Duplicate created!")
                        st.rerun()

                else:
                    cold1, cold2 = st.columns(2)
                    with cold1:
                        range_start = st.date_input("Start Date", key="dup_range_start")
                    with cold2:
                        range_end = st.date_input("End Date", key="dup_range_end")

                    st.info(
                        f"This will create duplicates for each day from {range_start} to {range_end}"
                    )

                    dup_btn = st.form_submit_button(
                        "🔄 Duplicate Across Date Range", use_container_width=True
                    )

                    if dup_btn:
                        if range_end < range_start:
                            st.error("End date must be after start date!")
                        else:
                            new_events = []
                            original = df.loc[selected_idx].copy()

                            cur = range_start
                            while cur <= range_end:
                                new_event = original.copy()
                                new_event["Date"] = pd.Timestamp(cur)
                                new_event["Date Modified"] = datetime.now().strftime(
                                    "%Y-%m-%d %H:%M"
                                )
                                new_event["Action Type"] = "Duplicated"
                                new_event["Modified By"] = user_email
                                new_event["Is Marked"] = False
                                new_event["Title"] = generate_title(new_event)
                                new_events.append(new_event)
                                cur += timedelta(days=1)

                            df = pd.concat(
                                [df, pd.DataFrame(new_events)], ignore_index=True
                            )
                            save_events(df)
                            append_audit(
                                user_email,
                                "Duplicate Event (Range)",
                                f"{len(new_events)} day(s)",
                            )
                            st.success(f"✅ Created {len(new_events)} duplicate(s)!")
                            st.rerun()

        # ---- Delete ----
        with op_tab3:
            st.warning("⚠️ You are about to delete 1 event")
            st.write(f"- {df.loc[selected_events[0], 'Title']}")

            if st.button(
                "🗑️ Delete This Event",
                type="primary",
                use_container_width=True,
                key="single_delete_btn",
            ):
                df = df.drop(selected_events[0]).reset_index(drop=True)
                save_events(df)
                append_audit(user_email, "Delete Event", "1 event")
                st.success("✅ Event deleted!")
                st.rerun()

    # ============================ MULTIPLE EVENTS SELECTED ============================
    else:
        op_tab1, op_tab2, op_tab3 = st.tabs(["✏️ Bulk Edit", "📋 Duplicate", "🗑️ Delete"])

        # ---- Bulk Edit ----
        with op_tab1:
            st.write(f"**Edit {len(selected_events)} selected event(s)**")

            st.write("**Events to be updated:**")
            for idx in selected_events:
                date_str = pd.to_datetime(df.loc[idx, "Date"]).strftime("%Y-%m-%d")
                st.write(f"- {df.loc[idx, 'Title']} ({date_str})")

            st.divider()

            with st.form("bulk_edit_form"):
                update_options = st.multiselect(
                    "Select fields to update",
                    [
                        "Status",
                        "Trainer Calendar",
                        "Location",
                        "Medium",
                        "Invoiced",
                        "Type",
                        "Source",
                    ],
                    help="Only the fields you select here will be updated",
                )

                bulk_updates = {}

                colb1, colb2 = st.columns(2)
                with colb1:
                    if "Status" in update_options:
                        real_statuses = (
                            STATUSES[1:]
                            if STATUSES and STATUSES[0] == "All"
                            else STATUSES
                        )
                        bulk_updates["Status"] = st.selectbox(
                            "New Status",
                            real_statuses,
                            key="bulk_status_new",
                        )
                    if "Trainer Calendar" in update_options:
                        bulk_updates["Trainer Calendar"] = st.selectbox(
                            "New Trainer", TRAINERS, key="bulk_trainer_new"
                        )
                    if "Location" in update_options:
                        bulk_updates["Location"] = st.selectbox(
                            "New Location", LOCATIONS, key="bulk_location_new"
                        )
                    if "Type" in update_options:
                        bulk_updates["Type"] = st.selectbox(
                            "New Type", TYPES, key="bulk_type_new"
                        )

                with colb2:
                    if "Medium" in update_options:
                        bulk_updates["Medium"] = st.selectbox(
                            "New Medium", MEDIUMS, key="bulk_medium_new"
                        )
                    if "Invoiced" in update_options:
                        bulk_updates["Invoiced"] = st.selectbox(
                            "New Invoiced", ["No", "Yes"], key="bulk_invoiced_new"
                        )
                    if "Source" in update_options:
                        real_sources = (
                            SOURCES[1:]
                            if SOURCES and SOURCES[0] == "All"
                            else SOURCES
                        )
                        bulk_updates["Source"] = st.selectbox(
                            "New Source", real_sources, key="bulk_source_new"
                        )

                bulk_btn = st.form_submit_button(
                    f"💾 Update {len(selected_events)} Event(s)",
                    use_container_width=True,
                )

            if bulk_btn:
                if len(update_options) == 0:
                    st.warning("Please select at least one field to update!")
                else:
                    for idx in selected_events:
                        for field, value in bulk_updates.items():
                            df.at[idx, field] = value
                        df.at[idx, "Date Modified"] = datetime.now().strftime(
                            "%Y-%m-%d %H:%M"
                        )
                        df.at[idx, "Action Type"] = "Bulk Modified"
                        df.at[idx, "Modified By"] = user_email
                        df.at[idx, "Title"] = generate_title(df.loc[idx])

                    save_events(df)
                    append_audit(
                        user_email,
                        "Bulk Edit Events",
                        f"{len(selected_events)} events",
                    )
                    st.success(f"✅ Updated {len(selected_events)} event(s)!")
                    st.rerun()

        # ---- Bulk Duplicate ----
        with op_tab2:
            st.write(f"**Duplicate {len(selected_events)} selected event(s)**")

            with st.form("bulk_duplicate_form"):
                dup_method = st.radio(
                    "Duplication method",
                    ["Single Date", "Date Range"],
                    help=(
                        "Single Date: duplicate to one specific date. "
                        "Date Range: duplicate across multiple consecutive days"
                    ),
                )

                if dup_method == "Single Date":
                    dup_date = st.date_input("Duplicate to this date")

                    dup_btn = st.form_submit_button(
                        f"🔄 Duplicate {len(selected_events)} Event(s)",
                        use_container_width=True,
                    )

                    if dup_btn:
                        new_events = []
                        for idx in selected_events:
                            original = df.loc[idx].copy()
                            original["Date"] = pd.Timestamp(dup_date)
                            original["Date Modified"] = datetime.now().strftime(
                                "%Y-%m-%d %H:%M"
                            )
                            original["Action Type"] = "Duplicated"
                            original["Modified By"] = user_email
                            original["Is Marked"] = False
                            original["Title"] = generate_title(original)
                            new_events.append(original)

                        df = pd.concat(
                            [df, pd.DataFrame(new_events)], ignore_index=True
                        )
                        save_events(df)
                        append_audit(
                            user_email,
                            "Bulk Duplicate Events",
                            f"{len(new_events)} events",
                        )
                        st.success(f"✅ Created {len(new_events)} duplicate(s)!")
                        st.rerun()

                else:
                    cold1, cold2 = st.columns(2)
                    with cold1:
                        range_start = st.date_input(
                            "Start Date", key="bulk_dup_range_start"
                        )
                    with cold2:
                        range_end = st.date_input(
                            "End Date", key="bulk_dup_range_end"
                        )

                    st.info(
                        f"This will create duplicates for each day from {range_start} to {range_end}"
                    )

                    dup_btn = st.form_submit_button(
                        "🔄 Duplicate Across Date Range", use_container_width=True
                    )

                    if dup_btn:
                        if range_end < range_start:
                            st.error("End date must be after start date!")
                        else:
                            new_events = []
                            for idx in selected_events:
                                original = df.loc[idx].copy()
                                cur = range_start
                                while cur <= range_end:
                                    new_event = original.copy()
                                    new_event["Date"] = pd.Timestamp(cur)
                                    new_event["Date Modified"] = datetime.now().strftime(
                                        "%Y-%m-%d %H:%M"
                                    )
                                    new_event["Action Type"] = "Duplicated"
                                    new_event["Modified By"] = user_email
                                    new_event["Is Marked"] = False
                                    new_event["Title"] = generate_title(new_event)
                                    new_events.append(new_event)
                                    cur += timedelta(days=1)

                            df = pd.concat(
                                [df, pd.DataFrame(new_events)], ignore_index=True
                            )
                            save_events(df)
                            append_audit(
                                user_email,
                                "Bulk Duplicate Events (Range)",
                                f"{len(new_events)} events",
                            )
                            st.success(f"✅ Created {len(new_events)} duplicate(s)!")
                            st.rerun()

        # ---- Bulk Delete ----
        with op_tab3:
            st.warning(f"⚠️ You are about to delete {len(selected_events)} event(s)")

            for idx in selected_events:
                st.write(f"- {df.loc[idx, 'Title']}")

            if st.button(
                f"🗑️ Delete {len(selected_events)} Event(s)",
                type="primary",
                use_container_width=True,
                key="bulk_delete_btn",
            ):
                df = df.drop(selected_events).reset_index(drop=True)
                save_events(df)
                append_audit(
                    user_email,
                    "Bulk Delete Events",
                    f"{len(selected_events)} events",
                )
                st.success(f"✅ Deleted {len(selected_events)} event(s)!")
                st.rerun()

    return df
