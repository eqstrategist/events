import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from core.utils import generate_title, trainer_matches
from core.rules import is_date_blocked_for_trainer
from core.storage import save_events, append_audit

def clear_event_selections():
    """Clear all event checkbox selections from session state."""
    keys_to_delete = [key for key in st.session_state.keys() if key.startswith("check_")]
    for key in keys_to_delete:
        del st.session_state[key]

@st.dialog("Event Saved")
def show_event_saved_dialog(event_count):
    st.success(f"✅ Event saved successfully!")
    st.write(f"**{event_count} event(s)** added to the calendar.")
    if st.button("OK", type="primary", use_container_width=True):
        del st.session_state["event_saved_success"]
        if "event_saved_count" in st.session_state:
            del st.session_state["event_saved_count"]
        st.rerun()

def new_event_tab(df, user_email, TRAINERS, TYPES, STATUSES, SOURCES, MEDIUMS, LOCATIONS,
                  DEFAULT_TYPE, DEFAULT_STATUS, DEFAULT_SOURCE, DEFAULT_MEDIUM, DEFAULT_LOCATION):
    st.header("Add New Event")

    # Show confirmation popup if event was just saved
    if st.session_state.get("event_saved_success"):
        event_count = st.session_state.get("event_saved_count", 1)
        show_event_saved_dialog(event_count)

    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date", value=start_date)
        with c2:
            type_ = st.selectbox("Type", TYPES, index=TYPES.index(DEFAULT_TYPE) if DEFAULT_TYPE in TYPES else 0)
            status = st.selectbox("Status", STATUSES[1:], index=STATUSES[1:].index(DEFAULT_STATUS) if DEFAULT_STATUS in STATUSES[1:] else 0)
            source = st.selectbox("Source", SOURCES[1:], index=SOURCES[1:].index(DEFAULT_SOURCE) if DEFAULT_SOURCE in SOURCES[1:] else 0)
        with c3:
            client = st.text_input("Client")
            course = st.text_input("Course / Description")
            trainer = st.multiselect("Trainer Calendar", ["All"] + TRAINERS, default=[])
            medium = st.selectbox("Medium", MEDIUMS, index=MEDIUMS.index(DEFAULT_MEDIUM) if DEFAULT_MEDIUM in MEDIUMS else 0)

        location = st.selectbox("Location", LOCATIONS, index=LOCATIONS.index(DEFAULT_LOCATION) if DEFAULT_LOCATION in LOCATIONS else 0)
        billing = st.text_area("Billing Notes")
        invoiced = st.selectbox("Invoiced", ["No", "Yes"])
        notes = st.text_area("Additional Notes")

        submitted = st.form_submit_button("Save Event", use_container_width=True)

        if submitted:
            if not trainer:
                st.error("❌ Please select at least one trainer!")
                return df
            if end_date < start_date:
                st.error("❌ End Date cannot be before Start Date!")
                return df

            trainers_for_event = TRAINERS if "All" in trainer else trainer
            blocked_dates = []
            cur = start_date
            while cur <= end_date:
                for t in trainers_for_event:
                    if is_date_blocked_for_trainer(df, cur, t):
                        blocked_dates.append(f"{cur} ({t})")
                cur += timedelta(days=1)

            if blocked_dates:
                st.error("❌ Cannot create event! Blocked for: " + ", ".join(sorted(set(blocked_dates))))
                return df

            trainer_list = ", ".join(TRAINERS) if "All" in trainer else ", ".join(trainer)
            events_to_add = []
            cur = start_date
            while cur <= end_date:
                row = {
                    "Date": cur,
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
                    "Marked For": ""
                }
                row["Title"] = generate_title(row)
                events_to_add.append(row)
                cur += timedelta(days=1)

            df = pd.concat([df, pd.DataFrame(events_to_add)], ignore_index=True)
            save_events(df)
            append_audit(user_email, "Created Event", f"{len(events_to_add)} event(s) added")
            # Set session state for confirmation popup after rerun
            st.session_state["event_saved_success"] = True
            st.session_state["event_saved_count"] = len(events_to_add)
            st.rerun()
    return df

