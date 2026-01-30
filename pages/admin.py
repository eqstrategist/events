import streamlit as st
from datetime import datetime
import pandas as pd
from ui.event_forms import new_event_tab, manage_events_tab
from ui.calendar_grid import calendar_grid
from ui.day_details import day_details_panel
from ui.mark_dates import mark_dates_tab
from ui.settings_page import settings_tab
from ui.shared import trainer_legend

def admin_page(df, user_email, settings):
    (TRAINERS, TRAINER_COLORS, TYPES, STATUSES, SOURCES, MEDIUMS, LOCATIONS,
     DEFAULT_TYPE, DEFAULT_STATUS, DEFAULT_SOURCE, DEFAULT_MEDIUM, DEFAULT_LOCATION,
     RULE_ONLY_ADMIN_CAN_BLOCK, RULE_BLOCK_PREVENT_DUPLICATES,
     users_df, trainers_df, lists_df, rules_df, defaults_df, notif_df, EXCEL_FILE, refresh_pw_cb) = settings

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ New Event","🔍 Manage Events","📅 Calendar View","🚫 Mark Dates","⚙️ Settings"
    ])

    with tab1:
        df = new_event_tab(df, user_email, TRAINERS, TYPES, STATUSES, SOURCES, MEDIUMS, LOCATIONS,
                           DEFAULT_TYPE, DEFAULT_STATUS, DEFAULT_SOURCE, DEFAULT_MEDIUM, DEFAULT_LOCATION)

    with tab2:
        df = manage_events_tab(df, user_email, TRAINERS, STATUSES, SOURCES, LOCATIONS, MEDIUMS, TYPES, RULE_BLOCK_PREVENT_DUPLICATES)

    with tab3:
        st.header("📅 Calendar View")
        col1, col2 = st.columns([1,3])
        with col1:
            cy = datetime.now().year
            selected_year = st.selectbox("Year", range(cy-1, cy+3), index=1)
        with col2:
            selected_month = st.selectbox("Month", range(1,13),
                                          format_func=lambda x: datetime(2000,x,1).strftime("%B"),
                                          index=datetime.now().month-1)

        trainer_legend(TRAINERS, TRAINER_COLORS)
        st.divider()

        month_events = df[
            (pd.to_datetime(df["Date"]).dt.month==selected_month) &
            (pd.to_datetime(df["Date"]).dt.year==selected_year)
        ].copy()

        calendar_grid(month_events, selected_year, selected_month, TRAINERS, TRAINER_COLORS, role_prefix="admin")
        st.divider()
        df = day_details_panel(month_events, df, can_unmark=True, close_key="admin_close_day")

        st.divider()
        st.subheader(f"📋 All Events in {datetime(2000,selected_month,1).strftime('%B')} {selected_year}")
        if len(month_events):
            for _, ev in month_events.sort_values("Date").iterrows():
                if ev.get("Is Marked", False):
                    with st.expander(f"🚫 {ev['Date'].strftime('%b %d')} - BLOCKED ({ev.get('Marked For','All')}): {ev.get('Course/Description','')}"):
                        st.error(f"Blocked for: {ev.get('Marked For','All')}")
                    continue
                with st.expander(f"📅 {ev['Date'].strftime('%b %d')} - **{ev.get('Title','')}**"):
                    st.write(f"Trainer: {ev.get('Trainer Calendar','')}")
                    st.write(f"Status: {ev.get('Status','')} | Type: {ev.get('Type','')}")
                    st.write(f"Client: {ev.get('Client','')} | Source: {ev.get('Source','')}")
                    st.write(f"Medium: {ev.get('Medium','')} | Location: {ev.get('Location','')}")
                    st.write(f"Course: {ev.get('Course/Description','')}")
        else:
            st.info("No events in this month.")

    with tab4:
        df = mark_dates_tab(df, user_email, TRAINERS, RULE_ONLY_ADMIN_CAN_BLOCK, "admin")

    with tab5:
        settings_tab(users_df, trainers_df, lists_df, rules_df, defaults_df, notif_df, EXCEL_FILE, refresh_pw_cb, user_email)

    return df
