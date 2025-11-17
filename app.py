import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import time
import os
import calendar

# For local development, use OneDrive path
# For online hosting, use local file

EXCEL_FILE = 'scheduling_recent.xlsx'  # For online hosting

st.set_page_config(page_title="EQS Event Scheduling", layout="wide")

# ---------- Authentication ----------
AUTHORIZED_EMAILS = [
    "sues@eqstrategist.com",
    "joec@eqstrategist.com",
    "doms@eqstrategist.com",
    "bernardl@eqstrategist.com"
]

# Default password
DEFAULT_PASSWORD = "Welcome123"

# Initialize password storage in session state
if "user_passwords" not in st.session_state:
    st.session_state.user_passwords = {email: DEFAULT_PASSWORD for email in AUTHORIZED_EMAILS}

def check_authentication():
    """Check if user is authenticated"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

def login_page():
    """Display login page"""
    # Custom CSS for white background and styled login form
    st.markdown("""
        <style>
        .stApp {
            background-color: white;
        }
        .stButton>button {
            background-color: #FF6B35;
            color: white;
            border: none;
            padding: 10px 24px;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #E85A2A;
            color: white;
        }
        h1, h2, h3, p, label, div {
            color: black !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Center container
    col1, col2, col3 = st.columns([1.5, 2, 1.5])
    
    with col2:
        # Display logo
        st.markdown("<div style='text-align: center; margin-top: 30px;'>", unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", width=150)
        else:
            st.title("🗓️ EQS Event Scheduling")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Login form
        st.markdown("<h3 style='text-align: center; color: black;'>🔐 Login to Access</h3>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Check if we're in reset password mode
        if "reset_mode" not in st.session_state:
            st.session_state.reset_mode = False
        
        if not st.session_state.reset_mode:
            # Normal login form
            with st.form("login_form"):
                email = st.text_input("Email Address", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submit = st.form_submit_button("Login", use_container_width=True)
                with col_b:
                    reset = st.form_submit_button("Reset Password", use_container_width=True)
                
                if submit:
                    email_lower = email.lower().strip()
                    if email_lower in AUTHORIZED_EMAILS:
                        if st.session_state.user_passwords.get(email_lower) == password:
                            st.session_state.authenticated = True
                            st.session_state.user_email = email_lower
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Incorrect password.")
                    else:
                        st.error("❌ Access denied. You are not authorized to access this application.")
                
                if reset:
                    st.session_state.reset_mode = True
                    st.rerun()
        
        else:
            # Reset password form
            st.markdown("<p style='text-align: center; font-weight: bold; color: black;'>Reset Your Password</p>", unsafe_allow_html=True)
            with st.form("reset_form"):
                email = st.text_input("Email Address", placeholder="Enter your email")
                old_password = st.text_input("Current Password", type="password", placeholder="Enter current password")
                new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
                confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submit_reset = st.form_submit_button("Update Password", use_container_width=True)
                with col_b:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)
                
                if submit_reset:
                    email_lower = email.lower().strip()
                    if email_lower in AUTHORIZED_EMAILS:
                        if st.session_state.user_passwords.get(email_lower) == old_password:
                            if new_password == confirm_password:
                                if len(new_password) >= 6:
                                    st.session_state.user_passwords[email_lower] = new_password
                                    st.success("✅ Password updated successfully!")
                                    st.session_state.reset_mode = False
                                    time.sleep(2)
                                    st.rerun()
                                else:
                                    st.error("❌ Password must be at least 6 characters long.")
                            else:
                                st.error("❌ New passwords do not match.")
                        else:
                            st.error("❌ Incorrect current password.")
                    else:
                        st.error("❌ Email not found.")
                
                if cancel:
                    st.session_state.reset_mode = False
                    st.rerun()

# Check authentication
if not check_authentication():
    login_page()
    st.stop()

# Add logout button in sidebar
with st.sidebar:
    st.write(f"👤 Logged in as: **{st.session_state.user_email}**")
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.rerun()

# ---------- Main Application (Only shown if authenticated) ----------

# Main heading
st.title("🗓️ EQS Event Scheduling")
st.markdown("---")

# ---------- Utility ----------
def load_data():
    """Load data WITHOUT caching so it always reflects the latest saved state"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Check if file exists, if not create it
            if not os.path.exists(EXCEL_FILE):
                df = pd.DataFrame(columns=[
                    "Title", "Date", "Type", "Status", "Source",
                    "Client", "Course/Description", "Trainer Calendar", "Medium", "Location",
                    "Billing", "Invoiced", "Notes", "Date Modified", "Action Type", "Modified By"
                ])
                df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
                return df
            
            df = pd.read_excel(EXCEL_FILE, engine='openpyxl')
            
            # Remove Start Time, End Time, All Day columns if they exist
            columns_to_drop = ['Start Time', 'End Time', 'All Day']
            df = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
            
            # Add Modified By column if it doesn't exist
            if 'Modified By' not in df.columns:
                df['Modified By'] = ''
            
            # Ensure Date column is datetime
            if len(df) > 0 and 'Date' in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
            
            # Reorder columns to put Title first
            cols = df.columns.tolist()
            if "Title" in cols:
                cols.remove("Title")
                cols = ["Title"] + cols
                df = df[cols]
            return df
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 second before retrying
                continue
            else:
                st.error("⚠️ Cannot access the file. Please close the Excel file if it's open and refresh the page.")
                st.stop()
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                st.error(f"⚠️ Error loading data: {str(e)}")
                # Return empty dataframe as fallback
                df = pd.DataFrame(columns=[
                    "Title", "Date", "Type", "Status", "Source",
                    "Client", "Course/Description", "Trainer Calendar", "Medium", "Location",
                    "Billing", "Invoiced", "Notes", "Date Modified", "Action Type", "Modified By"
                ])
                return df
    return pd.DataFrame()

def save_data(df):
    """Save data with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Ensure Title is first column before saving
            cols = df.columns.tolist()
            if "Title" in cols:
                cols.remove("Title")
                cols = ["Title"] + cols
                df = df[cols]
            
            # Try to save
            df.to_excel(EXCEL_FILE, index=False, engine='openpyxl')
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait 1 second before retrying
                continue
            else:
                st.error("⚠️ Cannot save to file. Please close the Excel file if it's open and try again.")
                return False
    return False

def generate_title(row):
    base = f"{row['Status']}-{row['Source']}-{row['Client']} {row['Course/Description']}"
    if row["Type"] == "W":
        base += f" ({row['Medium']}) {row['Trainer Calendar']} {row['Location']}"
    elif row["Type"] == "M":
        base += f" {row['Trainer Calendar']} {row['Location']}"
    else:
        base += f" {row['Trainer Calendar']}"
    return base.strip()

# ---------- Constants ----------
TRAINERS = ["Dom", "Andrew", "Dale", "Jack"]
LOCATIONS = ["Syd", "Mel", "Bne", "SG", "Msia"]
MONTHS = [
    "All months", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
STATUSES = ["All", "Offered", "Tentative", "Confirmed"]
SOURCES = ["All", "EQS", "CCE", "CTD"]

# Trainer colors
TRAINER_COLORS = {
    "Dom": "#FF6B6B",      # Red
    "Andrew": "#4ECDC4",   # Teal
    "Dale": "#95E1D3",     # Mint
    "Jack": "#FFD93D"      # Yellow
}

# ---------- Load Data ----------
df = load_data()

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["➕ New Event", "🔍 Manage Events", "📅 Calendar View"])

# ---------- NEW EVENT TAB ----------
with tab1:
    st.header("Add New Event")
    with st.form("add_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date", value=start_date)
            st.info("💡 For single-day events, set End Date same as Start Date")
        
        with c2:
            type_ = st.selectbox("Type", ["W", "C", "M"])
            status = st.selectbox("Status", ["Offered", "Tentative", "Confirmed"])
            source = st.selectbox("Source", ["EQS", "CCE", "CTD"])
        with c3:
            client = st.text_input("Client")
            course = st.text_input("Course / Description")
            trainer = st.selectbox("Trainer Calendar", TRAINERS)
            medium = st.selectbox("Medium", ["F2F", "Online"])

        location = st.selectbox("Location", LOCATIONS)
        billing = st.text_area("Billing Notes")
        invoiced = st.selectbox("Invoiced", ["No", "Yes"])
        notes = st.text_area("Additional Notes")

        submitted = st.form_submit_button("Save Event", use_container_width=True)
        if submitted:
            if end_date < start_date:
                st.error("❌ End Date cannot be before Start Date!")
            else:
                # Create an event for each day in the range
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
                        "Trainer Calendar": trainer,
                        "Medium": medium,
                        "Location": location,
                        "Billing": billing,
                        "Invoiced": invoiced,
                        "Notes": notes,
                        "Date Modified": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Action Type": "Created",
                        "Modified By": st.session_state.user_email
                    }
                    new_row["Title"] = generate_title(new_row)
                    events_to_add.append(new_row)
                    current_date += timedelta(days=1)
                
                # Add all events
                df = pd.concat([df, pd.DataFrame(events_to_add)], ignore_index=True)
                save_data(df)
                
                num_days = len(events_to_add)
                if num_days == 1:
                    st.success("✅ Event added successfully! Form cleared for new entry.")
                else:
                    st.success(f"✅ {num_days} events added successfully (one for each day)! Form cleared for new entry.")
                st.rerun()

# ---------- MANAGE EVENTS TAB ----------
with tab2:
    st.header("Manage Events")

    # Filters
    st.subheader("🔍 Filter Events")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Date range filter
    with col1:
        use_date_range = st.checkbox("Filter by Date Range", value=False)
        if use_date_range:
            date_from = st.date_input("From Date", key="date_from")
            date_to = st.date_input("To Date", key="date_to")
    
    trainer_filter = col2.selectbox("Trainer", ["All"] + TRAINERS, key="search_trainer")
    status_filter = col3.selectbox("Status", STATUSES, key="search_status")
    source_filter = col4.selectbox("Source", SOURCES, key="search_source")
    client_search = col5.text_input("Client", key="search_client", placeholder="Search client...")

    result = df.copy()

    # Apply date range filter if enabled
    if use_date_range:
        if date_to < date_from:
            st.warning("⚠️ 'To Date' cannot be before 'From Date'")
        else:
            result = result[
                (pd.to_datetime(result["Date"]).dt.date >= date_from) & 
                (pd.to_datetime(result["Date"]).dt.date <= date_to)
            ]
    
    if trainer_filter != "All":
        result = result[result["Trainer Calendar"] == trainer_filter]
    if status_filter != "All":
        result = result[result["Status"] == status_filter]
    if source_filter != "All":
        result = result[result["Source"] == source_filter]
    if client_search:
        result = result[result["Client"].str.contains(client_search, case=False, na=False)]

    st.write(f"**Showing {len(result)} events**")
    
    # Display filtered results with checkboxes
    if len(result) == 0:
        st.info("No events found with current filters.")
    else:
        # Add selection column
        st.write("### Select One Event for Single Edit or More for Bulk Operation")
        
        # Create checkboxes for each event
        selected_events = []
        for idx in result.index:
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                if st.checkbox("", key=f"check_{idx}"):
                    selected_events.append(idx)
            with col2:
                st.write(f"**{result.loc[idx, 'Title']}** - {result.loc[idx, 'Date'].strftime('%Y-%m-%d')}")
        
        st.divider()
        
        # Display full table
        st.dataframe(result, use_container_width=True)
        
        # Export button
        towrite = BytesIO()
        result.to_excel(towrite, index=False, engine="openpyxl")
        towrite.seek(0)
        st.download_button("⬇️ Download Filtered Data", data=towrite,
                           file_name="Filtered_Events.xlsx", mime="application/vnd.ms-excel")
        
        st.divider()
        
        # Operations on selected events
        if len(selected_events) > 0:
            st.write(f"### 🎯 {len(selected_events)} Event(s) Selected")
            
            # Show different tabs based on number of selected events
            if len(selected_events) == 1:
                # Single event editing
                op_tab1, op_tab2, op_tab3 = st.tabs(["✏️ Edit Event", "📋 Duplicate", "🗑️ Delete"])
                
                # SINGLE EDIT
                with op_tab1:
                    selected_idx = selected_events[0]
                    selected_event = df.loc[selected_idx]
                    
                    st.write(f"**Editing:** {selected_event['Title']}")
                    st.divider()
                    
                    with st.form("single_edit_form"):
                        st.subheader("Edit Event Details")
                        
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            edit_start_date = st.date_input("Start Date", value=pd.to_datetime(selected_event["Date"]).date())
                            edit_end_date = st.date_input("End Date", value=pd.to_datetime(selected_event["Date"]).date())
                            st.info("💡 Changing dates will create separate events for each day")
                        
                        with c2:
                            edit_type = st.selectbox("Type", ["W", "C", "M"], 
                                                    index=["W", "C", "M"].index(selected_event["Type"]))
                            edit_status = st.selectbox("Status", ["Offered", "Tentative", "Confirmed"],
                                                      index=["Offered", "Tentative", "Confirmed"].index(selected_event["Status"]))
                            edit_source = st.selectbox("Source", ["EQS", "CCE", "CTD"],
                                                      index=["EQS", "CCE", "CTD"].index(selected_event["Source"]))
                        with c3:
                            edit_client = st.text_input("Client", value=selected_event["Client"])
                            edit_course = st.text_input("Course / Description", value=selected_event["Course/Description"])
                            edit_trainer = st.selectbox("Trainer Calendar", TRAINERS,
                                                       index=TRAINERS.index(selected_event["Trainer Calendar"]))
                            edit_medium = st.selectbox("Medium", ["F2F", "Online"],
                                                      index=0 if selected_event["Medium"] == "F2F" else 1)

                        edit_location = st.selectbox("Location", LOCATIONS,
                                                    index=LOCATIONS.index(selected_event["Location"]))
                        edit_billing = st.text_area("Billing Notes", value=selected_event["Billing"])
                        edit_invoiced = st.selectbox("Invoiced", ["No", "Yes"],
                                                    index=0 if selected_event["Invoiced"] == "No" else 1)
                        edit_notes = st.text_area("Additional Notes", value=selected_event["Notes"])
                        
                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            if edit_end_date < edit_start_date:
                                st.error("❌ End Date cannot be before Start Date!")
                            else:
                                # Delete the original event
                                df = df.drop(selected_idx).reset_index(drop=True)
                                
                                # Create events for the new date range
                                events_to_add = []
                                current_date = edit_start_date
                                
                                while current_date <= edit_end_date:
                                    updated_row = {
                                        "Date": current_date,
                                        "Type": edit_type,
                                        "Status": edit_status,
                                        "Source": edit_source,
                                        "Client": edit_client,
                                        "Course/Description": edit_course,
                                        "Trainer Calendar": edit_trainer,
                                        "Medium": edit_medium,
                                        "Location": edit_location,
                                        "Billing": edit_billing,
                                        "Invoiced": edit_invoiced,
                                        "Notes": edit_notes,
                                        "Date Modified": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "Action Type": "Modified",
                                        "Modified By": st.session_state.user_email
                                    }
                                    updated_row["Title"] = generate_title(updated_row)
                                    events_to_add.append(updated_row)
                                    current_date += timedelta(days=1)
                                
                                # Add updated events
                                df = pd.concat([df, pd.DataFrame(events_to_add)], ignore_index=True)
                                save_data(df)
                                st.success("✅ Event updated successfully!")
                                st.rerun()
            
            else:
                # Multiple events - show bulk operations
                op_tab1, op_tab2, op_tab3 = st.tabs(["✏️ Bulk Edit", "📋 Duplicate", "🗑️ Delete"])
            
                # BULK EDIT
                with op_tab1:
                    st.write(f"**Edit {len(selected_events)} selected event(s)**")
                    
                    # Show which events will be edited
                    st.write("**Events to be updated:**")
                    for idx in selected_events:
                        st.write(f"- {df.loc[idx, 'Title']} ({df.loc[idx, 'Date'].strftime('%Y-%m-%d')})")
                    
                    st.divider()
                    
                    with st.form("bulk_edit_form"):
                        update_options = st.multiselect(
                            "Select fields to update",
                            ["Status", "Trainer Calendar", "Location", "Medium", "Invoiced", "Type", "Source"],
                            help="Only the fields you select here will be updated"
                        )
                        
                        bulk_updates = {}
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if "Status" in update_options:
                                bulk_updates["Status"] = st.selectbox("New Status", ["Offered", "Tentative", "Confirmed"], key="bulk_status_new")
                            if "Trainer Calendar" in update_options:
                                bulk_updates["Trainer Calendar"] = st.selectbox("New Trainer", TRAINERS, key="bulk_trainer_new")
                            if "Location" in update_options:
                                bulk_updates["Location"] = st.selectbox("New Location", LOCATIONS, key="bulk_location_new")
                            if "Type" in update_options:
                                bulk_updates["Type"] = st.selectbox("New Type", ["W", "C", "M"], key="bulk_type_new")
                        
                        with col2:
                            if "Medium" in update_options:
                                bulk_updates["Medium"] = st.selectbox("New Medium", ["F2F", "Online"], key="bulk_medium_new")
                            if "Invoiced" in update_options:
                                bulk_updates["Invoiced"] = st.selectbox("New Invoiced", ["No", "Yes"], key="bulk_invoiced_new")
                            if "Source" in update_options:
                                bulk_updates["Source"] = st.selectbox("New Source", ["EQS", "CCE", "CTD"], key="bulk_source_new")
                        
                        if st.form_submit_button(f"💾 Update {len(selected_events)} Event(s)", use_container_width=True):
                            if len(update_options) == 0:
                                st.warning("Please select at least one field to update!")
                            else:
                                # Only update the SELECTED events, not all filtered events
                                for idx in selected_events:
                                    for field, value in bulk_updates.items():
                                        df.at[idx, field] = value
                                    df.at[idx, "Date Modified"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                    df.at[idx, "Action Type"] = "Bulk Modified"
                                    df.at[idx, "Modified By"] = st.session_state.user_email
                                    df.at[idx, "Title"] = generate_title(df.loc[idx])
                                
                                save_data(df)
                                st.success(f"✅ Updated {len(selected_events)} event(s)!")
                                st.rerun()
            
            # DUPLICATE
            with op_tab2:
                st.write(f"**Duplicate {len(selected_events)} selected event(s)**")
                
                with st.form("duplicate_form"):
                    dup_method = st.radio(
                        "Duplication method",
                        ["Single Date", "Date Range"],
                        help="Single Date: duplicate to one specific date. Date Range: duplicate across multiple consecutive days"
                    )
                    
                    if dup_method == "Single Date":
                        dup_date = st.date_input("Duplicate to this date")
                        
                        if st.form_submit_button(f"🔄 Duplicate {len(selected_events)} Event(s)", use_container_width=True):
                            new_events = []
                            for idx in selected_events:
                                original = df.loc[idx].copy()
                                original["Date"] = pd.Timestamp(dup_date)
                                original["Date Modified"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                original["Action Type"] = "Duplicated"
                                original["Modified By"] = st.session_state.user_email
                                original["Title"] = generate_title(original)
                                new_events.append(original)
                            
                            df_new = pd.concat([df, pd.DataFrame(new_events)], ignore_index=True)
                            save_data(df_new)
                            st.success(f"✅ Created {len(new_events)} duplicate(s)!")
                            st.rerun()
                    
                    else:  # Date Range
                        col1, col2 = st.columns(2)
                        with col1:
                            range_start = st.date_input("Start Date")
                        with col2:
                            range_end = st.date_input("End Date")
                        
                        st.info(f"This will create duplicates for each day from {range_start} to {range_end}")
                        
                        if st.form_submit_button(f"🔄 Duplicate Across Date Range", use_container_width=True):
                            if range_end < range_start:
                                st.error("End date must be after start date!")
                            else:
                                new_events = []
                                for idx in selected_events:
                                    original = df.loc[idx].copy()
                                    
                                    current_date = range_start
                                    while current_date <= range_end:
                                        new_event = original.copy()
                                        new_event["Date"] = pd.Timestamp(current_date)
                                        new_event["Date Modified"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                        new_event["Action Type"] = "Duplicated"
                                        new_event["Modified By"] = st.session_state.user_email
                                        new_event["Title"] = generate_title(new_event)
                                        new_events.append(new_event)
                                        current_date += timedelta(days=1)
                                
                                df_new = pd.concat([df, pd.DataFrame(new_events)], ignore_index=True)
                                save_data(df_new)
                                st.success(f"✅ Created {len(new_events)} duplicate(s)!")
                                st.rerun()
            
            # DELETE
            with op_tab3:
                st.warning(f"⚠️ You are about to delete {len(selected_events)} event(s)")
                
                # Show events to be deleted
                for idx in selected_events:
                    st.write(f"- {df.loc[idx, 'Title']}")
                
                if st.button(f"🗑️ Delete {len(selected_events)} Event(s)", type="primary", use_container_width=True):
                    # Log deletion in remaining events
                    for idx in selected_events:
                        df.at[idx, "Action Type"] = "Deleted"
                        df.at[idx, "Modified By"] = st.session_state.user_email
                        df.at[idx, "Date Modified"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    
                    df = df.drop(selected_events).reset_index(drop=True)
                    save_data(df)
                    st.success(f"✅ Deleted {len(selected_events)} event(s)!")
                    st.rerun()
        
        else:
            st.info("👆 Select events using the checkboxes above to perform bulk operations")

# ---------- CALENDAR VIEW TAB ----------
with tab3:
    st.header("📅 Calendar View")
    
    # Month and Year selector
    col1, col2 = st.columns([1, 3])
    with col1:
        current_year = datetime.now().year
        selected_year = st.selectbox("Year", range(current_year - 1, current_year + 3), index=1)
    with col2:
        selected_month = st.selectbox("Month", range(1, 13), 
                                      format_func=lambda x: datetime(2000, x, 1).strftime('%B'),
                                      index=datetime.now().month - 1)
    
    # Trainer color legend
    st.subheader("Trainer Color Legend")
    legend_cols = st.columns(len(TRAINERS))
    for idx, trainer in enumerate(TRAINERS):
        with legend_cols[idx]:
            st.markdown(f"<div style='background-color: {TRAINER_COLORS[trainer]}; padding: 10px; border-radius: 5px; text-align: center; color: black; font-weight: bold;'>{trainer}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Filter events for selected month
    month_events = df[
        (pd.to_datetime(df["Date"]).dt.month == selected_month) & 
        (pd.to_datetime(df["Date"]).dt.year == selected_year)
    ].copy()
    
    # Generate calendar
    cal = calendar.monthcalendar(selected_year, selected_month)
    
    # Days of week header
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for idx, day in enumerate(days_of_week):
        with header_cols[idx]:
            st.markdown(f"<div style='text-align: center; font-weight: bold; padding: 5px;'>{day}</div>", unsafe_allow_html=True)
    
    # Calendar grid
    for week in cal:
        week_cols = st.columns(7)
        for idx, day in enumerate(week):
            with week_cols[idx]:
                if day == 0:
                    # Empty cell for days outside the month
                    st.markdown("<div style='height: 100px; border: 1px solid #ddd; border-radius: 5px;'></div>", unsafe_allow_html=True)
                else:
                    # Get events for this day
                    day_date = datetime(selected_year, selected_month, day)
                    day_events = month_events[pd.to_datetime(month_events["Date"]).dt.date == day_date.date()]
                    
                    # Create day cell
                    if len(day_events) > 0:
                        # Group events by trainer
                        trainer_counts = day_events["Trainer Calendar"].value_counts()
                        
                        # Build color indicators
                        color_bars = ""
                        for trainer in TRAINERS:
                            if trainer in trainer_counts:
                                count = trainer_counts[trainer]
                                color_bars += f"<div style='background-color: {TRAINER_COLORS[trainer]}; height: 8px; margin: 2px 0;'></div>"
                        
                        cell_html = f"""
                        <div style='border: 2px solid #333; border-radius: 5px; padding: 5px; height: 100px; background-color: #f9f9f9;'>
                            <div style='text-align: center; font-weight: bold; font-size: 18px; color: #000;'>{day}</div>
                            {color_bars}
                            <div style='text-align: center; font-size: 12px; margin-top: 5px; color: #000;'>{len(day_events)} event(s)</div>
                        </div>
                        """
                        st.markdown(cell_html, unsafe_allow_html=True)
                        
                        # Button to show details
                        if st.button(f"View Details", key=f"day_{day}", use_container_width=True):
                            st.session_state[f"selected_day"] = day_date
                    else:
                        # Empty day
                        st.markdown(f"""
                        <div style='border: 1px solid #ddd; border-radius: 5px; padding: 5px; height: 100px; background-color: #fff;'>
                            <div style='text-align: center; font-weight: bold; font-size: 18px; color: #999;'>{day}</div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Show event details when a day is selected
    st.divider()
    
    # Display all events for the month at the bottom
    st.subheader(f"📋 All Events in {datetime(2000, selected_month, 1).strftime('%B')} {selected_year}")
    
    if len(month_events) > 0:
        st.write(f"**Total: {len(month_events)} event(s)**")
        
        # Sort by date
        month_events_sorted = month_events.sort_values('Date')
        
        # Display events in expandable sections
        for idx, (event_idx, event) in enumerate(month_events_sorted.iterrows()):
            trainer_color = TRAINER_COLORS.get(event["Trainer Calendar"], "#CCCCCC")
            
            with st.expander(f"📅 {event['Date'].strftime('%b %d')} - **{event['Title']}**"):
                st.markdown(f"<div style='background-color: {trainer_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Trainer:** {event['Trainer Calendar']}")
                    st.write(f"**Type:** {event['Type']}")
                    st.write(f"**Status:** {event['Status']}")
                with col2:
                    st.write(f"**Client:** {event['Client']}")
                    st.write(f"**Source:** {event['Source']}")
                    st.write(f"**Medium:** {event['Medium']}")
                with col3:
                    st.write(f"**Location:** {event['Location']}")
                    st.write(f"**Invoiced:** {event['Invoiced']}")
                
                st.write(f"**Course:** {event['Course/Description']}")
                if event['Notes']:
                    st.write(f"**Notes:** {event['Notes']}")
                if event['Billing']:
                    st.write(f"**Billing:** {event['Billing']}")
                
                # Show modification info
                st.markdown("---")
                st.write(f"**Last Modified:** {event['Date Modified']} | **Action:** {event['Action Type']} | **By:** {event.get('Modified By', 'N/A')}")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Edit button for this event
                if st.button(f"✏️ Edit This Event", key=f"edit_cal_{event_idx}"):
                    st.session_state[f"edit_event_idx"] = event_idx
                    st.rerun()
        
        # Show edit form if an event is selected for editing
        if "edit_event_idx" in st.session_state:
            st.divider()
            st.subheader("✏️ Edit Event")
            
            edit_idx = st.session_state["edit_event_idx"]
            
            # Check if the event still exists
            if edit_idx in df.index:
                selected_event = df.loc[edit_idx]
                
                with st.form("calendar_edit_form"):
                    st.write(f"**Editing:** {selected_event['Title']}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        edit_start_date = st.date_input("Start Date", value=pd.to_datetime(selected_event["Date"]).date())
                        edit_end_date = st.date_input("End Date", value=pd.to_datetime(selected_event["Date"]).date())
                        st.info("💡 Changing dates will create separate events for each day")
                    
                    with c2:
                        edit_type = st.selectbox("Type", ["W", "C", "M"], 
                                                index=["W", "C", "M"].index(selected_event["Type"]))
                        edit_status = st.selectbox("Status", ["Offered", "Tentative", "Confirmed"],
                                                  index=["Offered", "Tentative", "Confirmed"].index(selected_event["Status"]))
                        edit_source = st.selectbox("Source", ["EQS", "CCE", "CTD"],
                                                  index=["EQS", "CCE", "CTD"].index(selected_event["Source"]))
                    with c3:
                        edit_client = st.text_input("Client", value=selected_event["Client"])
                        edit_course = st.text_input("Course / Description", value=selected_event["Course/Description"])
                        edit_trainer = st.selectbox("Trainer Calendar", TRAINERS,
                                                   index=TRAINERS.index(selected_event["Trainer Calendar"]))
                        edit_medium = st.selectbox("Medium", ["F2F", "Online"],
                                                  index=0 if selected_event["Medium"] == "F2F" else 1)

                    edit_location = st.selectbox("Location", LOCATIONS,
                                                index=LOCATIONS.index(selected_event["Location"]))
                    edit_billing = st.text_area("Billing Notes", value=selected_event["Billing"])
                    edit_invoiced = st.selectbox("Invoiced", ["No", "Yes"],
                                                index=0 if selected_event["Invoiced"] == "No" else 1)
                    edit_notes = st.text_area("Additional Notes", value=selected_event["Notes"])
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        save_changes = st.form_submit_button("💾 Save Changes", use_container_width=True)
                    with col_b:
                        cancel_edit = st.form_submit_button("❌ Cancel", use_container_width=True)
                    
                    if save_changes:
                        if edit_end_date < edit_start_date:
                            st.error("❌ End Date cannot be before Start Date!")
                        else:
                            # Delete the original event
                            df = df.drop(edit_idx).reset_index(drop=True)
                            
                            # Create events for the new date range
                            events_to_add = []
                            current_date = edit_start_date
                            
                            while current_date <= edit_end_date:
                                updated_row = {
                                    "Date": current_date,
                                    "Type": edit_type,
                                    "Status": edit_status,
                                    "Source": edit_source,
                                    "Client": edit_client,
                                    "Course/Description": edit_course,
                                    "Trainer Calendar": edit_trainer,
                                    "Medium": edit_medium,
                                    "Location": edit_location,
                                    "Billing": edit_billing,
                                    "Invoiced": edit_invoiced,
                                    "Notes": edit_notes,
                                    "Date Modified": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "Action Type": "Modified",
                                    "Modified By": st.session_state.user_email
                                }
                                updated_row["Title"] = generate_title(updated_row)
                                events_to_add.append(updated_row)
                                current_date += timedelta(days=1)
                            
                            # Add updated events
                            df = pd.concat([df, pd.DataFrame(events_to_add)], ignore_index=True)
                            save_data(df)
                            del st.session_state["edit_event_idx"]
                            st.success("✅ Event updated successfully!")
                            st.rerun()
                    
                    if cancel_edit:
                        del st.session_state["edit_event_idx"]
                        st.rerun()
            else:
                st.error("Event not found. It may have been deleted.")
                del st.session_state["edit_event_idx"]
                st.rerun()
    else:
        st.info("No events found for this month.")
    
    # Original day-click functionality (keep for backward compatibility)
    if "selected_day" in st.session_state:
        st.divider()
        selected_date = st.session_state["selected_day"]
        st.subheader(f"📋 Events on {selected_date.strftime('%B %d, %Y')}")
        
        day_events = month_events[pd.to_datetime(month_events["Date"]).dt.date == selected_date.date()]
        
        if len(day_events) > 0:
            for idx, (event_idx, event) in enumerate(day_events.iterrows()):
                trainer_color = TRAINER_COLORS.get(event["Trainer Calendar"], "#CCCCCC")
                
                with st.expander(f"**{event['Title']}**", expanded=True):
                    st.markdown(f"<div style='background-color: {trainer_color}; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Trainer:** {event['Trainer Calendar']}")
                        st.write(f"**Type:** {event['Type']}")
                        st.write(f"**Status:** {event['Status']}")
                    with col2:
                        st.write(f"**Client:** {event['Client']}")
                        st.write(f"**Source:** {event['Source']}")
                        st.write(f"**Medium:** {event['Medium']}")
                    with col3:
                        st.write(f"**Location:** {event['Location']}")
                        st.write(f"**Invoiced:** {event['Invoiced']}")
                    
                    st.write(f"**Course:** {event['Course/Description']}")
                    if event['Notes']:
                        st.write(f"**Notes:** {event['Notes']}")
                    if event['Billing']:
                        st.write(f"**Billing:** {event['Billing']}")
                    
                    # Show modification info
                    st.markdown("---")
                    st.write(f"**Last Modified:** {event['Date Modified']} | **Action:** {event['Action Type']} | **By:** {event.get('Modified By', 'N/A')}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No events on this date.")
        
        if st.button("Clear Selection"):
            del st.session_state["selected_day"]
            st.rerun()
