import streamlit as st

from config import STATUSES
from components.lead_card import render_lead_card


BOARD_STATUS_ORDER = [
    "Quotation Given",
    "Follow up",
    "Converted",
    "No Availability",
    "Out of Budget",
    "Ghosted",
    "Not Interested",
]


STATUS_ICONS = {
    "Follow up": "🟡",
    "Quotation Given": "🔵",
    "Converted": "🟢",
    "No Availability": "⚪",
    "Out of Budget": "🔴",
    "Ghosted": "🟣",
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
    # PAGINATION SETTINGS
    # -------------------------------------------------

    PAGE_SIZE = 25

    page_key = f"board_page_{selected_status}"

    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    total_leads = len(selected_df)

    total_pages = max(
        1,
        (total_leads + PAGE_SIZE - 1) // PAGE_SIZE,
    )

    # Keep the current page within valid limits.
    st.session_state[page_key] = min(
        max(1, st.session_state[page_key]),
        total_pages,
    )

    current_page = st.session_state[page_key]

    # Select only the leads for the current page.
    start = (current_page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE

    page_df = selected_df.iloc[start:end]

    # -------------------------------------------------
    # DISPLAY LEADS
    # -------------------------------------------------

    for _, record in page_df.iterrows():

        result = render_lead_card(record)

        if result:
            return result

    # -------------------------------------------------
    # PAGINATION CONTROLS BELOW THE LEADS
    # -------------------------------------------------

    st.divider()

    page_col1, page_col2, page_col3 = st.columns([1, 2, 1])

    with page_col1:

        if st.button(
                "← Previous",
                disabled=current_page <= 1,
                key=f"prev_bottom_{selected_status}",
                use_container_width=True,
        ):
            st.session_state[page_key] -= 1
            st.rerun()

    with page_col2:

        st.markdown(
            f"""
            <div style="text-align:center; padding-top:8px;">
                Page {current_page} of {total_pages}
                <br>
                <span style="font-size:12px; opacity:0.7;">
                    Showing {start + 1}–{min(end, total_leads)}
                    of {total_leads} leads
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with page_col3:

        if st.button(
                "Next →",
                disabled=current_page >= total_pages,
                key=f"next_bottom_{selected_status}",
                use_container_width=True,
        ):
            st.session_state[page_key] += 1
            st.rerun()

    return None