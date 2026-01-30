import streamlit as st, calendar
from datetime import datetime
from core.utils import get_events_for_day
from core.rules import render_mixed_calendar_cell

def calendar_grid(month_events, selected_year, selected_month, TRAINERS, TRAINER_COLORS, role_prefix="admin"):
    cal = calendar.monthcalendar(selected_year, selected_month)
    days_of_week = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

    header_cols = st.columns(7)
    for i, dn in enumerate(days_of_week):
        with header_cols[i]:
            st.markdown(f"<div style='text-align:center;font-weight:bold;padding:5px;'>{dn}</div>",
                        unsafe_allow_html=True)

    for week in cal:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            with week_cols[i]:
                if day == 0:
                    st.markdown("<div style='height:120px;border:1px solid #ddd;border-radius:5px;'></div>",
                                unsafe_allow_html=True)
                else:
                    day_date = datetime(selected_year, selected_month, day).date()
                    day_events = get_events_for_day(month_events, day_date)

                    rendered = render_mixed_calendar_cell(day, day_events, TRAINERS, TRAINER_COLORS)
                    if not rendered:
                        st.markdown(f"""
                        <div style='border:1px solid #ddd;border-radius:5px;padding:5px;height:120px;background:#fff;'>
                            <div style='text-align:center;font-weight:bold;font-size:18px;color:#999;'>{day}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    if st.button("View Details",
                                 key=f"{role_prefix}_view_{selected_year}_{selected_month}_{day}",
                                 use_container_width=True):
                        st.session_state["selected_day"] = day_date
