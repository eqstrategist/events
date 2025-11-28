import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

from ui.event_forms import new_event_tab, manage_events_tab
from ui.calendar_grid import calendar_grid
from ui.mark_dates import mark_dates_tab
from ui.settings_page import settings_tab
from ui.shared import trainer_legend

from core.utils import generate_title
from core.storage import save_events, append_audit


def admin_page(df, user_email, settings):
    (
        TRAINERS,
        TRAINER_COLORS,
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
        RULE_ONLY_ADMIN_CAN_BLOCK,
        RULE_BLOCK_PREVENT_DUPLICATES,
        users_df,
        trainers_df,
        lists_df,
        rules_df,
        defaults_df,
        notif_df,
        EXCEL_FILE,
        refresh_pw_cb,
    ) = settings

    st.title("🗓️ EQS Event Scheduling – Admin")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "➕ New Event",
            "🔍 Manage Events",
            "📅 Calendar View",
            "🚫 Mark Dates",
            "⚙️ Settings",
        ]
    )

    # -------------------------------------------------------------------------
    # TAB 1 – NEW EVENT
    # -------------------------------------------------------------------------
    with tab1:
        df = new_event_tab(
            df,
            user_email,
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
        )

    # -------------------------------------------------------------------------
    # TAB 2 – MANAGE EVENTS
    # -------------------------------------------------------------------------
    with tab2:
        df = manage_events_tab(
            df,
            user_email,
            TRAINERS,
            STATUSES,
            SOURCES,
            LOCATIONS,
            MEDIUMS,
            TYPES,
            RULE_BLOCK_PREVENT_DUPLICATES,
        )

    # -------------------------------------------------------------------------
    # TAB 3 – CALENDAR VIEW (with edit-from-calendar flow)
    # -------------------------------------------------------------------------
    with tab3:
        st.header("📅 Calendar View")

        # Year / Month selectors
        cy = datetime.now().year
        col1, col2 = st.columns([1, 3])
        with col1:
            selected_year = st.selectbox(
                "Year",
                range(cy - 1, cy + 3),
                index=1,
                key="admin_calendar_year",
            )
        with col2:
            selected_month = st.selectbox(
                "Month",
                range(1, 13),
                format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                index=datetime.now().month - 1,
                key="admin_calendar_month",
            )

        # Trainer legend
        trainer_legend(TRAINERS, TRAINER_COLORS)
        st.divider()

        # Filter events for the selected month/year
        month_events = df[
            (pd.to_datetime(df["Date"]).dt.month == selected_month)
            & (pd.to_datetime(df["Date"]).dt.year == selected_year)
        ].copy()

        # Draw calendar grid – clicking "View Details" sets st.session_state["selected_day"]
        calendar_grid(
            month_events,
            selected_year,
            selected_month,
            TRAINERS,
            TRAINER_COLORS,
            role_prefix="admin",
        )

        st.divider()

        # ---- DAY DETAILS + EDITING ----
        sel_day = st.session_state.get("selected_day", None)
        if sel_day is not None:
            # sel_day might be datetime OR date
            if isinstance(sel_day, datetime):
                day_date = sel_day.date()
            else:
                day_date = sel_day

            st.subheader(f"📌 Events on {day_date.strftime('%A, %d %B %Y')}")

            day_events = df[
                pd.to_datetime(df["Date"]).dt.date == day_date
            ].sort_values("Date")

            if len(day_events) == 0:
                st.info("No events on this day.")
            else:
                for event_idx, ev in day_events.iterrows():
                    is_marked = bool(ev.get("Is Marked", False))
                    title_prefix = "🚫 BLOCKED - " if is_marked else "📅"
                    with st.expander(
                        f"{title_prefix} {ev.get('Title','')}",
                        expanded=False,
                    ):
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.write(
                                f"**Date:** {pd.to_datetime(ev.get('Date')).strftime('%Y-%m-%d')}"
                            )
                            st.write(
                                f"**Trainer(s):** {ev.get('Trainer Calendar','')}"
                            )
                            st.write(
                                f"**Status:** {ev.get('Status','')} | "
                                f"**Type:** {ev.get('Type','')}"
                            )
                        with col_b:
                            st.write(
                                f"**Client:** {ev.get('Client','')} | "
                                f"**Source:** {ev.get('Source','')}"
                            )
                            st.write(
                                f"**Medium:** {ev.get('Medium','')} | "
                                f"**Location:** {ev.get('Location','')}"
                            )
                        with col_c:
                            st.write(
                                f"**Invoiced:** {ev.get('Invoiced','No')}"
                            )
                            st.write(
                                f"**Modified By:** {ev.get('Modified By','')}"
                            )

                        st.write(
                            f"**Course/Description:** {ev.get('Course/Description','')}"
                        )
                        notes = str(ev.get("Notes", ""))
                        billing = str(ev.get("Billing", ""))
                        if notes not in ["nan", "", None]:
                            st.write(f"**Notes:** {notes}")
                        if billing not in ["nan", "", None]:
                            st.write(f"**Billing:** {billing}")

                        st.markdown("---")
                        st.write(
                            f"**Last Modified:** {ev.get('Date Modified','')} | "
                            f"**Action:** {ev.get('Action Type','')}"
                        )

                        # Only allow editing for non-block rows
                        if not is_marked:
                            if st.button(
                                "✏️ Edit This Event",
                                key=f"admin_cal_edit_btn_{event_idx}",
                                use_container_width=True,
                            ):
                                st.session_state["admin_cal_edit_idx"] = int(
                                    event_idx
                                )
                                st.rerun()

            # Close day details
            if st.button("❌ Close Day Details", key="admin_close_day_details"):
                st.session_state["selected_day"] = None
                st.session_state.pop("admin_cal_edit_idx", None)
                st.rerun()
        else:
            st.info(
                "Click **View Details** on a day in the calendar above to see and edit events for that date."
            )

        # ---- EDIT FORM (from calendar) ----
        edit_idx = st.session_state.get("admin_cal_edit_idx", None)
        if edit_idx is not None and edit_idx in df.index:
            st.divider()
            st.subheader("✏️ Edit Event (from Calendar View)")

            selected_event = df.loc[edit_idx]

            with st.form("admin_calendar_edit_form"):
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
                with c2:
                    edit_type = st.selectbox(
                        "Type",
                        TYPES,
                        index=TYPES.index(selected_event["Type"]),
                    )
                    # STATUSES[0] is "All" – for editing we use the real statuses
                    real_statuses = STATUSES[1:]
                    edit_status = st.selectbox(
                        "Status",
                        real_statuses,
                        index=real_statuses.index(selected_event["Status"]),
                    )
                    real_sources = SOURCES[1:]
                    edit_source = st.selectbox(
                        "Source",
                        real_sources,
                        index=real_sources.index(selected_event["Source"]),
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
                        for t in str(
                            selected_event.get("Trainer Calendar", "")
                        ).split(",")
                        if t.strip()
                    ]
                    edit_trainer = st.multiselect(
                        "Trainer Calendar",
                        ["All"] + TRAINERS,
                        default=current_trainers
                        if current_trainers
                        else ["All"],
                    )
                    edit_medium = st.selectbox(
                        "Medium",
                        MEDIUMS,
                        index=MEDIUMS.index(selected_event["Medium"])
                        if selected_event["Medium"] in MEDIUMS
                        else 0,
                    )

                # Location, Billing, Invoiced, Notes
                edit_location = st.selectbox(
                    "Location",
                    LOCATIONS,
                    index=LOCATIONS.index(selected_event["Location"])
                    if selected_event["Location"] in LOCATIONS
                    else 0,
                )
                edit_billing = st.text_area(
                    "Billing Notes",
                    value=selected_event.get("Billing", ""),
                )
                edit_invoiced = st.selectbox(
                    "Invoiced",
                    ["No", "Yes"],
                    index=0
                    if selected_event.get("Invoiced", "No") == "No"
                    else 1,
                )
                edit_notes = st.text_area(
                    "Additional Notes",
                    value=selected_event.get("Notes", ""),
                )

                col_sa, col_sb = st.columns(2)
                with col_sa:
                    save_btn = st.form_submit_button(
                        "💾 Save Changes", use_container_width=True
                    )
                with col_sb:
                    cancel_btn = st.form_submit_button(
                        "❌ Cancel", use_container_width=True
                    )

            if save_btn:
                if not edit_trainer:
                    st.error("❌ Please select at least one trainer!")
                elif edit_end_date < edit_start_date:
                    st.error("❌ End Date cannot be before Start Date!")
                else:
                    # Drop original event
                    df_drop = df.drop(index=edit_idx).reset_index(drop=True)

                    # Build trainer list string
                    trainer_list = (
                        ", ".join(TRAINERS)
                        if "All" in edit_trainer
                        else ", ".join(edit_trainer)
                    )

                    # Build new rows for each day in range
                    events_to_add = []
                    cur = edit_start_date
                    while cur <= edit_end_date:
                        row = {
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
                            "Action Type": "Modified (Calendar)",
                            "Modified By": user_email,
                            "Is Marked": False,
                            "Marked For": "",
                        }
                        row["Title"] = generate_title(row)
                        events_to_add.append(row)
                        cur += timedelta(days=1)

                    df = pd.concat(
                        [df_drop, pd.DataFrame(events_to_add)],
                        ignore_index=True,
                    )
                    save_events(df)
                    append_audit(
                        user_email,
                        "Edited Event (Calendar)",
                        f"{len(events_to_add)} day(s)",
                    )
                    st.success("✅ Updated event(s) from calendar view!")
                    st.session_state.pop("admin_cal_edit_idx", None)
                    st.rerun()

            if cancel_btn:
                st.session_state.pop("admin_cal_edit_idx", None)
                st.info("Edit canceled.")

    # -------------------------------------------------------------------------
    # TAB 4 – MARK DATES
    # -------------------------------------------------------------------------
    with tab4:
        df = mark_dates_tab(
            df,
            user_email,
            TRAINERS,
            RULE_ONLY_ADMIN_CAN_BLOCK,
            "admin",
        )

    # -------------------------------------------------------------------------
    # TAB 5 – SETTINGS
    # -------------------------------------------------------------------------
    with tab5:
        settings_tab(
            users_df,
            trainers_df,
            lists_df,
            rules_df,
            defaults_df,
            notif_df,
            EXCEL_FILE,
            refresh_pw_cb,
        )

    return df
