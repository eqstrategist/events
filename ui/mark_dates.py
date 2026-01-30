import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from core.storage import save_events
from core.utils import marked_for_includes

def mark_dates_tab(df, user_email, TRAINERS, RULE_ONLY_ADMIN_CAN_BLOCK, user_role):
    st.header("🚫 Mark Dates (Holidays/Blocked Days)")
    st.info("Mark dates for ALL trainers or specific trainer(s). Mixed calendar will still show other trainers' events.")

    col1, col2 = st.columns(2)
    with col1:
        with st.form("mark_dates_form"):
            mark_start = st.date_input("Start Date", key="mark_start")
            mark_end = st.date_input("End Date", value=mark_start, key="mark_end")

            mark_scope = st.radio("Block Scope", ["All Trainers","Specific Trainer(s)"], horizontal=True)
            selected_trainers=[]
            if mark_scope=="Specific Trainer(s)":
                selected_trainers=st.multiselect("Choose trainer(s) to block", TRAINERS)

            mark_reason = st.text_input("Reason", placeholder="e.g., Leave, Holiday")

            if st.form_submit_button("🚫 Mark Dates", use_container_width=True):
                if RULE_ONLY_ADMIN_CAN_BLOCK and user_role != "admin":
                    st.error("Only admins can block.")
                elif mark_end < mark_start:
                    st.error("End date before start.")
                elif mark_scope=="Specific Trainer(s)" and not selected_trainers:
                    st.error("Pick trainer(s).")
                else:
                    marked_for_value = "All" if mark_scope=="All Trainers" else ", ".join(selected_trainers)

                    marked_to_add=[]
                    cur=mark_start
                    while cur<=mark_end:
                        existing=df[
                            (pd.to_datetime(df["Date"]).dt.date==cur) &
                            (df["Is Marked"]==True) &
                            (df["Marked For"].fillna("").str.strip()==marked_for_value)
                        ]
                        if len(existing)==0:
                            new_mark={
                                "Date":cur,
                                "Type":"M",
                                "Status":"Blocked",
                                "Source":"Admin",
                                "Client":"N/A",
                                "Course/Description":mark_reason if mark_reason else "Marked Date",
                                "Trainer Calendar":marked_for_value,
                                "Medium":"N/A",
                                "Location":"N/A",
                                "Billing":"",
                                "Invoiced":"No",
                                "Notes":mark_reason if mark_reason else "",
                                "Date Modified":datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "Action Type":"Marked",
                                "Modified By":user_email,
                                "Is Marked":True,
                                "Marked For":marked_for_value
                            }
                            new_mark["Title"]=f"🚫 BLOCKED ({marked_for_value}) - {mark_reason if mark_reason else 'Marked Date'}"
                            marked_to_add.append(new_mark)
                        cur+=timedelta(days=1)

                    if marked_to_add:
                        df=pd.concat([df,pd.DataFrame(marked_to_add)],ignore_index=True)
                        save_events(df)
                        st.success(f"✅ Marked {len(marked_to_add)} day(s) for {marked_for_value}")
                        st.rerun()
                    else:
                        st.warning("All dates already marked for that scope.")

    with col2:
        st.subheader("Currently Marked")
        marked_dates=df[df["Is Marked"]==True].sort_values("Date")
        if len(marked_dates):
            for idx,row in marked_dates.iterrows():
                with st.expander(f"🚫 {row['Date'].strftime('%Y-%m-%d')} - {row['Course/Description']} (For: {row.get('Marked For')})"):
                    st.write(f"**Reason:** {row['Course/Description']}")
                    st.write(f"**Blocked For:** {row.get('Marked For')}")
                    if st.button("✅ Unmark", key=f"unmark_{idx}"):
                        df=df.drop(idx).reset_index(drop=True)
                        save_events(df)
                        st.success("Unmarked!")
                        st.rerun()
        else:
            st.info("No blocked dates.")

    return df
