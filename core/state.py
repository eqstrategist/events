import streamlit as st

def init_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "reset_mode" not in st.session_state:
        st.session_state.reset_mode = False
    if "selected_day" not in st.session_state:
        st.session_state.selected_day = None