def manage_events_tab(df, user_email, TRAINERS, STATUSES, SOURCES, LOCATIONS, MEDIUMS, TYPES, RULE_BLOCK_PREVENT_DUPLICATES):
    st.header("Manage Events")

    st.subheader("🔍 Filter Events")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        use_date_range = st.checkbox("Filter by Date Range", value=False)
        if use_date_range:
            date_from = st.date_input("From Date", key="date_from")
            date_to = st.date_input("To Date", key="date_to")

    trainer_filter = col2.selectbox("Trainer", ["All"] + TRAINERS, key="search_trainer")
    status_filter = col3.selectbox("Status", STATUSES, key="search_status")
    source_filter = col4.selectbox("Source", SOURCES, key="search_source")
    client_search = col5.text_input("Client", key="search_client")

    result = df.copy()
    if use_date_range:
        if date_to < date_from:
            st.warning("⚠️ 'To Date' cannot be before 'From Date'")
        else:
            result = result[
                (pd.to_datetime(result["Date"]).dt.date >= date_from) &
                (pd.to_datetime(result["Date"]).dt.date <= date_to)
            ]

    if trainer_filter != "All":
        result = result[trainer_matches(result["Trainer Calendar"], trainer_filter)]
    if status_filter != "All":
        result = result[result["Status"] == status_filter]
    if source_filter != "All":
        result = result[result["Source"] == source_filter]
    if client_search:
        result = result[result["Client"].str.contains(client_search, case=False, na=False)]

    st.write(f"**Showing {len(result)} events**")
    if len(result) == 0:
        st.info("No events found.")
        return df

    selected_events = []
    for idx in result.index:
        cA, cB = st.columns([0.1, 0.9])
        with cA:
            if st.checkbox("", key=f"check_{idx}"):
                selected_events.append(idx)
        with cB:
            st.write(f"**{result.loc[idx,'Title']}** - {result.loc[idx,'Date'].strftime('%Y-%m-%d')}")

    st.divider()
    display_result = result.copy()
    display_result.index = range(1, len(display_result) + 1)
    st.dataframe(display_result, use_container_width=True)

    towrite = BytesIO()
    result.to_excel(towrite, index=False, engine="openpyxl")
    towrite.seek(0)
    st.download_button("⬇️ Download Filtered Data", data=towrite,
                       file_name="Filtered_Events.xlsx",
                       mime="application/vnd.ms-excel")

    st.divider()
    if not selected_events:
        st.info("👆 Select events using the checkboxes above to perform operations")
        return df

    st.write(f"### 🎯 {len(selected_events)} Event(s) Selected")

    # SINGLE OR BULK
    if len(selected_events) == 1:
        op_tab1, op_tab2, op_tab3 = st.tabs(["✏️ Edit Event", "📋 Duplicate", "🗑️ Delete"])
        selected_idx = selected_events[0]
        selected_event = df.loc[selected_idx]

        with op_tab1:
            with st.form("single_edit_form"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    edit_start_date = st.date_input("Start Date", value=pd.to_datetime(selected_event["Date"]).date())
                    edit_end_date = st.date_input("End Date", value=pd.to_datetime(selected_event["Date"]).date())
                with c2:
                    edit_type = st.selectbox("Type", TYPES, index=TYPES.index(selected_event["Type"]) if selected_event["Type"] in TYPES else 0)
                    edit_status = st.selectbox("Status", STATUSES[1:], index=STATUSES[1:].index(selected_event["Status"]) if selected_event["Status"] in STATUSES[1:] else 0)
                    edit_source = st.selectbox("Source", SOURCES[1:], index=SOURCES[1:].index(selected_event["Source"]) if selected_event["Source"] in SOURCES[1:] else 0)
                with c3:
                    edit_client = st.text_input("Client", value=selected_event["Client"])
                    edit_course = st.text_input("Course / Description", value=selected_event["Course/Description"])
                    current_trainers = [t.strip() for t in str(selected_event["Trainer Calendar"]).split(",")]
                    edit_trainer = st.multiselect("Trainer Calendar", ["All"] + TRAINERS,
                                                  default=[t for t in current_trainers if t in (["All"] + TRAINERS)])
                    edit_medium = st.selectbox("Medium", MEDIUMS, index=MEDIUMS.index(selected_event["Medium"]) if selected_event["Medium"] in MEDIUMS else 0)
                edit_location = st.selectbox("Location", LOCATIONS, index=LOCATIONS.index(selected_event["Location"]) if selected_event["Location"] in LOCATIONS else 0)
                edit_billing = st.text_area("Billing Notes", value=selected_event["Billing"])
                edit_invoiced = st.selectbox("Invoiced", ["No","Yes"], index=0 if selected_event["Invoiced"]=="No" else 1)
                edit_notes = st.text_area("Notes", value=selected_event["Notes"])

                if st.form_submit_button("💾 Save Changes", use_container_width=True):
                    if not edit_trainer:
                        st.error("Select a trainer.")
                        return df
                    if edit_end_date < edit_start_date:
                        st.error("End date cannot be before start.")
                        return df

                    df_drop = df.drop(selected_idx).reset_index(drop=True)
                    trainer_list = ", ".join(TRAINERS) if "All" in edit_trainer else ", ".join(edit_trainer)

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
                            "Date Modified": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Action Type": "Modified",
                            "Modified By": user_email,
                            "Is Marked": False,
                            "Marked For": ""
                        }
                        row["Title"] = generate_title(row)
                        events_to_add.append(row)
                        cur += timedelta(days=1)

                    df = pd.concat([df_drop, pd.DataFrame(events_to_add)], ignore_index=True)
                    save_events(df)
                    append_audit(user_email, "Edited Event", f"{len(events_to_add)} day(s)")
                    st.success("✅ Updated!")
                    clear_event_selections()
                    st.rerun()

        with op_tab2:
            with st.form("duplicate_single_form"):
                dup_method = st.radio("Duplication method", ["Single Date","Date Range"])
                if dup_method == "Single Date":
                    dup_date = st.date_input("Duplicate to date")
                    if st.form_submit_button("🔄 Duplicate"):
                        original = df.loc[selected_idx].copy()
                        original["Date"] = pd.Timestamp(dup_date)
                        original["Date Modified"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        original["Action Type"] = "Duplicated"
                        original["Modified By"] = user_email
                        original["Is Marked"] = False
                        original["Marked For"] = ""
                        original["Title"] = generate_title(original)
                        df = pd.concat([df, pd.DataFrame([original])], ignore_index=True)
                        save_events(df)
                        st.success("✅ Duplicated!")
                        clear_event_selections()
                        st.rerun()
                else:
                    cX, cY = st.columns(2)
                    with cX:
                        rs = st.date_input("Range Start")
                    with cY:
                        re_ = st.date_input("Range End")
                    if st.form_submit_button("🔄 Duplicate Range"):
                        if re_ < rs:
                            st.error("End after start")
                            return df
                        original = df.loc[selected_idx].copy()
                        trainers_for_event = [t.strip() for t in str(original["Trainer Calendar"]).split(",")]
                        new_events=[]
                        cur=rs
                        while cur<=re_:
                            if RULE_BLOCK_PREVENT_DUPLICATES:
                                any_block = any(is_date_blocked_for_trainer(df, cur, t) for t in trainers_for_event)
                                if any_block:
                                    cur += timedelta(days=1); continue
                            e=original.copy()
                            e["Date"]=pd.Timestamp(cur)
                            e["Date Modified"]=datetime.now().strftime("%Y-%m-%d %H:%M")
                            e["Action Type"]="Duplicated"
                            e["Modified By"]=user_email
                            e["Is Marked"]=False
                            e["Marked For"]=""
                            e["Title"]=generate_title(e)
                            new_events.append(e)
                            cur += timedelta(days=1)
                        df = pd.concat([df, pd.DataFrame(new_events)], ignore_index=True)
                        save_events(df)
                        st.success(f"✅ {len(new_events)} duplicates created!")
                        clear_event_selections()
                        st.rerun()

        with op_tab3:
            st.warning("⚠️ Delete selected event")
            if st.button("🗑️ Delete", type="primary", use_container_width=True):
                df = df.drop([selected_idx]).reset_index(drop=True)
                save_events(df)
                st.success("✅ Deleted!")
                clear_event_selections()
                st.rerun()

    else:
        op_tab1, op_tab2, op_tab3 = st.tabs(["✏️ Bulk Edit","📋 Duplicate","🗑️ Delete"])

        with op_tab1:
            with st.form("bulk_edit_form"):
                fields = st.multiselect("Fields to update",
                                        ["Status","Trainer Calendar","Location","Medium","Invoiced","Type","Source","Client","Course/Description"])
                updates = {}
                cX, cY = st.columns(2)
                with cX:
                    if "Status" in fields:
                        updates["Status"] = st.selectbox("New Status", STATUSES[1:])
                    if "Trainer Calendar" in fields:
                        updates["Trainer Calendar"] = st.selectbox("New Trainer", ["All"] + TRAINERS)
                    if "Location" in fields:
                        updates["Location"] = st.selectbox("New Location", LOCATIONS)
                    if "Type" in fields:
                        updates["Type"] = st.selectbox("New Type", TYPES)
                    if "Client" in fields:
                        updates["Client"] = st.text_input("New Client")
                with cY:
                    if "Medium" in fields:
                        updates["Medium"] = st.selectbox("New Medium", MEDIUMS)
                    if "Invoiced" in fields:
                        updates["Invoiced"] = st.selectbox("New Invoiced", ["No","Yes"])
                    if "Source" in fields:
                        updates["Source"] = st.selectbox("New Source", SOURCES[1:])
                    if "Course/Description" in fields:
                        updates["Course/Description"] = st.text_input("New Course/Description")

                if st.form_submit_button("💾 Bulk Update", use_container_width=True):
                    if not fields:
                        st.warning("Pick at least one field.")
                        return df
                    for idx in selected_events:
                        for f,v in updates.items():
                            if f=="Trainer Calendar" and v=="All":
                                df.at[idx,f] = ", ".join(TRAINERS)
                            else:
                                df.at[idx,f] = v
                        df.at[idx,"Date Modified"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        df.at[idx,"Action Type"] = "Bulk Modified"
                        df.at[idx,"Modified By"] = user_email
                        df.at[idx,"Title"] = generate_title(df.loc[idx])

                    save_events(df)
                    st.success("✅ Bulk updated!")
                    clear_event_selections()
                    st.rerun()

        with op_tab2:
            with st.form("dup_bulk_form"):
                dup_method = st.radio("Duplication method", ["Single Date","Date Range"], key="dup_bulk_method")
                if dup_method=="Single Date":
                    dup_date=st.date_input("Duplicate to date", key="dup_bulk_date")
                    if st.form_submit_button("🔄 Duplicate"):
                        new_events=[]
                        for idx in selected_events:
                            original=df.loc[idx].copy()
                            original["Date"]=pd.Timestamp(dup_date)
                            original["Date Modified"]=datetime.now().strftime("%Y-%m-%d %H:%M")
                            original["Action Type"]="Duplicated"
                            original["Modified By"]=user_email
                            original["Is Marked"]=False
                            original["Marked For"]=""
                            original["Title"]=generate_title(original)
                            new_events.append(original)
                        df=pd.concat([df,pd.DataFrame(new_events)],ignore_index=True)
                        save_events(df)
                        st.success(f"✅ {len(new_events)} duplicated!")
                        clear_event_selections()
                        st.rerun()
                else:
                    cX,cY=st.columns(2)
                    with cX:
                        rs=st.date_input("Range Start", key="dup_bulk_rs")
                    with cY:
                        re_=st.date_input("Range End", key="dup_bulk_re")
                    if st.form_submit_button("🔄 Duplicate Range"):
                        if re_ < rs:
                            st.error("End after start"); return df
                        new_events=[]
                        for idx in selected_events:
                            original=df.loc[idx].copy()
                            trainers_for_event = [t.strip() for t in str(original["Trainer Calendar"]).split(",")]
                            cur=rs
                            while cur<=re_:
                                if RULE_BLOCK_PREVENT_DUPLICATES:
                                    any_block = any(is_date_blocked_for_trainer(df, cur, t) for t in trainers_for_event)
                                    if any_block:
                                        cur += timedelta(days=1); continue
                                e=original.copy()
                                e["Date"]=pd.Timestamp(cur)
                                e["Date Modified"]=datetime.now().strftime("%Y-%m-%d %H:%M")
                                e["Action Type"]="Duplicated"
                                e["Modified By"]=user_email
                                e["Is Marked"]=False
                                e["Marked For"]=""
                                e["Title"]=generate_title(e)
                                new_events.append(e)
                                cur += timedelta(days=1)
                        df=pd.concat([df,pd.DataFrame(new_events)],ignore_index=True)
                        save_events(df)
                        st.success(f"✅ {len(new_events)} duplicates created!")
                        clear_event_selections()
                        st.rerun()

        with op_tab3:
            st.warning(f"⚠️ Delete {len(selected_events)} selected events")
            if st.button("🗑️ Bulk Delete", type="primary", use_container_width=True):
                df = df.drop(selected_events).reset_index(drop=True)
                save_events(df)
                st.success("✅ Deleted!")
                clear_event_selections()
                st.rerun()

    return df
