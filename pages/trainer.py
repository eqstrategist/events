import streamlit as st
from datetime import datetime
from io import BytesIO

import pandas as pd

from ui.calendar_grid import calendar_grid
from ui.shared import trainer_legend


def trainer_page(df: pd.DataFrame, user_email: str, settings: dict):
    """
    Trainer view.

    app.py calls:

        trainer_page(
            df,
            user_email,
            {
                "TRAINERS": TRAINERS,
                "TRAINER_COLORS": TRAINER_COLORS,
                "trainer_name": trainer_name,
            },
        )

    This page provides:
      - Tab 1: 📅 My Calendar   (visual month view for this trainer + "View Details" by day)
      - Tab 2: 🔍 My Events     (read-only filtered list of this trainer's events)

    Trainers CANNOT:
      - Edit events
      - Delete events
      - Duplicate events
      - Filter by trainer (they only see their own events)
    """

    TRAINERS = settings.get("TRAINERS", [])
    TRAINER_COLORS = settings.get("TRAINER_COLORS", {})
    trainer_name = settings.get("trainer_name", "Trainer")

    st.title(f"🎓 Trainer View – {trainer_name}")

    # Restrict dataframe to this trainer's events only (supports multi-trainer strings)
    df_trainer = df[
        df["Trainer Calendar"].astype(str).str.contains(trainer_name, case=False, na=False)
    ].copy()

    tab1, tab2 = st.tabs(["📅 My Calendar", "🔍 My Events"])

    # -------------------------------------------------------------------------
    # TAB 1 – MY CALENDAR
    # -------------------------------------------------------------------------
    with tab1:
        st.subheader("📅 My Calendar")

        current_year = datetime.now().year
        col_year, col_month = st.columns([1, 3])
        with col_year:
            selected_year = st.selectbox(
                "Year",
                range(current_year - 1, current_year + 3),
                index=1,
                key="trainer_calendar_year",
            )
        with col_month:
            selected_month = st.selectbox(
                "Month",
                range(1, 13),
                format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
                index=datetime.now().month - 1,
                key="trainer_calendar_month",
            )

        # Trainer's own color legend
        st.subheader("Your Color")
        trainer_legend(
            [trainer_name],
            {trainer_name: TRAINER_COLORS.get(trainer_name, "#CCCCCC")},
        )
        st.divider()

        # Filter to this trainer & this month
        month_events = df_trainer[
            (pd.to_datetime(df_trainer["Date"]).dt.year == selected_year)
            & (pd.to_datetime(df_trainer["Date"]).dt.month == selected_month)
        ].copy()

        # Use calendar grid with a "trainer" prefix, but the grid sets st.session_state["selected_day"]
        calendar_grid(
            month_events,
            selected_year,
            selected_month,
            [trainer_name],
            {trainer_name: TRAINER_COLORS.get(trainer_name, "#CCCCCC")},
            role_prefix="trainer",
        )

        st.divider()

        # -------------------------------
        # "View Details" behaviour
        # calendar_grid sets st.session_state["selected_day"] = day_date
        # -------------------------------
        sel_day = st.session_state.get("selected_day", None)

        if sel_day is not None:
            # sel_day might be datetime or date
            if isinstance(sel_day, datetime):
                day_date = sel_day.date()
            else:
                day_date = sel_day

            st.subheader(f"📌 Your Events on {day_date.strftime('%A, %d %B %Y')}")

            day_events = month_events[
                pd.to_datetime(month_events["Date"]).dt.date == day_date
            ].sort_values("Date")

            if len(day_events) == 0:
                st.info("No events for you on this day.")
            else:
                st.write(f"**Total: {len(day_events)} event(s)**")
                for _, ev in day_events.iterrows():
                    with st.expander(
                        f"📅 {pd.to_datetime(ev['Date']).strftime('%b %d')} – {ev['Title']}",
                        expanded=True,
                    ):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Type:** {ev['Type']}")
                            st.write(f"**Status:** {ev['Status']}")
                        with col2:
                            st.write(f"**Client:** {ev['Client']}")
                            st.write(f"**Source:** {ev['Source']}")
                            st.write(f"**Medium:** {ev['Medium']}")
                        with col3:
                            st.write(f"**Location:** {ev['Location']}")
                            st.write(f"**Invoiced:** {ev['Invoiced']}")

                        st.write(f"**Course/Description:** {ev['Course/Description']}")
                        notes = str(ev.get("Notes", ""))
                        billing = str(ev.get("Billing", ""))
                        if notes not in ["nan", "", None]:
                            st.write(f"**Notes:** {notes}")
                        if billing not in ["nan", "", None]:
                            st.write(f"**Billing:** {billing}")

                        st.markdown("---")
                        st.write(
                            f"**Last Modified:** {ev.get('Date Modified','')} | "
                            f"**Action:** {ev.get('Action Type','')} | "
                            f"**By:** {ev.get('Modified By','')}"
                        )

            if st.button("❌ Close Day Details", key="trainer_close_day_details"):
                st.session_state["selected_day"] = None
                st.rerun()

        else:
            # No specific day selected: show all events for this month (as a list)
            st.subheader(
                f"📋 Your Events – {datetime(2000, selected_month, 1).strftime('%B')} {selected_year}"
            )

            if len(month_events) == 0:
                st.info("No events found for this month.")
            else:
                month_events_sorted = month_events.sort_values("Date")
                st.write(f"**Total: {len(month_events_sorted)} event(s)**")

                for _, ev in month_events_sorted.iterrows():
                    with st.expander(
                        f"📅 {pd.to_datetime(ev['Date']).strftime('%b %d')} – {ev['Title']}"
                    ):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**Type:** {ev['Type']}")
                            st.write(f"**Status:** {ev['Status']}")
                        with col2:
                            st.write(f"**Client:** {ev['Client']}")
                            st.write(f"**Source:** {ev['Source']}")
                            st.write(f"**Medium:** {ev['Medium']}")
                        with col3:
                            st.write(f"**Location:** {ev['Location']}")
                            st.write(f"**Invoiced:** {ev['Invoiced']}")

                        st.write(f"**Course/Description:** {ev['Course/Description']}")
                        notes = str(ev.get("Notes", ""))
                        billing = str(ev.get("Billing", ""))
                        if notes not in ["nan", "", None]:
                            st.write(f"**Notes:** {notes}")
                        if billing not in ["nan", "", None]:
                            st.write(f"**Billing:** {billing}")

                        st.markdown("---")
                        st.write(
                            f"**Last Modified:** {ev.get('Date Modified','')} | "
                            f"**Action:** {ev.get('Action Type','')} | "
                            f"**By:** {ev.get('Modified By','')}"
                        )

    # -------------------------------------------------------------------------
    # TAB 2 – MY EVENTS (READ-ONLY MANAGE-LIKE VIEW)
    # -------------------------------------------------------------------------
    with tab2:
        st.subheader("🔍 My Events")
      

        # ---- Filters (date range, status, source, client) ----
        col_filters = st.columns(4)

        # 1) Date range toggle
        with col_filters[0]:
            use_date_range = st.checkbox("Filter by Date Range", value=False)

        date_from = date_to = None
        if use_date_range:
            col_dates = st.columns(2)
            with col_dates[0]:
                date_from = st.date_input("From", key="trainer_events_from")
            with col_dates[1]:
                date_to = st.date_input("To", key="trainer_events_to")

        # Build choices for status and source based on the trainer's own data
        status_values = sorted(df_trainer["Status"].dropna().unique().tolist())
        source_values = sorted(df_trainer["Source"].dropna().unique().tolist())

        status_options = ["All"] + status_values
        source_options = ["All"] + source_values

        with col_filters[1]:
            status_filter = st.selectbox(
                "Status", status_options, key="trainer_events_status"
            )

        with col_filters[2]:
            source_filter = st.selectbox(
                "Source", source_options, key="trainer_events_source"
            )

        with col_filters[3]:
            client_search = st.text_input(
                "Client",
                key="trainer_events_client",
                placeholder="Search client name...",
            )

        # ---- Apply filters to trainer's own events ----
        result = df_trainer.copy()

        # Date range
        if use_date_range and date_from and date_to:
            if date_to < date_from:
                st.warning("⚠️ 'To' date cannot be before 'From' date.")
            else:
                result = result[
                    (pd.to_datetime(result["Date"]).dt.date >= date_from)
                    & (pd.to_datetime(result["Date"]).dt.date <= date_to)
                ]

        # Status filter
        if status_filter != "All":
            result = result[result["Status"] == status_filter]

        # Source filter
        if source_filter != "All":
            result = result[result["Source"] == source_filter]

        # Client text search
        if client_search:
            result = result[
                result["Client"].astype(str).str.contains(
                    client_search, case=False, na=False
                )
            ]

        st.markdown("---")
        st.write(f"**Showing {len(result)} event(s)**")

        if len(result) == 0:
            st.info("No events match the current filters.")
        else:
            # Sort by date and show as a table (view-only)
            result = result.sort_values("Date")

            st.dataframe(
                result[
                    [
                        "Date",
                        "Title",
                        "Status",
                        "Source",
                        "Client",
                        "Course/Description",
                        "Medium",
                        "Location",

                    ]
                ],
                use_container_width=True,
            )

            # Optional: allow trainer to download their filtered data (still read-only)
            towrite = BytesIO()
            result.to_excel(towrite, index=False, engine="openpyxl")
            towrite.seek(0)

            st.download_button(
                "⬇️ Download My Filtered Events",
                data=towrite,
                file_name="My_Events.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    # Trainers do not modify df, so just return it unchanged
    return df
