import streamlit as st
from datetime import datetime
import pandas as pd
import calendar
from core.utils import trainer_matches, get_events_for_day, marked_for_includes

def trainer_page(df, user_email, settings):
    TRAINERS, TRAINER_COLORS, trainer_name = settings["TRAINERS"], settings["TRAINER_COLORS"], settings["trainer_name"]

    st.info(f"🎓 Welcome {trainer_name}! This is your personal calendar.")
    st.header("📅 My Calendar")

    trainer_events = df[trainer_matches(df["Trainer Calendar"], trainer_name)]
    marked_events = df[
        (df["Is Marked"]==True) &
        (df["Marked For"].apply(lambda x: marked_for_includes(x, trainer_name)))
    ]
    df_my = pd.concat([trainer_events, marked_events], ignore_index=True)

    col1, col2 = st.columns([1,3])
    with col1:
        cy = datetime.now().year
        selected_year = st.selectbox("Year", range(cy-1, cy+3), index=1)
    with col2:
        selected_month = st.selectbox("Month", range(1,13),
                                      format_func=lambda x: datetime(2000,x,1).strftime("%B"),
                                      index=datetime.now().month-1)

    st.subheader("Your Color")
    st.markdown(
        f"<div style='background:{TRAINER_COLORS.get(trainer_name,'#ccc')};padding:10px;border-radius:5px;text-align:center;font-weight:bold;color:black;max-width:200px;'>{trainer_name}</div>",
        unsafe_allow_html=True
    )
    st.divider()

    month_events = df_my[
        (pd.to_datetime(df_my["Date"]).dt.month==selected_month) &
        (pd.to_datetime(df_my["Date"]).dt.year==selected_year)
    ].copy()

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
                if day==0:
                    st.markdown("<div style='height:120px;border:1px solid #ddd;border-radius:5px;'></div>",
                                unsafe_allow_html=True)
                else:
                    day_date = datetime(selected_year,selected_month,day).date()
                    day_events = get_events_for_day(month_events, day_date)

                    # check blocked for me
                    reason = None
                    marks = df[
                        (df["Is Marked"]==True) &
                        (pd.to_datetime(df["Date"]).dt.date==day_date)
                    ]
                    for _,m in marks.iterrows():
                        if marked_for_includes(m.get("Marked For","All"), trainer_name):
                            reason = str(m.get("Course/Description","Blocked"))
                            break

                    if reason:
                        disp=(reason[:18]+"...") if len(reason)>18 else reason
                        st.markdown(f"""
                        <div style='border:3px solid #FF0000;border-radius:5px;padding:5px;height:120px;background:#FFE0E0;'>
                            <div style='text-align:center;font-weight:bold;font-size:18px;color:#FF0000;'>{day}</div>
                            <div style='text-align:center;font-size:22px;margin-top:4px;'>🚫</div>
                            <div style='text-align:center;font-size:11px;color:#FF0000;font-weight:bold;'>{disp}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    elif len(day_events):
                        st.markdown(f"""
                        <div style='border:2px solid #333;border-radius:5px;padding:5px;height:120px;background:{TRAINER_COLORS.get(trainer_name,'#ccc')};'>
                            <div style='text-align:center;font-weight:bold;font-size:18px;color:#000;'>{day}</div>
                            <div style='text-align:center;font-size:12px;margin-top:5px;color:#000;'>{len(day_events)} event(s)</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='border:1px solid #ddd;border-radius:5px;padding:5px;height:120px;background:#fff;'>
                            <div style='text-align:center;font-weight:bold;font-size:18px;color:#999;'>{day}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    if st.button("View Details", key=f"trainer_view_{selected_year}_{selected_month}_{day}", use_container_width=True):
                        st.session_state["selected_day"] = day_date

    st.divider()
    # day details for trainer
    if "selected_day" in st.session_state and st.session_state["selected_day"]:
        sel_day = st.session_state["selected_day"]
        st.subheader(f"📌 My Events on {sel_day.strftime('%A, %d %B %Y')}")
        day_all = get_events_for_day(month_events, sel_day)
        if len(day_all)==0:
            st.info("No events on this day.")
        else:
            blocked_today = day_all[day_all.get("Is Marked", False)==True]
            normal_today = day_all[day_all.get("Is Marked", False)!=True]
            for _, ev in blocked_today.iterrows():
                with st.expander(f"🚫 BLOCKED: {ev.get('Course/Description','')}", expanded=True):
                    st.error("Blocked for you.")
                    st.write(f"Reason: {ev.get('Course/Description','')}")
            for _, ev in normal_today.iterrows():
                with st.expander(f"📅 {ev.get('Title','')}", expanded=True):
                    st.write(f"Type: {ev.get('Type','')} | Status: {ev.get('Status','')}")
                    st.write(f"Client: {ev.get('Client','')} | Source: {ev.get('Source','')}")
                    st.write(f"Medium: {ev.get('Medium','')} | Location: {ev.get('Location','')}")
                    st.write(f"Course: {ev.get('Course/Description','')}")

        if st.button("❌ Close Day Details", key="trainer_close_day"):
            st.session_state["selected_day"]=None
            st.rerun()

    return df
