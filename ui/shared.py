import streamlit as st

def trainer_legend(TRAINERS, TRAINER_COLORS):
    st.subheader("Trainer Color Legend")
    legend_cols = st.columns(len(TRAINERS))
    for i, t in enumerate(TRAINERS):
        with legend_cols[i]:
            st.markdown(
                f"<div style='background:{TRAINER_COLORS.get(t,'#ccc')};padding:10px;border-radius:5px;text-align:center;font-weight:bold;color:black;'>{t}</div>",
                unsafe_allow_html=True
            )
