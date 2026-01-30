import streamlit as st
from core.utils import get_events_for_day
from core.storage import save_events

def day_details_panel(month_events, df, can_unmark=False, close_key="close_day"):
    if "selected_day" not in st.session_state or not st.session_state["selected_day"]:
        return df

    sel_day = st.session_state["selected_day"]
    st.subheader(f"📌 Events on {sel_day.strftime('%A, %d %B %Y')}")

    day_all = get_events_for_day(month_events, sel_day)
    if len(day_all) == 0:
        st.info("No events on this day.")
    else:
        blocked_today = day_all[day_all.get("Is Marked", False) == True]
        normal_today  = day_all[day_all.get("Is Marked", False) != True]

        if len(blocked_today):
            for idx, ev in blocked_today.iterrows():
                with st.expander(
                    f"🚫 BLOCKED ({ev.get('Marked For','All')}): {ev.get('Course/Description','')}",
                    expanded=True
                ):
                    st.error(f"Blocked for: {ev.get('Marked For','All')}")
                    st.write(f"**Reason:** {ev.get('Course/Description','')}")
                    st.write(f"**Marked by:** {ev.get('Modified By','N/A')}")
                    st.write(f"**Modified:** {ev.get('Date Modified','')}")
                    if can_unmark and st.button("✅ Unmark this date", key=f"unmark_day_{idx}"):
                        df = df.drop(idx).reset_index(drop=True)
                        save_events(df)
                        st.success("✅ Date unmarked!")
                        st.session_state["selected_day"] = None
                        st.rerun()

        if len(normal_today):
            for _, ev in normal_today.iterrows():
                with st.expander(f"📅 {ev.get('Title','')}", expanded=True):
                    st.write(f"**Trainer:** {ev.get('Trainer Calendar','')}")
                    st.write(f"**Type:** {ev.get('Type','')} | **Status:** {ev.get('Status','')}")
                    st.write(f"**Client:** {ev.get('Client','')} | **Source:** {ev.get('Source','')}")
                    st.write(f"**Medium:** {ev.get('Medium','')} | **Location:** {ev.get('Location','')}")
                    st.write(f"**Course/Description:** {ev.get('Course/Description','')}")
                    notes = str(ev.get("Notes",""))
                    billing = str(ev.get("Billing",""))
                    if notes not in ["nan","",None]:
                        st.write(f"**Notes:** {notes}")
                    if billing not in ["nan","",None]:
                        st.write(f"**Billing:** {billing}")

    if st.button("❌ Close Day Details", key=close_key):
        st.session_state["selected_day"] = None
        st.rerun()

    return df
