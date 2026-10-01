import streamlit as st

from config import STATUSES
from components.lead_card import render_lead_card


BOARD_STATUS_ORDER = [
    "Quotation Given",
    "Follow up",
    "Converted",
    "No Availability",
    "Out of Budget",
    "Past Dated",
    "Not Interested",
]


STATUS_ICONS = {
    "Follow up": "🟡",
    "Quotation Given": "🔵",
    "Converted": "🟢",
    "No Availability": "⚪",
    "Out of Budget": "🔴",
    "Past Dated": "🟣",
}


def render_board(df):

    if "selected_status" not in st.session_state:
        st.session_state["selected_status"] = "Quotation Given"

    # -------------------------------------------------
    # STATUS NAVIGATION
    # -------------------------------------------------

    st.markdown(
        """
        <div class="section-heading">
            Lead Conversion Board
        </div>
        """,
        unsafe_allow_html=True,
    )

    status_columns = st.columns(len(BOARD_STATUS_ORDER))

    for index, status in enumerate(BOARD_STATUS_ORDER):

        count = int(
            (
                df["Status"]
                .astype(str)
                .str.strip()
                == status
            ).sum()
        )

        selected = (
            st.session_state["selected_status"]
            == status
        )

        button_text = (
            f"{STATUS_ICONS.get(status, '•')} "
            f"{status}  •  {count}"
        )

        with status_columns[index]:

            if st.button(
                button_text,
                key=f"board_status_{status}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state["selected_status"] = status
                st.rerun()

    # -------------------------------------------------
    # SELECTED STATUS
    # -------------------------------------------------

    selected_status = st.session_state["selected_status"]

    selected_df = df[
        df["Status"]
        .astype(str)
        .str.strip()
        == selected_status
    ].copy()

    selected_df = selected_df.sort_values(
        by="_sheet_row",
        ascending=False,
    )

    st.markdown(
        f"""
        <div class="selected-status-header">
            <div>
                <span class="selected-status-icon">
                    {STATUS_ICONS.get(selected_status, "•")}
                </span>
                <span class="selected-status-title">
                    {selected_status}
                </span>
            </div>
            <span class="selected-count">
                {len(selected_df)} Leads
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if selected_df.empty:

        st.markdown(
            """
            <div class="empty-board">
                <div class="empty-icon">📭</div>
                <div class="empty-title">
                    No leads in this stage
                </div>
                <div class="empty-text">
                    Leads assigned to this pipeline stage will appear here.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return None

    # -------------------------------------------------
    # TABLE HEADER
    # -------------------------------------------------

    st.markdown(
        """
        <div class="lead-table-header">
            <div>CLIENT</div>
            <div>PHONE</div>
            <div>STAY DATES</div>
            <div>AGENT / SOURCE</div>
            <div>FOLLOW-UP</div>
            <div>ACTIONS</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------
    # LEADS
    # -------------------------------------------------

    for _, record in selected_df.iterrows():

        result = render_lead_card(record)

        if result:
            return result

    return None