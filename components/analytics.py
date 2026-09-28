import streamlit as st

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
        (
            df["Status"]
            .astype(str)
            .str.strip()
            == "Converted"
        ).sum()
    )

    followups = int(
        (
            df["Status"]
            .astype(str)
            .str.strip()
            == "Follow up"
        ).sum()
    )

    past_dated = int(
        (
            df["Status"]
            .astype(str)
            .str.strip()
            == "Past Dated"
        ).sum()
    )

    conversion_rate = (
        converted / total_leads * 100
        if total_leads
        else 0
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Total Leads",
            total_leads
        )

    with c2:

        st.metric(
            "Converted",
            converted
        )

    with c3:

        st.metric(
            "Conversion Rate",
            f"{conversion_rate:.1f}%"
        )

    with c4:

        st.metric(
            "Pending Follow-ups",
            followups
        )

    st.divider()

    # =================================================
    # AGENT PERFORMANCE
    # =================================================

    st.subheader(
        "👥 Agent Performance"
    )

    for agent in AGENTS:

        agent_df = df[
            df["Agent"]
            .astype(str)
            .str.strip()
            == agent
        ]

        total = len(agent_df)

        converted_agent = int(
            (
                agent_df["Status"]
                .astype(str)
                .str.strip()
                == "Converted"
            ).sum()
        )

        followup_agent = int(
            (
                agent_df["Status"]
                .astype(str)
                .str.strip()
                == "Follow up"
            ).sum()
        )

        conversion = (
            converted_agent / total * 100
            if total
            else 0
        )

        st.markdown(
            f"### 👤 {agent}"
        )

        a1, a2, a3, a4 = st.columns(4)

        with a1:

            st.metric(
                "Total Leads",
                total
            )

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

    st.subheader(
        "📌 Pipeline Status"
    )

    status_columns = st.columns(
        3
    )

    for index, status in enumerate(
        STATUSES
    ):

        count = int(
            (
                df["Status"]
                .astype(str)
                .str.strip()
                == status
            ).sum()
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

    st.subheader(
        "🔗 Lead Sources"
    )

    source_counts = (
        df["Source"]
        .astype(str)
        .str.strip()
        .replace(
            "",
            "Unknown"
        )
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
    ) in enumerate(
        source_counts.items()
    ):

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

    st.subheader(
        "🔔 Follow-up Insights"
    )

    if "Follow Up Count" not in df.columns:

        st.info(
            "Follow-up count data is not available."
        )

        return

    followup_counts = (
        df["Follow Up Count"]
        .astype(str)
        .str.strip()
    )

    followup_columns = st.columns(
        4
    )

    for index, followup in enumerate(
        FOLLOW_UP_OPTIONS
    ):

        count = int(
            (
                followup_counts
                == followup
            ).sum()
        )

        with followup_columns[
            index % 4
        ]:

            st.metric(
                followup,
                count
            )

    # =================================================
    # PAST DATED ALERT
    # =================================================

    if past_dated > 0:

        st.warning(
            f"⚠️ {past_dated} lead(s) "
            "are currently marked as Past Dated."
        )