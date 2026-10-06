import streamlit as st
import pandas as pd
import plotly.graph_objects as go


# ============================================================
# STATUS CONFIGURATION
# ============================================================

STATUS_ORDER = [
    "Follow up",
    "Quotation Given",
    "Converted",
    "No Availability",
    "Out of Budget",
    "Ghosted",
    "Not Interested",
]


# ============================================================
# DISTINCT STATUS COLORS
# ============================================================

STATUS_COLORS = {
    "Follow up": "#F59E0B",          # Orange
    "Quotation Given": "#3B82F6",    # Blue
    "Converted": "#22C55E",          # Green
    "No Availability": "#06B6D4",   # Cyan
    "Out of Budget": "#EF4444",      # Red
    "Ghosted": "#A855F7",            # Purple
    "Not Interested": "#64748B",     # Slate
}


# ============================================================
# CHART COLORS
# ============================================================

CHART_BG = "#0E1117"
TEXT_COLOR = "#F8FAFC"
MUTED_TEXT = "#CBD5E1"
GRID_COLOR = "#29313D"


# ============================================================
# COMMON FIGURE SETTINGS
# ============================================================

def _base_layout(
    title,
    height=480,
    x_title=None,
    y_title=None,
):
    return dict(

        # ====================================================
        # TITLE
        # ====================================================

        title=dict(
            text=title,
            x=0,
            xanchor="left",
            y=0.98,
            yanchor="top",
            font=dict(
                size=20,
                color=TEXT_COLOR,
            ),
        ),

        # ====================================================
        # BACKGROUND
        # ====================================================

        paper_bgcolor=CHART_BG,

        plot_bgcolor=CHART_BG,

        # ====================================================
        # FONT
        # ====================================================

        font=dict(
            color=TEXT_COLOR,
            size=12,
        ),

        # ====================================================
        # HEIGHT
        # ====================================================

        height=height,

        # ====================================================
        # MARGINS
        # ====================================================

        margin=dict(
            l=70,
            r=30,
            t=90,
            b=80,
        ),

        # ====================================================
        # HOVER
        # ====================================================

        hoverlabel=dict(
            bgcolor="#111827",
            bordercolor="#374151",
            font=dict(
                color="#F9FAFB",
                size=12,
            ),
        ),

        hovermode="closest",

        # ====================================================
        # LEGEND
        # ====================================================

        legend=dict(
            font=dict(
                color=TEXT_COLOR,
                size=11,
            ),
        ),
    )


# ============================================================
# DATE PARSER
# ============================================================

def _parse_dates(series):

    return pd.to_datetime(
        series
        .fillna("")
        .astype(str)
        .str.strip(),
        dayfirst=True,
        errors="coerce",
    )


# ============================================================
# 1. DAILY LEAD DISTRIBUTION
# ============================================================

