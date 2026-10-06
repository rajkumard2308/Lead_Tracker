import streamlit as st
import pandas as pd

from config import (
    AGENTS,
    STATUSES,
)


FOLLOW_UP_OPTIONS = [
    f"Follow up {i}"
    for i in range(1, 9)
]


def render_analytics(df):

    # =================================================
    # EMPTY
    # =================================================

    if df.empty:

        st.info(
            "No data available for analytics."
        )

        return

    # =================================================
    # PRECOMPUTE COMMON SERIES ONCE
    # =================================================

    status_series = (
        df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    agent_series = (
        df["Agent"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    source_series = (
        df["Source"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if "Total Amount" in df.columns:

        amount_series = pd.to_numeric(
            df["Total Amount"],
            errors="coerce",
        ).fillna(0.0)

    else:

        amount_series = pd.Series(
            0.0,
            index=df.index,
        )

    # =================================================
    # HEADER
    # =================================================

    st.title(
        "📊 Agent Performance & Insights"
    )

    st.caption(
        "Performance summary based on the "
        "currently selected filters."
    )

    # =================================================
    # BASIC METRICS
    # =================================================

    total_leads = len(df)

    converted = int(
        (status_series == "Converted").sum()
    )

    followups = int(
        (status_series == "Follow up").sum()
    )

    ghosted = int(
        (status_series == "Ghosted").sum()
    )

    conversion_rate = (
        converted / total_leads * 100
        if total_leads
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Total Leads", total_leads)

    with c2:
        st.metric("Converted", converted)

    with c3:
        st.metric(
            "Conversion Rate",
            f"{conversion_rate:.1f}%"
        )

    with c4:
        st.metric("Pending Follow-ups", followups)

    st.divider()

    # =================================================
    # AGENT PERFORMANCE
    # =================================================

    st.subheader("👥 Agent Performance")

    for agent in AGENTS:

        agent_mask = (
            agent_series == agent
        )

        total = int(agent_mask.sum())

        agent_status = status_series.loc[
            agent_mask
        ]

        agent_amount = amount_series.loc[
            agent_mask
        ]

        converted_agent = int(
            (agent_status == "Converted").sum()
        )

        followup_agent = int(
            (agent_status == "Follow up").sum()
        )

        conversion = (
            converted_agent / total * 100
            if total
            else 0
        )

        agent_revenue = float(
            agent_amount.sum()
        )

        st.markdown(
            f"### 👤 {agent}"
        )

        a1, a2, a3, a4, a5 = st.columns(5)

        with a1:
            st.metric("Total Leads", total)

        with a2:
            st.metric(
                "Converted",
                converted_agent
            )

        with a3:
            st.metric(
                "Follow Ups",
                followup_agent
            )

        with a4:
            st.metric(
                "Conversion",
                f"{conversion:.1f}%"
            )

        with a5:
            st.metric(
                "Total Revenue",
                f"₹{agent_revenue:,.0f}"
            )

        if total > 0:
            st.progress(
                min(
                    conversion / 100,
                    1.0
                )
            )

        st.divider()

    # =================================================
    # PIPELINE STATUS
    # =================================================

    st.subheader("📌 Pipeline Status")

    status_columns = st.columns(3)

    for index, status in enumerate(STATUSES):

        count = int(
            (status_series == status).sum()
        )

        with status_columns[
            index % 3
        ]:

            st.metric(
                status,
                count
            )

    st.divider()

    # =================================================
    # LEAD SOURCES
    # =================================================

    st.subheader("🔗 Lead Sources")

    source_counts = (
        source_series
        .replace("", "Unknown")
        .value_counts()
    )

    source_columns = st.columns(
        min(
            max(
                len(source_counts),
                1
            ),
            4
        )
    )

    for index, (
        source,
        count
    ) in enumerate(source_counts.items()):

        with source_columns[
            index % len(source_columns)
        ]:

            st.metric(
                str(source),
                int(count)
            )

    st.divider()

    # =================================================
    # FOLLOW-UP INSIGHTS
    # =================================================

    st.subheader("🔔 Follow-up Insights")

    if "Follow Up Count" not in df.columns:

        st.info(
            "Follow-up count data is not available."
        )

        return

    followup_counts = (
        df["Follow Up Count"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # One value_counts() is faster than scanning the
    # DataFrame eight separate times.
    followup_value_counts = (
        followup_counts.value_counts()
    )

    followup_columns = st.columns(4)

    for index, followup in enumerate(
        FOLLOW_UP_OPTIONS
    ):

        count = int(
            followup_value_counts.get(
                followup,
                0,
            )
        )

        with followup_columns[
            index % 4
        ]:

            st.metric(
                followup,
                count
            )

    # =================================================
    # GHOSTED ALERT
    # =================================================

    if ghosted > 0:

        st.warning(
            f"⚠️ {ghosted} lead(s) "
            "are currently marked as Ghosted."
        )
