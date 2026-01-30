import streamlit as st
import pandas as pd
from core.storage import read_sheet, write_sheet, create_backup, list_backups, delete_backup, restore_backup, import_backup
from core.config import LIST_CATEGORIES
from core.security import hash_password

def settings_tab(users_df, trainers_df, lists_df, rules_df, defaults_df, notif_df, EXCEL_FILE, refresh_passwords_cb, user_email=""):
    st.header("⚙️ Settings (Admin Only)")

    tabs = st.tabs([
        "1) Users & Roles",
        "2) Trainers & Colors",
        "3) Dropdown Lists",
        "4) Blocking Rules",
        "5) File / Backup",
        "6) Defaults",
        "7) Notifications",
        "8) Audit Log"
    ])

    with tabs[0]:
        st.subheader("User & Role Management")
        edited_users = st.data_editor(
            users_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Role": st.column_config.SelectboxColumn("Role", options=["admin","view_only","trainer"]),
                "Active": st.column_config.CheckboxColumn("Active"),
            }
        )
        if st.button("💾 Save Users"):
            edited_users["Email"] = edited_users["Email"].str.lower().str.strip()
            write_sheet("Users", edited_users)
            refresh_passwords_cb()
            st.success("Users saved. App will refresh.")
            st.rerun()

        st.divider()
        reset_email = st.selectbox("User", edited_users["Email"].tolist() if len(edited_users) else [])
        new_pw = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            if reset_email and new_pw:
                if len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    hashed_pw = hash_password(new_pw)
                    edited_users.loc[edited_users["Email"]==reset_email, "Password"] = hashed_pw
                    write_sheet("Users", edited_users)
                    refresh_passwords_cb()
                    st.success("Password reset.")
            else:
                st.error("Pick user and password.")

    with tabs[1]:
        st.subheader("Trainer & Colors")
        edited_trainers = st.data_editor(
            trainers_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={"Active": st.column_config.CheckboxColumn("Active")}
        )
        if st.button("💾 Save Trainers"):
            write_sheet("Trainers", edited_trainers)
            st.success("Saved. Refreshing.")
            st.rerun()

    with tabs[2]:
        st.subheader("Lists / Dropdowns")
        edited_lists = st.data_editor(
            lists_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Category": st.column_config.SelectboxColumn("Category", options=LIST_CATEGORIES),
                "Active": st.column_config.CheckboxColumn("Active")
            }
        )
        if st.button("💾 Save Lists"):
            write_sheet("Lists", edited_lists)
            st.success("Saved. Refreshing.")
            st.rerun()

    with tabs[3]:
        st.subheader("Blocking Rules")
        rules_map = {r["Key"]: r["Value"] for _, r in rules_df.iterrows()}
        blocked_allows_visible_events = st.checkbox(
            "Blocked dates still show other trainers' events",
            value=bool(rules_map.get("blocked_allows_visible_events", True))
        )
        only_admin_can_block = st.checkbox(
            "Only admins can mark/unmark dates",
            value=bool(rules_map.get("only_admin_can_block", True))
        )
        blocked_prevents_duplicates = st.checkbox(
            "Duplication skips blocked dates",
            value=bool(rules_map.get("blocked_prevents_duplicates", True))
        )
        if st.button("💾 Save Blocking Rules"):
            new_rules = pd.DataFrame([
                ("blocked_allows_visible_events", blocked_allows_visible_events),
                ("only_admin_can_block", only_admin_can_block),
                ("blocked_prevents_duplicates", blocked_prevents_duplicates),
            ], columns=["Key","Value"])
            write_sheet("Rules", new_rules)
            st.success("Saved. Refreshing.")
            st.rerun()

    with tabs[4]:
        st.subheader("Backup / Download")

        # Show backup confirmation if just created
        if st.session_state.get("backup_created_success"):
            backup_name = st.session_state.get("backup_created_name", "")
            st.success(f"Backup created successfully: {backup_name}")
            st.balloons()
            del st.session_state["backup_created_success"]
            if "backup_created_name" in st.session_state:
                del st.session_state["backup_created_name"]

        # Create backup section
        st.markdown("### Create Manual Backup")
        st.info("Create a timestamped backup of your data. Backups are stored on the server and can be downloaded later.")

        if st.button("Create Backup Now", type="primary", use_container_width=True):
            success, result = create_backup(user_email)
            if success:
                st.session_state["backup_created_success"] = True
                st.session_state["backup_created_name"] = result
                st.rerun()
            else:
                st.error(f"Failed to create backup: {result}")

        st.divider()

        # Download current file
        st.markdown("### Download Current Data")
        with open(EXCEL_FILE, "rb") as f:
            st.download_button("Download Current Data File", f, file_name=EXCEL_FILE)

        st.divider()

        # Import backup from file
        st.markdown("### Import Backup")
        st.info("Upload a previously downloaded backup file to restore your data.")
        uploaded_file = st.file_uploader("Choose a backup file", type=["xlsx"], key="import_backup_file")
        if uploaded_file is not None:
            st.warning(f"⚠️ Importing '{uploaded_file.name}' will replace all current data. A backup of current data will be created first.")
            if st.button("Import and Restore", type="primary"):
                success, message = import_backup(uploaded_file, user_email)
                if success:
                    st.success(f"✅ {message}")
                    st.info("Please refresh the app to see the restored data.")
                    st.rerun()
                else:
                    st.error(f"Failed to import: {message}")

        st.divider()

        # List existing backups
        st.markdown("### Existing Backups")
        backups = list_backups()

        if not backups:
            st.info("No backups found. Create your first backup using the button above.")
        else:
            st.write(f"**{len(backups)} backup(s) available:**")
            for backup in backups:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.text(f"{backup['filename']}")
                    st.caption(f"Created: {backup['created']} | Size: {backup['size_kb']} KB")
                with col2:
                    with open(backup['filepath'], "rb") as f:
                        st.download_button(
                            "Download",
                            f,
                            file_name=backup['filename'],
                            key=f"dl_{backup['filename']}"
                        )
                with col3:
                    if st.button("Restore", key=f"restore_{backup['filename']}", type="primary"):
                        success, message = restore_backup(backup['filename'], user_email)
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"Failed: {message}")
                with col4:
                    if st.button("Delete", key=f"del_{backup['filename']}", type="secondary"):
                        delete_backup(backup['filename'])
                        st.rerun()

    with tabs[5]:
        st.subheader("Defaults")
        defaults_map = {d["Key"]: d["Value"] for _, d in defaults_df.iterrows()}

        STATUSES = lists_df[(lists_df["Category"]=="Statuses") & (lists_df["Active"]==True)]["Value"].tolist()
        MEDIUMS = lists_df[(lists_df["Category"]=="Mediums") & (lists_df["Active"]==True)]["Value"].tolist()
        SOURCES = lists_df[(lists_df["Category"]=="Sources") & (lists_df["Active"]==True)]["Value"].tolist()
        LOCATIONS = lists_df[(lists_df["Category"]=="Locations") & (lists_df["Active"]==True)]["Value"].tolist()
        TYPES = lists_df[(lists_df["Category"]=="Types") & (lists_df["Active"]==True)]["Value"].tolist()

        new_default_status = st.selectbox("Default Status", STATUSES, index=STATUSES.index(defaults_map.get("default_status","Offered")) if defaults_map.get("default_status","Offered") in STATUSES else 0)
        new_default_medium = st.selectbox("Default Medium", MEDIUMS, index=MEDIUMS.index(defaults_map.get("default_medium","Online")) if defaults_map.get("default_medium","Online") in MEDIUMS else 0)
        new_default_source = st.selectbox("Default Source", SOURCES, index=SOURCES.index(defaults_map.get("default_source","EQS")) if defaults_map.get("default_source","EQS") in SOURCES else 0)
        new_default_location = st.selectbox("Default Location", LOCATIONS, index=LOCATIONS.index(defaults_map.get("default_location","Global")) if defaults_map.get("default_location","Global") in LOCATIONS else 0)
        new_default_type = st.selectbox("Default Type", TYPES, index=TYPES.index(defaults_map.get("default_type","W")) if defaults_map.get("default_type","W") in TYPES else 0)

        if st.button("💾 Save Defaults"):
            new_defaults = pd.DataFrame([
                ("default_status", new_default_status),
                ("default_medium", new_default_medium),
                ("default_source", new_default_source),
                ("default_location", new_default_location),
                ("default_type", new_default_type),
            ], columns=["Key","Value"])
            write_sheet("Defaults", new_defaults)
            st.success("Defaults saved. Refreshing.")
            st.rerun()

    with tabs[6]:
        st.subheader("Notifications")
        notif_map = {n["Key"]: n["Value"] for _, n in notif_df.iterrows()}
        notify_new = st.checkbox("Notify on new event", value=bool(notif_map.get("notify_on_new_event", False)))
        notify_edit = st.checkbox("Notify on edit", value=bool(notif_map.get("notify_on_edit", False)))
        notify_block = st.checkbox("Notify on block", value=bool(notif_map.get("notify_on_block", False)))
        notif_emails = st.text_area("Notification Emails", value=str(notif_map.get("notification_emails","")))
        if st.button("💾 Save Notifications"):
            new_notif = pd.DataFrame([
                ("notify_on_new_event", notify_new),
                ("notify_on_edit", notify_edit),
                ("notify_on_block", notify_block),
                ("notification_emails", notif_emails),
            ], columns=["Key","Value"])
            write_sheet("Notifications", new_notif)
            st.success("Saved.")

    with tabs[7]:
        st.subheader("Audit Log")
        audit_df = read_sheet("Audit", pd.DataFrame(columns=["Timestamp","User","Action","Details"]))
        st.dataframe(audit_df.sort_values("Timestamp", ascending=False), use_container_width=True)