def _render_leads_by_date(df):

    if df is None or df.empty:
        st.info(
            "No lead data available for the selected filters."
        )
        return

    if "Date" not in df.columns:
        st.warning(
            "The Date column is not available."
        )
        return

    if "Status" not in df.columns:
        st.warning(
            "The Status column is not available."
        )
        return

    chart_df = df[
        ["Date", "Status"]
    ].copy()

    chart_df["Lead Date"] = _parse_dates(
        chart_df["Date"]
    )

    chart_df["Status"] = (
        chart_df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    chart_df = chart_df.dropna(
        subset=["Lead Date"]
    )

    chart_df = chart_df[
        chart_df["Status"] != ""
    ]

    if chart_df.empty:
        st.info(
            "No valid Lead Date / Status data available."
        )
        return

    # --------------------------------------------------------
    # DATE + STATUS COUNTS
    # --------------------------------------------------------

    daily_status = (
        chart_df
        .groupby(
            ["Lead Date", "Status"]
        )
        .size()
        .unstack(
            fill_value=0
        )
    )

    # --------------------------------------------------------
    # ENSURE EVERY STATUS EXISTS
    # --------------------------------------------------------

    for status in STATUS_ORDER:

        if status not in daily_status.columns:
            daily_status[status] = 0

    daily_status = daily_status[
        STATUS_ORDER
    ]

    daily_status = daily_status.sort_index()

    # --------------------------------------------------------
    # DISPLAY DATES
    # --------------------------------------------------------

    dates = [
        d.strftime("%d-%m-%Y")
        for d in daily_status.index
    ]

    # --------------------------------------------------------
    # TOTAL PER DATE
    # --------------------------------------------------------

    totals = (
        daily_status
        .sum(axis=1)
        .astype(int)
    )

    # --------------------------------------------------------
    # FIGURE
    # --------------------------------------------------------

    fig = go.Figure()

    # --------------------------------------------------------
    # STACKED STATUS BARS
    # --------------------------------------------------------

    for status in STATUS_ORDER:

        values = (
            daily_status[status]
            .astype(int)
            .tolist()
        )

        fig.add_trace(
            go.Bar(

                x=dates,

                y=values,

                name=status,

                marker=dict(
                    color=STATUS_COLORS[status],
                    line=dict(
                        width=0,
                    ),
                ),

                # NO NUMBERS INSIDE BARS
                text=None,

                texttemplate=None,

                hovertemplate=(
                    "<b>%{x}</b>"
                    "<br>"
                    f"{status}: "
                    "<b>%{y}</b>"
                    "<extra></extra>"
                ),
            )
        )

    # --------------------------------------------------------
    # TOTAL NUMBER ABOVE EACH BAR
    # --------------------------------------------------------

    for date_label, total in zip(
        dates,
        totals,
    ):

        if total <= 0:
            continue

        fig.add_annotation(

            x=date_label,

            y=int(total),

            text=f"<b>{int(total)}</b>",

            showarrow=False,

            yshift=10,

            font=dict(
                size=13,
                color=TEXT_COLOR,
            ),

            xanchor="center",

            yanchor="bottom",
        )

    # --------------------------------------------------------
    # DYNAMIC Y AXIS
    # --------------------------------------------------------

    max_total = (
        int(totals.max())
        if not totals.empty
        else 0
    )

    if max_total <= 10:
        tick = 2
    elif max_total <= 20:
        tick = 5
    elif max_total <= 50:
        tick = 5
    elif max_total <= 100:
        tick = 10
    elif max_total <= 200:
        tick = 20
    else:
        tick = 50

    y_max = max(
        5,
        int(max_total * 1.18) + 1,
    )

    # --------------------------------------------------------
    # LAYOUT
    # --------------------------------------------------------

    fig.update_layout(

        title=dict(
            text="Daily Lead Distribution",
            x=0,
            xanchor="left",
            font=dict(
                size=20,
                color=TEXT_COLOR,
            ),
        ),

        barmode="stack",

        bargap=0.25,

        paper_bgcolor=CHART_BG,

        plot_bgcolor=CHART_BG,

        height=560,

        margin=dict(
            l=75,
            r=30,
            t=115,
            b=95,
        ),

        font=dict(
            color=TEXT_COLOR,
        ),

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,

            font=dict(
                color=TEXT_COLOR,
                size=12,
            ),

            bgcolor="rgba(0,0,0,0)",
        ),

        xaxis=dict(

            title=dict(
                text="Lead Date",
                font=dict(
                    color=TEXT_COLOR,
                    size=13,
                ),
            ),

            type="category",

            tickangle=-30,

            tickfont=dict(
                color=MUTED_TEXT,
                size=11,
            ),

            showgrid=False,

            showline=False,

            zeroline=False,

            automargin=True,

            categoryorder="array",

            categoryarray=dates,
        ),

        yaxis=dict(

            title=dict(
                text="Number of Leads",
                font=dict(
                    color=TEXT_COLOR,
                    size=13,
                ),
            ),

            range=[
                0,
                y_max,
            ],

            dtick=tick,

            tickfont=dict(
                color=MUTED_TEXT,
                size=11,
            ),

            gridcolor=GRID_COLOR,

            gridwidth=1,

            showgrid=True,

            showline=False,

            zeroline=False,

            rangemode="tozero",

            automargin=True,
        ),

        hoverlabel=dict(
            bgcolor="#111827",
            bordercolor="#374151",
            font=dict(
                color="#FFFFFF",
                size=12,
            ),
        ),

        hovermode="closest",
    )

    # --------------------------------------------------------
    # RENDER
    # --------------------------------------------------------

    st.plotly_chart(
        fig,
        use_container_width=True,

        config={
            "displaylogo": False,
            "responsive": True,
            "scrollZoom": False,
            "modeBarButtonsToRemove": [
                "select2d",
                "lasso2d",
                "autoScale2d",
                "toggleSpikelines",
            ],
        },

        key="analytics_daily_lead_distribution",
    )


# ============================================================
# 2. LEADS BY AGENT
# ============================================================

def _render_leads_by_agent(df):

    if df is None or df.empty:
        return

    if "Agent" not in df.columns:
        return

    agent_counts = (
        df["Agent"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts()
    )

    if agent_counts.empty:
        return

    agents = agent_counts.index.tolist()

    values = agent_counts.values.tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(

            x=agents,

            y=values,

            marker=dict(
                color="#3B82F6",
            ),

            text=[
                str(int(v))
                for v in values
            ],

            textposition="outside",

            cliponaxis=False,

            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Leads: "
                "<b>%{y}</b>"
                "<extra></extra>"
            ),
        )
    )

    max_value = (
        int(max(values))
        if values
        else 0
    )

    fig.update_layout(
        **_base_layout(
            "Leads by Agent",
            height=470,
            x_title="Agent",
            y_title="Number of Leads",
        ),

        showlegend=False,

        yaxis=dict(
            title="Number of Leads",
            rangemode="tozero",
            range=[
                0,
                max(
                    5,
                    int(max_value * 1.18) + 1,
                ),
            ],
            gridcolor=GRID_COLOR,
            tickfont=dict(
                color=MUTED_TEXT,
            ),
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
        },
        key="analytics_leads_by_agent",
    )


