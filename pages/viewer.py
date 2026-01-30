import streamlit as st
from datetime import datetime
import pandas as pd
from ui.calendar_grid import calendar_grid
from ui.day_details import day_details_panel
from ui.shared import trainer_legend

def viewer_page(df, user_email, settings):
    TRAINERS, TRAINER_COLORS = settings["TRAINERS"], settings["TRAINER_COLORS"]

    st.info("👁️ You have view-only access.")
    st.header("📅 Calendar View (Read Only)")

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

    calendar_grid(month_events, selected_year, selected_month, TRAINERS, TRAINER_COLORS, role_prefix="viewer")
    st.divider()
    df = day_details_panel(month_events, df, can_unmark=False, close_key="viewer_close_day")
    return df
