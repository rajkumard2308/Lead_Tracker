import streamlit as st
import pandas as pd

from config import (
    PAGE_TITLE,
    PAGE_ICON,
    STATUSES,
    SOURCES,
)

from google_sheet import (
    get_leads,
    add_lead,
    update_lead,
    delete_lead,
)

from components.dashboard import (
    render_dashboard,
)

from components.board import (
    render_board,
)

from components.lead_form import (
    render_add_lead_form,
    render_edit_lead_form,
)

from components.analytics import (
    render_analytics,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# SESSION STATE
# ============================================================

if "show_add_form" not in st.session_state:
    st.session_state["show_add_form"] = False

if "editing_row" not in st.session_state:
    st.session_state["editing_row"] = None

if "deleting_row" not in st.session_state:
    st.session_state["deleting_row"] = None

if "filter_by_date" not in st.session_state:
    st.session_state["filter_by_date"] = False


# ============================================================
# PROFESSIONAL UI CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
    ======================================================== */

    .main {
        background: #f8fafc;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1,
    h2,
    h3 {
        color: #172033;
    }


    /* ========================================================
       HEADER
    ======================================================== */

    .main-title {
        font-size: 32px;
        font-weight: 800;
        color: #172033;
        letter-spacing: -0.5px;
        margin-bottom: 3px;
    }

    .sub-title {
        color: #64748b;
        font-size: 14px;
        margin-bottom: 22px;
    }


    /* ========================================================
       STATUS HEADER
    ======================================================== */

    .selected-status-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        background: #ffffff;

        border: 1px solid #e2e8f0;

        border-radius: 12px;

        padding: 16px 20px;

        margin: 18px 0 12px 0;

        box-shadow:
            0 2px 8px rgba(15, 23, 42, 0.04);
    }

    .selected-status-title {
        font-size: 20px;
        font-weight: 750;
        color: #172033;
    }

    .selected-status-icon {
        font-size: 20px;
        margin-right: 8px;
    }

    .selected-count {
        background: #eef2ff;
        color: #4338ca;

        border-radius: 999px;

        padding: 6px 12px;

        font-size: 12px;
        font-weight: 700;
    }


    /* ========================================================
       TABLE HEADER
    ======================================================== */

    .lead-table-header {
        display: grid;

        grid-template-columns:
            1.35fr
            1.55fr
            1.55fr
            1.55fr
            1.45fr
            1.25fr;

        gap: 12px;

        padding: 10px 14px;

        color: #64748b;

        font-size: 10px;

        font-weight: 800;

        letter-spacing: 0.6px;
    }


    /* ========================================================
       LEAD ROW
    ======================================================== */

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;

        border-radius: 12px !important;

        border: 1px solid #e5e7eb !important;

        box-shadow:
            0 2px 8px rgba(15, 23, 42, 0.03);

        margin-bottom: 8px;
    }

    .lead-name {
        font-size: 14px;

        font-weight: 750;

        color: #172033;

        margin-bottom: 5px;
    }

    .lead-date {
        color: #64748b;
        font-size: 11px;
    }

    .lead-email {
        color: #64748b;

        font-size: 11px;

        margin-top: 6px;

        word-break: break-word;
    }

    .field-label {
        font-size: 9px;

        font-weight: 800;

        color: #94a3b8;

        letter-spacing: 0.5px;

        margin-bottom: 3px;
    }

    .field-value {
        font-size: 12px;

        color: #334155;

        margin-bottom: 3px;
    }

    .agent-name {
        font-size: 12px;

        font-weight: 650;

        color: #334155;

        margin-bottom: 6px;
    }

    .source-name {
        font-size: 11px;
        color: #64748b;
    }

    .muted-field {
        color: #94a3b8;
        font-size: 11px;
    }

    .booking-date {
        display: inline-block;

        margin-top: 7px;

        padding: 4px 7px;

        background: #ecfdf5;

        color: #047857;

        border-radius: 6px;

        font-size: 10px;

        font-weight: 650;
    }

    .followup-badge {
        display: inline-block;

        background: #fff7ed;

        color: #c2410c;

        border: 1px solid #fed7aa;

        border-radius: 6px;

        padding: 5px 8px;

        font-size: 10px;

        font-weight: 700;

        margin-bottom: 7px;
    }


    /* ========================================================
       EMPTY BOARD
    ======================================================== */

    .empty-board {
        background: #ffffff;

        border: 1px dashed #cbd5e1;

        border-radius: 14px;

        padding: 50px 20px;

        text-align: center;

        margin-top: 10px;
    }

    .empty-icon {
        font-size: 36px;
        margin-bottom: 10px;
    }

    .empty-title {
        font-size: 16px;

        font-weight: 700;

        color: #334155;
    }

    .empty-text {
        color: #94a3b8;

        font-size: 13px;

        margin-top: 5px;
    }


    /* ========================================================
       ANALYTICS
    ======================================================== */

    .analytics-title {
        font-size: 28px;

        font-weight: 800;

        color: #172033;

        margin-top: 15px;
    }

    .analytics-subtitle {
        color: #64748b;

        font-size: 13px;

        margin-bottom: 20px;
    }

    .analytics-table-wrapper {
        width: 100%;

        overflow-x: auto;

        background: #ffffff;

        border: 1px solid #e5e7eb;

        border-radius: 12px;

        margin-top: 10px;
    }

    .analytics-table {
        width: 100%;

        border-collapse: collapse;

        font-size: 13px;
    }

    .analytics-table th {
        background: #f8fafc;

        color: #64748b;

        text-align: left;

        padding: 13px 15px;

        font-size: 11px;

        text-transform: uppercase;

        letter-spacing: 0.5px;
    }

    .analytics-table td {
        padding: 14px 15px;

        border-top: 1px solid #f1f5f9;

        color: #334155;
    }

    .progress-container {
        width: 120px;

        height: 7px;

        background: #e2e8f0;

        border-radius: 999px;

        display: inline-block;

        vertical-align: middle;

        margin-right: 8px;
    }

    .progress-bar {
        height: 100%;

        background: #6366f1;

        border-radius: 999px;
    }

    .percentage {
        font-size: 11px;

        font-weight: 700;

        color: #475569;
    }

    .summary-row {
        display: flex;

        justify-content: space-between;

        align-items: center;

        padding: 10px 0;

        border-bottom: 1px solid #f1f5f9;
    }

    .summary-progress {
        width: 240px;

        height: 5px;

        background: #e2e8f0;

        border-radius: 999px;

        margin-top: 6px;
    }

    .summary-progress-fill {
        height: 100%;

        background: #6366f1;

        border-radius: 999px;
    }

    .summary-count {
        font-weight: 800;

        color: #172033;

        font-size: 14px;
    }

    .insight-card {
        background: #ffffff;

        border: 1px solid #e5e7eb;

        border-radius: 12px;

        padding: 15px;

        text-align: center;
    }

    .insight-label {
        font-size: 11px;

        color: #64748b;

        font-weight: 650;
    }

    .insight-number {
        font-size: 28px;

        font-weight: 800;

        color: #172033;

        margin-top: 4px;
    }

    .insight-small {
        color: #94a3b8;

        font-size: 10px;
    }

    .analytics-empty {
        padding: 30px;

        background: #ffffff;

        border: 1px dashed #cbd5e1;

        border-radius: 12px;

        color: #64748b;

        text-align: center;
    }


    /* ========================================================
       FILTER DATE BOX
    ======================================================== */

    .date-filter-title {
        font-size: 13px;
        font-weight: 700;
        color: #334155;
        margin-top: 8px;
        margin-bottom: 4px;
    }


    /* ========================================================
       EDIT DIALOG
    ======================================================== */

    div[data-testid="stDialog"] [data-testid="stVerticalBlockBorderWrapper"] {
        border: 0 !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* ========================================================
       BUTTONS
    ======================================================== */

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 12px;
    }

    /* ========================================================
       HEADER ADD LEAD BUTTON
    ======================================================== */

    .add-lead-header-button {
        width: 100%;
        min-width: 150px;
        padding-top: 2px;
    }

    .add-lead-header-button button {
        width: 100% !important;
        min-width: 150px !important;
        height: 42px !important;
        padding: 0 16px !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
    }


    /* ========================================================
       MOBILE
    ======================================================== */

    @media(max-width: 900px) {

        .lead-table-header {
            display: none;
        }

        .selected-status-title {
            font-size: 17px;
        }

        .add-lead-header-button {
            min-width: 130px;
        }

        .add-lead-header-button button {
            min-width: 130px !important;
            font-size: 12px !important;
        }

    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DELETE DIALOG
# ============================================================

@st.dialog("🗑️ Delete Lead")
def delete_lead_dialog(row_number, lead_name):

    st.write(
        f"Are you sure you want to delete **{lead_name}**?"
    )

    st.warning(
        "This action will permanently remove the lead "
        "from the Google Sheet."
    )

    delete_col1, delete_col2 = st.columns(2)

    # --------------------------------------------------------
    # YES DELETE
    # --------------------------------------------------------

    with delete_col1:

        if st.button(
            "🗑️ Yes, Delete Lead",
            type="primary",
            use_container_width=True,
            key=f"confirm_delete_{row_number}",
        ):

            try:

                delete_lead(
                    int(row_number)
                )

                st.session_state[
                    "deleting_row"
                ] = None

                st.cache_data.clear()

                st.rerun()

            except ValueError as exc:

                st.warning(
                    f"⚠️ {exc}"
                )

            except Exception as exc:

                st.error(
                    f"Could not delete lead: {exc}"
                )

    # --------------------------------------------------------
    # CANCEL
    # --------------------------------------------------------

    with delete_col2:

        if st.button(
            "Cancel",
            use_container_width=True,
            key=f"cancel_delete_{row_number}",
        ):

            st.session_state[
                "deleting_row"
            ] = None

            st.rerun()


# ============================================================
# HEADER
# ============================================================

header_left, header_right = st.columns(
    [5.8, 1.2],
    gap="medium",
)

with header_left:

    st.markdown(
        """
        <div class="main-title">
            📈 2026 Lead Conversion Board
        </div>

        <div class="sub-title">
            Pipeline Tracking, Conversion Velocity & Follow-Up Management
        </div>
        """,
        unsafe_allow_html=True,
    )


with header_right:

    st.markdown(
        '<div class="add-lead-header-button">',
        unsafe_allow_html=True,
    )

    if st.button(
        "➕ Add Lead",
        type="primary",
        use_container_width=True,
        key="header_add_lead",
    ):

        st.session_state[
            "show_add_form"
        ] = True

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# GOOGLE SHEETS
# ============================================================

try:

    df = get_leads()

except Exception as exc:

    st.error(
        "Unable to connect to Google Sheets."
    )

    st.exception(exc)

    st.stop()


# ============================================================
# MAKE SURE REQUIRED COLUMNS EXIST
# ============================================================

required_columns = [
    "Date",
    "Name",
    "Number",
    "Email",
    "Check In Date",
    "Check Out Date",
    "Booking Confirmation Date",
    "Agent",
    "Status",
    "Source",
    "Last Follow Up",
    "Follow Up Count",
    "Remarks",
    "Total Amount",
    "_sheet_row",
]

for column in required_columns:

    if column not in df.columns:
        df[column] = ""


# ============================================================
# ADD LEAD FORM
# ============================================================

if st.session_state.get(
    "show_add_form",
    False,
):

    st.markdown(
        """
        <div style="
            font-size:18px;
            font-weight:700;
            color:#172033;
            margin-top:10px;
            margin-bottom:12px;
        ">
            ➕ Add New Lead
        </div>
        """,
        unsafe_allow_html=True,
    )

    new_lead = render_add_lead_form()

    if new_lead is not None:

        try:

            add_lead(
                new_lead
            )

            st.session_state[
                "show_add_form"
            ] = False

            st.cache_data.clear()

            st.success(
                "Lead added successfully."
            )

            st.rerun()

        except ValueError as exc:

            st.warning(
                f"⚠️ {exc}"
            )

        except Exception as exc:

            st.error(
                f"Could not add lead: {exc}"
            )


# ============================================================
# FILTERS
# ============================================================

st.markdown("### Filters")


# ============================================================
# FIRST FILTER ROW
# ============================================================

f1, f2, f3, f4 = st.columns(
    [2.5, 1.4, 1.4, 1.4]
)


# ------------------------------------------------------------
# SEARCH
# ------------------------------------------------------------

with f1:

    search = st.text_input(
        "Search",
        placeholder="Search name, phone or email...",
        label_visibility="collapsed",
        key="lead_search",
    )


# ------------------------------------------------------------
# STATUS
# ------------------------------------------------------------

with f2:

    selected_status = st.selectbox(
        "Status",
        ["All Statuses"] + STATUSES,
        label_visibility="collapsed",
        key="filter_status",
    )


# ------------------------------------------------------------
# AGENT
# ------------------------------------------------------------

with f3:

    agents = ["All Agents"]

    if not df.empty:

        agents += sorted(
            [
                str(x).strip()
                for x in df["Agent"]
                .dropna()
                .unique()
                if str(x).strip()
            ]
        )

    selected_agent = st.selectbox(
        "Agent",
        agents,
        label_visibility="collapsed",
        key="filter_agent",
    )


# ------------------------------------------------------------
# SOURCE
# ------------------------------------------------------------

with f4:

    selected_source = st.selectbox(
        "Source",
        ["All Sources"] + SOURCES,
        label_visibility="collapsed",
        key="filter_source",
    )


# ============================================================
# DATE FILTER
# ============================================================

st.markdown(
    "<div class='date-filter-title'>📅 Lead Date Filter</div>",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# CONVERT LEAD DATE
# ------------------------------------------------------------

lead_date_series = pd.to_datetime(
    df["Date"].astype(str).str.strip(),
    dayfirst=True,
    errors="coerce",
)


valid_lead_dates = lead_date_series.dropna()


# ------------------------------------------------------------
# DATE FILTER ENABLE/DISABLE
# ------------------------------------------------------------

date_filter_col1, date_filter_col2, date_filter_col3 = (
    st.columns([1.2, 1.6, 1.6])
)


with date_filter_col1:

    filter_by_date = st.checkbox(
        "Filter by Lead Date",
        key="filter_by_date",
    )


# ------------------------------------------------------------
# DEFAULT DATE RANGE
# ------------------------------------------------------------

if not valid_lead_dates.empty:

    min_lead_date = (
        valid_lead_dates
        .min()
        .date()
    )

    max_lead_date = (
        valid_lead_dates
        .max()
        .date()
    )

else:

    min_lead_date = None
    max_lead_date = None


# ------------------------------------------------------------
# FROM DATE
# ------------------------------------------------------------

with date_filter_col2:

    if min_lead_date is not None:

        date_from = st.date_input(
            "From Date",
            value=min_lead_date,
            min_value=min_lead_date,
            max_value=max_lead_date,
            disabled=not filter_by_date,
            format="DD-MM-YYYY",
            key="filter_date_from",
        )

    else:

        date_from = None

        st.date_input(
            "From Date",
            value=None,
            disabled=True,
            key="filter_date_from_empty",
        )


# ------------------------------------------------------------
# TO DATE
# ------------------------------------------------------------

with date_filter_col3:

    if max_lead_date is not None:

        date_to = st.date_input(
            "To Date",
            value=max_lead_date,
            min_value=min_lead_date,
            max_value=max_lead_date,
            disabled=not filter_by_date,
            format="DD-MM-YYYY",
            key="filter_date_to",
        )

    else:

        date_to = None

        st.date_input(
            "To Date",
            value=None,
            disabled=True,
            key="filter_date_to_empty",
        )


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()


# ------------------------------------------------------------
# SEARCH
# ------------------------------------------------------------

if search.strip():

    search_value = search.strip().lower()

    search_mask = (
        filtered_df
        .astype(str)
        .apply(
            lambda col:
            col.str
            .lower()
            .str.contains(
                search_value,
                na=False,
                regex=False,
            )
        )
        .any(axis=1)
    )

    filtered_df = filtered_df[
        search_mask
    ]


# ------------------------------------------------------------
# STATUS
# ------------------------------------------------------------

if selected_status != "All Statuses":

    filtered_df = filtered_df[
        filtered_df["Status"]
        .astype(str)
        .str.strip()
        == selected_status
    ]


# ------------------------------------------------------------
# AGENT
# ------------------------------------------------------------

if selected_agent != "All Agents":

    filtered_df = filtered_df[
        filtered_df["Agent"]
        .astype(str)
        .str.strip()
        == selected_agent
    ]


# ------------------------------------------------------------
# SOURCE
# ------------------------------------------------------------

if selected_source != "All Sources":

    filtered_df = filtered_df[
        filtered_df["Source"]
        .astype(str)
        .str.strip()
        == selected_source
    ]


# ============================================================
# APPLY DATE FILTER
# ============================================================

if filter_by_date:

    # Convert current filtered rows to dates
    current_dates = pd.to_datetime(
        filtered_df["Date"].astype(str).str.strip(),
        dayfirst=True,
        errors="coerce",
    )


    # --------------------------------------------------------
    # INVALID RANGE
    # --------------------------------------------------------

    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):

        st.error(
            "⚠️ From Date cannot be later than To Date."
        )

        filtered_df = filtered_df.iloc[0:0]


    else:

        # ----------------------------------------------------
        # FROM DATE
        # ----------------------------------------------------

        if date_from is not None:

            filtered_df = filtered_df[
                current_dates.dt.date >= date_from
            ]


        # ----------------------------------------------------
        # TO DATE
        # ----------------------------------------------------

        if date_to is not None:

            current_dates = pd.to_datetime(
                filtered_df["Date"].astype(str).str.strip(),
                dayfirst=True,
                errors="coerce",
            )

            filtered_df = filtered_df[
                current_dates.dt.date <= date_to
            ]


# ============================================================
# FILTER SUMMARY
# ============================================================

if filter_by_date:

    if date_from is not None and date_to is not None:

        st.caption(
            f"📅 Showing leads from "
            f"{date_from.strftime('%d %b %Y')} "
            f"to "
            f"{date_to.strftime('%d %b %Y')}"
        )


# ============================================================
# DASHBOARD
# ============================================================

render_dashboard(
    filtered_df
)

st.divider()


# ============================================================
# TABS
# ============================================================

tab_board, tab_analytics = st.tabs(
    [
        "📋 Conversion Board",
        "📊 Agent Performance & Insights",
    ]
)


# ============================================================
# CONVERSION BOARD
# ============================================================

with tab_board:

    result = render_board(
        filtered_df
    )


    if result:

        action = result.get(
            "action"
        )

        row_number = result.get(
            "row_number"
        )


        # ====================================================
        # EDIT
        # ====================================================

        if action == "edit":

            st.session_state[
                "editing_row"
            ] = int(row_number)

            st.rerun()


        # ====================================================
        # DELETE
        # ====================================================

        elif action == "delete":

            st.session_state[
                "deleting_row"
            ] = int(row_number)

            st.rerun()


        # ====================================================
        # STATUS UPDATE
        # ====================================================

        elif action == "status":

            try:

                new_status = result.get(
                    "new_status",
                    "",
                )

                update_data = {
                    "Status": new_status
                }


                # ------------------------------------------------
                # FOLLOW UP
                # ------------------------------------------------

                if new_status == "Follow up":

                    update_data[
                        "Follow Up Count"
                    ] = result.get(
                        "follow_up_count",
                        "Follow up 1",
                    )


                # ------------------------------------------------
                # OTHER STATUS
                # ------------------------------------------------

                else:

                    update_data[
                        "Follow Up Count"
                    ] = ""


                update_lead(
                    int(row_number),
                    update_data,
                )

                st.cache_data.clear()

                st.success(
                    "Lead updated successfully."
                )

                st.rerun()

            except Exception as exc:

                st.error(
                    f"Could not update lead: {exc}"
                )


# ============================================================
# DELETE POPUP
# ============================================================

deleting_row = st.session_state.get(
    "deleting_row"
)


if deleting_row is not None:

    # --------------------------------------------------------
    # ALWAYS USE FULL DATAFRAME
    # --------------------------------------------------------
    # Do NOT use filtered_df here.
    # A lead may have been deleted while filters are active.

    delete_record = df[
        df["_sheet_row"].astype(int)
        == int(deleting_row)
    ]


    # --------------------------------------------------------
    # LEAD NOT FOUND
    # --------------------------------------------------------

    if delete_record.empty:

        st.session_state[
            "deleting_row"
        ] = None

        st.error(
            "The selected lead could not be found in Google Sheets."
        )


    # --------------------------------------------------------
    # LEAD FOUND
    # --------------------------------------------------------

    else:

        record = delete_record.iloc[0]

        lead_name = str(
            record.get(
                "Name",
                "",
            )
            or "Unnamed Lead"
        )

        delete_lead_dialog(
            int(deleting_row),
            lead_name,
        )


# ============================================================
# ANALYTICS
# ============================================================

with tab_analytics:

    render_analytics(
        filtered_df
    )


# ============================================================
# EDIT LEAD DIALOG
# ============================================================

@st.dialog("✏️ Edit Lead", width="large")
def edit_lead_dialog(record, row_number):

    updated_lead = render_edit_lead_form(record)

    if updated_lead is not None:

        try:

            update_lead(
                int(row_number),
                updated_lead,
            )

            st.session_state["editing_row"] = None
            st.cache_data.clear()

            st.success("Lead updated successfully.")
            st.rerun()

        except Exception as exc:

            st.error(
                f"Could not update lead: {exc}"
            )

    if st.button(
        "Cancel",
        use_container_width=True,
        key=f"cancel_edit_dialog_{row_number}",
    ):

        st.session_state["editing_row"] = None
        st.rerun()


# ============================================================
# OPEN EDIT DIALOG
# ============================================================

editing_row = st.session_state.get(
    "editing_row"
)

if editing_row is not None:

    edit_record = df[
        df["_sheet_row"].astype(int)
        == int(editing_row)
    ]

    if not edit_record.empty:

        edit_lead_dialog(
            edit_record.iloc[0].to_dict(),
            int(editing_row),
        )

    else:

        st.session_state["editing_row"] = None


# ============================================================
# FOOTER
# ============================================================

st.caption(
    f"Showing {len(filtered_df)} of "
    f"{len(df)} leads • "
    "Google Sheets is the shared source of truth."
)