# ============================================================
# 3. REVENUE BY AGENT
# ============================================================

def _amount(value):

    if value is None:
        return 0.0

    try:

        if pd.isna(value):
            return 0.0

    except Exception:
        pass

    text = str(value).strip()

    if not text:
        return 0.0

    text = (
        text
        .replace("₹", "")
        .replace(",", "")
        .replace(" ", "")
    )

    if text.upper().startswith("INR"):
        text = text[3:]

    try:
        return float(text)
    except (
        ValueError,
        TypeError,
    ):
        return 0.0


def _render_revenue_by_agent(df):

    if df is None or df.empty:
        return

    if "Agent" not in df.columns:
        return

    if "Total Amount" not in df.columns:
        return

    working_df = df.copy()

    # Only Converted revenue
    if "Status" in working_df.columns:

        status = (
            working_df["Status"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        working_df = working_df[
            status == "Converted"
        ]

    if working_df.empty:
        st.info(
            "No converted revenue available."
        )
        return

    working_df["Revenue"] = (
        working_df["Total Amount"]
        .apply(_amount)
    )

    revenue = (
        working_df
        .groupby(
            working_df["Agent"]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
            .replace("", "Unknown")
        )["Revenue"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    if revenue.empty:
        return

    agents = revenue.index.tolist()

    values = [
        float(v)
        for v in revenue.values
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(

            x=agents,

            y=values,

            marker=dict(
                color="#22C55E",
            ),

            text=[
                f"₹{v:,.0f}"
                for v in values
            ],

            textposition="outside",

            cliponaxis=False,

            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Revenue: "
                "<b>₹%{y:,.0f}</b>"
                "<extra></extra>"
            ),
        )
    )

    max_value = (
        max(values)
        if values
        else 0
    )

    fig.update_layout(
        **_base_layout(
            "Revenue by Agent",
            height=470,
            x_title="Agent",
            y_title="Revenue",
        ),

        showlegend=False,

        yaxis=dict(
            title="Revenue",
            rangemode="tozero",
            range=[
                0,
                max(
                    1000,
                    max_value * 1.18,
                ),
            ],
            gridcolor=GRID_COLOR,
            tickfont=dict(
                color=MUTED_TEXT,
            ),

            tickprefix="₹",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
        },
        key="analytics_revenue_by_agent",
    )


# ============================================================
# 4. LEAD SOURCE DISTRIBUTION
# ============================================================

def _render_lead_source_distribution(df):

    if df is None or df.empty:
        return

    if "Source" not in df.columns:
        return

    source_counts = (
        df["Source"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
        .value_counts()
    )

    if source_counts.empty:
        return

    sources = source_counts.index.tolist()

    values = source_counts.values.tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(

            x=sources,

            y=values,

            marker=dict(
                color="#8B5CF6",
            ),

            text=[
                str(int(v))
                for v in values
            ],

            textposition="outside",

            cliponaxis=False,

            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Leads: "
                "<b>%{y}</b>"
                "<extra></extra>"
            ),
        )
    )

    max_value = (
        int(max(values))
        if values
        else 0
    )

    fig.update_layout(

        **_base_layout(
            "Lead Source Distribution",
            height=500,
            x_title="Source",
            y_title="Number of Leads",
        ),

        showlegend=False,

        xaxis=dict(
            title="Source",
            tickangle=-35,
            tickfont=dict(
                color=MUTED_TEXT,
                size=10,
            ),
            showgrid=False,
            automargin=True,
        ),

        yaxis=dict(
            title="Number of Leads",
            range=[
                0,
                max(
                    5,
                    int(max_value * 1.18) + 1,
                ),
            ],
            gridcolor=GRID_COLOR,
            rangemode="tozero",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
        },
        key="analytics_lead_source_distribution",
    )


# ============================================================
# 5. FOLLOW-UP COUNT DISTRIBUTION
# ============================================================

def _render_followup_distribution(df):

    if df is None or df.empty:
        return

    if "Follow Up Count" not in df.columns:
        return

    followup_order = [
        f"Follow up {i}"
        for i in range(1, 9)
    ]

    followup_series = (
        df["Follow Up Count"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    counts = (
        followup_series
        .value_counts()
        .reindex(
            followup_order,
            fill_value=0,
        )
    )

    values = counts.values.tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(

            x=followup_order,

            y=values,

            marker=dict(
                color="#F59E0B",
            ),

            text=[
                str(int(v))
                for v in values
            ],

            textposition="outside",

            cliponaxis=False,

            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Leads: "
                "<b>%{y}</b>"
                "<extra></extra>"
            ),
        )
    )

    max_value = (
        max(values)
        if values
        else 0
    )

    fig.update_layout(

        **_base_layout(
            "Follow-up Count Distribution",
            height=470,
            x_title="Follow-up",
            y_title="Number of Leads",
        ),

        showlegend=False,

        xaxis=dict(
            title="Follow-up",
            tickangle=-25,
            tickfont=dict(
                color=MUTED_TEXT,
                size=10,
            ),
            showgrid=False,
            automargin=True,
        ),

        yaxis=dict(
            title="Number of Leads",
            range=[
                0,
                max(
                    5,
                    int(max_value * 1.18) + 1,
                ),
            ],
            gridcolor=GRID_COLOR,
            rangemode="tozero",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
        },
        key="analytics_followup_distribution",
    )


# ============================================================
# 6. CONVERSION BY AGENT
# ============================================================

def _render_conversion_by_agent(df):

    if df is None or df.empty:
        return

    if "Agent" not in df.columns:
        return

    if "Status" not in df.columns:
        return

    working_df = df.copy()

    working_df["Agent"] = (
        working_df["Agent"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .replace("", "Unknown")
    )

    working_df["Status"] = (
        working_df["Status"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    agent_total = (
        working_df
        .groupby("Agent")
        .size()
    )

    agent_converted = (
        working_df[
            working_df["Status"] == "Converted"
        ]
        .groupby("Agent")
        .size()
    )

    conversion = (
        agent_converted
        .reindex(
            agent_total.index,
            fill_value=0,
        )
        / agent_total
        * 100
    )

    conversion = (
        conversion
        .fillna(0)
        .sort_values(
            ascending=False
        )
    )

    if conversion.empty:
        return

    agents = conversion.index.tolist()

    values = [
        float(v)
        for v in conversion.values
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(

            x=agents,

            y=values,

            marker=dict(
                color="#06B6D4",
            ),

            text=[
                f"{v:.1f}%"
                for v in values
            ],

            textposition="outside",

            cliponaxis=False,

            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Conversion: "
                "<b>%{y:.1f}%</b>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(

        **_base_layout(
            "Conversion by Agent",
            height=470,
            x_title="Agent",
            y_title="Conversion Rate",
        ),

        showlegend=False,

        xaxis=dict(
            title="Agent",
            tickfont=dict(
                color=MUTED_TEXT,
            ),
            showgrid=False,
        ),

        yaxis=dict(
            title="Conversion Rate",
            range=[
                0,
                max(
                    10,
                    min(
                        100,
                        max(values) * 1.2,
                    ),
                ),
            ],
            ticksuffix="%",
            gridcolor=GRID_COLOR,
            rangemode="tozero",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
        },
        key="analytics_conversion_by_agent",
    )


# ============================================================
# MAIN ANALYTICS CHART FUNCTION
# ============================================================

def render_analytics_charts(df):

    if df is None or df.empty:

        st.info(
            "No data available for analytics charts."
        )

        return

    # ========================================================
    # 1. DAILY LEAD DISTRIBUTION
    # ========================================================

    st.markdown(
        "### 📅 Leads by Date"
    )

    st.caption(
        "Lead distribution by Lead Date and pipeline status."
    )

    _render_leads_by_date(
        df
    )

    st.divider()

    # ========================================================
    # 2. LEADS BY AGENT
    # ========================================================

    st.markdown(
        "### 👥 Agent Performance"
    )

    _render_leads_by_agent(
        df
    )

    st.divider()

    # ========================================================
    # 3. REVENUE BY AGENT
    # ========================================================

    st.markdown(
        "### 💰 Revenue by Agent"
    )

    _render_revenue_by_agent(
        df
    )

    st.divider()

    # ========================================================
    # 4. LEAD SOURCE DISTRIBUTION
    # ========================================================

    st.markdown(
        "### 🔗 Lead Source Distribution"
    )

    _render_lead_source_distribution(
        df
    )

    st.divider()

    # ========================================================
    # 5. FOLLOW-UP COUNT DISTRIBUTION
    # ========================================================

    st.markdown(
        "### 🔔 Follow-up Count Distribution"
    )

    _render_followup_distribution(
        df
    )

    st.divider()

    # ========================================================
    # 6. CONVERSION BY AGENT
    # ========================================================

    st.markdown(
        "### 🎯 Conversion by Agent"
    )

    _render_conversion_by_agent(
        df
    )