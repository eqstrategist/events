import os, time
import streamlit as st
from .storage import read_sheet, write_sheet, append_audit, load_settings
import pandas as pd

def refresh_session_passwords(users_df):
    st.session_state.user_passwords = {
        row["Email"].lower(): row.get("Password", "Welcome123")
        for _, row in users_df.iterrows()
    }

def login_page(AUTHORIZED_EMAILS, users_df):

    # Hide sidebar entirely on login/reset screens
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        section[data-testid="stSidebar"] { display: none !important; }
        /* Remove left padding Streamlit leaves for sidebar */
        .block-container { padding-left: 2rem; padding-right: 2rem; }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown("""
    <style>
    .stApp { background-color: white; }
    .stButton>button {
        background-color: #FF6B35; color: white; border: none;
        padding: 10px 24px; font-weight: bold;
    }
    .stButton>button:hover { background-color: #E85A2A; color: white; }
    h1, h2, h3, p, label, div { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.5,2,1.5])
    with col2:
        st.markdown("<div style='text-align:center;margin-top:30px;'>", unsafe_allow_html=True)
        if os.path.exists("logo.png"):
            st.image("logo.png", width=150)
        else:
            st.title("🗓️ EQS Event Scheduling")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<h3 style='text-align:center;'>🔐 Login to Access</h3>", unsafe_allow_html=True)

        if "reset_mode" not in st.session_state:
            st.session_state.reset_mode = False

        if not st.session_state.reset_mode:
            with st.form("login_form"):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                col_a, col_b = st.columns(2)
                submit = col_a.form_submit_button("Login", use_container_width=True)
                reset = col_b.form_submit_button("Reset Password", use_container_width=True)

                if submit:
                    email_lower = email.lower().strip()
                    if email_lower in AUTHORIZED_EMAILS:
                        if st.session_state.user_passwords.get(email_lower) == password:
                            st.session_state.authenticated = True
                            st.session_state.user_email = email_lower
                            append_audit(email_lower, "Login", "User logged in")
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Incorrect password.")
                    else:
                        st.error("❌ Access denied.")

                if reset:
                    st.session_state.reset_mode = True
                    st.rerun()
        else:
            with st.form("reset_form"):
                email = st.text_input("Email Address")
                old_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")

                col_a, col_b = st.columns(2)
                submit_reset = col_a.form_submit_button("Update Password", use_container_width=True)
                cancel = col_b.form_submit_button("Cancel", use_container_width=True)

                if submit_reset:
                    email_lower = email.lower().strip()
                    if email_lower in AUTHORIZED_EMAILS:
                        if st.session_state.user_passwords.get(email_lower) == old_password:
                            if new_password == confirm_password:
                                if len(new_password) >= 6:
                                    users_df.loc[users_df["Email"].str.lower()==email_lower, "Password"] = new_password
                                    write_sheet("Users", users_df)
                                    refresh_session_passwords(users_df)
                                    append_audit(email_lower, "Password Reset", "User reset password")
                                    st.success("✅ Password updated!")
                                    st.session_state.reset_mode = False
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("❌ Password must be at least 6 characters.")
                            else:
                                st.error("❌ Passwords do not match.")
                        else:
                            st.error("❌ Incorrect current password.")
                    else:
                        st.error("❌ Email not found.")

                if cancel:
                    st.session_state.reset_mode = False
                    st.rerun()

def ensure_login(AUTHORIZED_EMAILS, users_df):
    if "user_passwords" not in st.session_state:
        refresh_session_passwords(users_df)
    if not st.session_state.get("authenticated", False):
        login_page(AUTHORIZED_EMAILS, users_df)
        st.stop()
    return st.session_state.user_email

def get_current_user_role(users_df, email):
    row = users_df[users_df["Email"].str.lower()==email.lower()]
    return row.iloc[0]["Role"] if len(row) else None

def get_trainer_name(users_df, email):
    row = users_df[users_df["Email"].str.lower()==email.lower()]
    if len(row)==0: return None
    return row.iloc[0].get("TrainerName", None)
