import html
import pandas as pd
import streamlit as st
from .utils import marked_for_includes
from datetime import datetime

def is_date_blocked_for_trainer(df_all, date_obj, trainer):
    # Check if "Is Marked" column exists, default to False if not
    is_marked = df_all["Is Marked"] if "Is Marked" in df_all.columns else False
    marks = df_all[
        (is_marked == True) &
        (pd.to_datetime(df_all["Date"]).dt.date == date_obj)
    ]
    for _, m in marks.iterrows():
        if marked_for_includes(m.get("Marked For", "All"), trainer):
            return True
    return False

def render_mixed_calendar_cell(day, day_events, TRAINERS, TRAINER_COLORS):
    # Check if "Is Marked" column exists, default to False if not
    is_marked = day_events["Is Marked"] if "Is Marked" in day_events.columns else False
    marked_event = day_events[is_marked == True]
    normal_events = day_events[is_marked != True]

    badges = []
    if len(marked_event):
        for _, mark in marked_event.iterrows():
            reason_raw = str(mark.get("Course/Description", "Blocked"))
            who_raw = str(mark.get("Marked For", "All"))
            reason = html.escape(reason_raw)
            who = html.escape(who_raw)
            display_reason = (reason[:16] + "...") if len(reason) > 16 else reason
            badge = (
                "<div style='margin-top:4px;padding:2px 4px;border-radius:4px;"
                "background:#FFE0E0;border:1px solid #FF0000;font-size:10px;"
                "color:#FF0000;font-weight:bold;text-align:center;'>"
                f"🚫 {display_reason}<br/>"
                f"<span style='font-weight:normal;'>For: {who}</span>"
                "</div>"
            )
            badges.append(badge)
    blocked_html = "".join(badges)

    color_bars = ""
    event_count_text = ""
    if len(normal_events):
        all_trainers_today = set()
        for _, ev in normal_events.iterrows():
            trainers_in_event = [t.strip() for t in str(ev.get("Trainer Calendar","")).split(",")]
            all_trainers_today.update(trainers_in_event)
        for t in TRAINERS:
            if t in all_trainers_today:
                color_bars += (
                    f"<div style='background:{TRAINER_COLORS.get(t,'#ccc')};"
                    "height:8px;margin:2px 0;'></div>"
                )
        event_count_text = (
            "<div style='text-align:center;font-size:12px;margin-top:5px;color:#000;'>"
            f"{len(normal_events)} event(s)</div>"
        )

    if len(marked_event) or len(normal_events):
        border_color = "#FF0000" if len(marked_event) else "#333"
        bg_color = "#FFECEC" if len(marked_event) else "#f9f9f9"
        cell_html = (
            f"<div style='border:2px solid {border_color};"
            "border-radius:5px;padding:5px;height:120px;"
            f"background:{bg_color};overflow:auto;'>"
            f"<div style='text-align:center;font-weight:bold;font-size:18px;color:#000;'>{day}</div>"
            f"{color_bars}{event_count_text}{blocked_html}"
            "</div>"
        )
        st.markdown(cell_html, unsafe_allow_html=True)
        return True
    return False
