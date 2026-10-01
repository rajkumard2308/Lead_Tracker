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
    add_leads_bulk,
    _get_sheet_values,
    _get_sheet_headers,
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
    clear_edit_form_state,
)

from components.analytics import (
    render_analytics,
)

from components.bulk_upload import render_bulk_upload


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

if "add_form_open" not in st.session_state:
    st.session_state["add_form_open"] = False

if "editing_row" not in st.session_state:
    st.session_state["editing_row"] = None

if "edit_dialog_open" not in st.session_state:
    st.session_state["edit_dialog_open"] = False

if "deleting_row" not in st.session_state:
    st.session_state["deleting_row"] = None

if "filter_by_date" not in st.session_state:
    st.session_state["filter_by_date"] = False

if "edit_success_message" not in st.session_state:
    st.session_state["edit_success_message"] = None

if "show_bulk_form" not in st.session_state:
    st.session_state["show_bulk_form"] = False


# ============================================================
# ADD FORM STATE CLEANUP
# ============================================================

ADD_FORM_KEYS = [
    "add_inquiry_date",
    "add_client_name",
    "add_phone",
    "add_email",
    "add_check_in_date",
    "add_check_out_date",
    "add_agent",
    "add_status",
    "add_source",
    "add_booking_date",
    "add_last_follow",
    "add_followup_count",
    "add_remarks",
    "add_total_amount",
]


def clear_add_form_state():
    for key in ADD_FORM_KEYS:
        st.session_state.pop(key, None)


def close_add_form():
    """Close Add Lead and clear all Add Lead widget state."""
    clear_add_form_state()
    st.session_state["show_add_form"] = False
    st.session_state["add_form_open"] = False


def close_edit_form():
    """Close Edit Lead and clear all Edit Lead widget state."""
    editing_row = st.session_state.get("editing_row")
    if editing_row is not None:
        try:
            clear_edit_form_state(int(editing_row))
        except Exception:
            pass

    st.session_state["editing_row"] = None
    st.session_state["edit_dialog_open"] = False


def close_bulk_form():
    st.session_state["show_bulk_form"] = False
    st.session_state.pop("bulk_lead_file", None)


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
       BUTTONS
    ======================================================== */

    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 12px;
    }

    /* ========================================================
       HEADER ACTION BUTTONS
    ======================================================== */

    .header-action {
        width: 100%;
        padding-top: 4px;
    }

    .header-action button {
        width: 100% !important;
        min-width: 0 !important;
        max-width: 100% !important;
        height: 42px !important;
        padding: 0 8px !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
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

        .header-action button {
            font-size: 12px !important;
            padding-left: 6px !important;
            padding-right: 6px !important;
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
# EDIT DIALOG
# ============================================================

@st.dialog("✏️ Edit Lead")
def edit_lead_dialog(row_number, record):

    updated_lead = render_edit_lead_form(record)

    if updated_lead is not None:

        try:

            update_lead(
                int(row_number),
                updated_lead,
            )

            close_edit_form()

            st.session_state[
                "edit_success_message"
            ] = "✅ Lead updated successfully."

            st.rerun()

        except Exception as exc:

            st.error(
                f"Could not update lead: {exc}"
            )

    if st.button(
        "Cancel",
        use_container_width=True,
        key=f"cancel_edit_{row_number}",
    ):

        close_edit_form()
        st.rerun()


# ============================================================
# HEADER
# ============================================================

# Three top-level columns — no nested columns.
# This prevents the Add Lead / Bulk Add buttons from being squeezed or clipped.
header_left, add_col, bulk_col = st.columns(
    [5.8, 1.45, 1.45],
    gap="medium",
    vertical_alignment="top",
)

with header_left:
    st.markdown(
        """
        <div class="main-title">📈 2026 Lead Conversion Board</div>
        <div class="sub-title">Pipeline Tracking, Conversion Velocity & Follow-Up Management</div>
        """,
        unsafe_allow_html=True,
    )

with add_col:
    st.markdown('<div class="header-action">', unsafe_allow_html=True)

    if st.button(
        "➕ Add Lead",
        type="primary",
        use_container_width=True,
        key="header_add_lead",
    ):
        close_edit_form()
        close_bulk_form()
        st.session_state["deleting_row"] = None
        clear_add_form_state()
        st.session_state["show_add_form"] = True
        st.session_state["add_form_open"] = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

with bulk_col:
    st.markdown('<div class="header-action">', unsafe_allow_html=True)

    if st.button(
        "📥 Bulk Add",
        use_container_width=True,
        key="header_bulk_add",
    ):
        close_edit_form()
        close_add_form()
        st.session_state["deleting_row"] = None
        st.session_state["show_bulk_form"] = True
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# EDIT SUCCESS MESSAGE
# ============================================================

if st.session_state.get("edit_success_message"):

    st.success(
        st.session_state["edit_success_message"]
    )

    st.session_state["edit_success_message"] = None


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
    "_sheet_row",
]

for column in required_columns:

    if column not in df.columns:
        df[column] = ""


# ============================================================
# DATA REFRESH
# ============================================================

refresh_col1, refresh_col2 = st.columns([8, 1])
with refresh_col2:
    if st.button("🔄 Refresh", use_container_width=True, key="refresh_data"):
        get_leads.clear()
        _get_sheet_values.clear()
        _get_sheet_headers.clear()
        st.rerun()


# ============================================================
# BULK ADD LEADS
# ============================================================

if st.session_state.get("show_bulk_form", False):
    st.markdown("### 📥 Bulk Add Leads")
    bulk_result = render_bulk_upload(df)

    if bulk_result is not None:
        if bulk_result.get("__action__") == "cancel":
            close_bulk_form()
            st.rerun()

        if bulk_result.get("__action__") == "add_bulk":
            try:
                count = add_leads_bulk(bulk_result["leads"])
                close_bulk_form()
                st.success(f"✅ {count} leads added successfully.")
                st.rerun()
            except ValueError as exc:
                st.warning(f"⚠️ {exc}")
            except Exception as exc:
                st.error(f"Could not add bulk leads: {exc}")


# ============================================================
# ADD LEAD FORM
# ============================================================

if (
    st.session_state.get("show_add_form", False)
    and st.session_state.get("add_form_open", False)
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

        # The Add Lead form can request cancellation without
        # sending the cancel action to Google Sheets.
        if new_lead.get("__action__") == "cancel":
            close_add_form()
            st.rerun()

        try:

            add_lead(
                new_lead
            )

            close_add_form()

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
    df["Date"],
    format="%d-%m-%Y",
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
# STAY DATE FILTER
# ============================================================

st.markdown(
    "<div class='date-filter-title'>🏨 Stay Date Filter</div>",
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# CONVERT CHECK-IN / CHECK-OUT DATES
# ------------------------------------------------------------

check_in_series = pd.to_datetime(
    df["Check In Date"].astype(str).str.strip(),
    format="%d-%m-%Y",
    errors="coerce",
)

check_out_series = pd.to_datetime(
    df["Check Out Date"].astype(str).str.strip(),
    format="%d-%m-%Y",
    errors="coerce",
)


valid_check_in_dates = check_in_series.dropna()


# ------------------------------------------------------------
# STAY FILTER COLUMNS
# ------------------------------------------------------------

stay_col1, stay_col2, stay_col3 = st.columns(
    [1.2, 1.6, 1.6]
)


# ------------------------------------------------------------
# ENABLE STAY DATE FILTER
# ------------------------------------------------------------

with stay_col1:

    filter_by_stay_date = st.checkbox(
        "Filter by Stay Date",
        key="filter_by_stay_date",
    )


# ------------------------------------------------------------
# CHECK-IN DATE
# ------------------------------------------------------------

with stay_col2:

    if not valid_check_in_dates.empty:

        min_check_in_date = (
            valid_check_in_dates
            .min()
            .date()
        )

        max_check_in_date = (
            valid_check_in_dates
            .max()
            .date()
        )

        check_in_filter = st.date_input(
            "Check-in Date *",
            value=min_check_in_date,
            min_value=min_check_in_date,
            max_value=max_check_in_date,
            disabled=not filter_by_stay_date,
            format="DD-MM-YYYY",
            key="filter_check_in_date",
        )

    else:

        check_in_filter = None

        st.date_input(
            "Check-in Date *",
            value=None,
            disabled=True,
            format="DD-MM-YYYY",
            key="filter_check_in_date_empty",
        )


# ------------------------------------------------------------
# CHECK-OUT DATE - OPTIONAL
# ------------------------------------------------------------

with stay_col3:

    check_out_filter = st.date_input(
        "Check-out Date (Optional)",
        value=None,
        min_value=(
            check_in_filter
            if filter_by_stay_date
            and check_in_filter is not None
            else None
        ),
        disabled=not filter_by_stay_date,
        format="DD-MM-YYYY",
        key="filter_check_out_date",
    )

# ============================================================
# PRECOMPUTE FILTER SERIES
# ============================================================

# Normalize common filter columns once per rerun.
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


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df.copy()


# ------------------------------------------------------------
# SEARCH
# ------------------------------------------------------------

if search.strip():

    search_value = search.strip().lower()

    # Search only the fields users actually search.
    # This avoids converting every column in the DataFrame to strings
    # on every Streamlit rerun and is much faster on Streamlit Cloud.
    search_mask = pd.Series(False, index=filtered_df.index)

    for column in ("Name", "Number", "Email"):

        if column in filtered_df.columns:
            search_mask |= (
                filtered_df[column]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    na=False,
                    regex=False,
                )
            )

    filtered_df = filtered_df.loc[search_mask]


# ------------------------------------------------------------
# STATUS
# ------------------------------------------------------------

if selected_status != "All Statuses":

    filtered_df = filtered_df.loc[
        status_series.loc[filtered_df.index]
        == selected_status
    ]


# ------------------------------------------------------------
# AGENT
# ------------------------------------------------------------

if selected_agent != "All Agents":

    filtered_df = filtered_df.loc[
        agent_series.loc[filtered_df.index]
        == selected_agent
    ]


# ------------------------------------------------------------
# SOURCE
# ------------------------------------------------------------

if selected_source != "All Sources":

    filtered_df = filtered_df.loc[
        source_series.loc[filtered_df.index]
        == selected_source
    ]


# ============================================================
# APPLY DATE FILTER
# ============================================================

if filter_by_date:

    # Reuse the Lead Date series parsed above.
    current_dates = lead_date_series.loc[
        filtered_df.index
    ]


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

            mask_from = (
                current_dates.dt.date >= date_from
            )

            filtered_df = filtered_df.loc[mask_from]

            current_dates = current_dates.loc[
                filtered_df.index
            ]


        # ----------------------------------------------------
        # TO DATE
        # ----------------------------------------------------

        if date_to is not None:

            mask_to = (
                current_dates.dt.date <= date_to
            )

            filtered_df = filtered_df.loc[mask_to]

# ============================================================
# APPLY STAY DATE FILTER
# ============================================================

if filter_by_stay_date:

    # --------------------------------------------------------
    # CHECK-IN DATE IS MANDATORY
    # --------------------------------------------------------

    if check_in_filter is None:

        st.error(
            "⚠️ Please select a Check-in Date."
        )

        filtered_df = filtered_df.iloc[0:0]

    else:

        current_check_in_dates = check_in_series.loc[
            filtered_df.index
        ]

        # ----------------------------------------------------
        # FILTER BY CHECK-IN DATE
        # ----------------------------------------------------

        check_in_mask = (
            current_check_in_dates.dt.date
            == check_in_filter
        )

        filtered_df = filtered_df.loc[
            check_in_mask
        ]

        # ----------------------------------------------------
        # FILTER BY CHECK-OUT DATE ONLY IF SELECTED
        # ----------------------------------------------------

        if check_out_filter is not None:

            current_check_out_dates = check_out_series.loc[
                filtered_df.index
            ]

            check_out_mask = (
                current_check_out_dates.dt.date
                == check_out_filter
            )

            filtered_df = filtered_df.loc[
                check_out_mask
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

    # Remember the last board status so changing a status
    # tab cannot reopen a stale Edit dialog.
    last_board_status = st.session_state.get(
        "_last_board_status"
    )

    result = render_board(
        filtered_df
    )

    current_board_status = st.session_state.get(
        "selected_status"
    )

    if (
        last_board_status is not None
        and current_board_status != last_board_status
        and st.session_state.get("edit_dialog_open", False)
    ):
        close_edit_form()

    st.session_state[
        "_last_board_status"
    ] = current_board_status

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

            row_number = int(row_number)

            # Close any other transient UI before opening Edit.
            close_add_form()
            st.session_state["deleting_row"] = None
            clear_edit_form_state(row_number)

            st.session_state[
                "editing_row"
            ] = row_number

            st.session_state[
                "edit_dialog_open"
            ] = True

            st.rerun()


        # ====================================================
        # DELETE
        # ====================================================

        elif action == "delete":

            close_add_form()
            close_edit_form()

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
# EDIT LEAD POPUP
# ============================================================

editing_row = st.session_state.get(
    "editing_row"
)

edit_dialog_open = st.session_state.get(
    "edit_dialog_open",
    False,
)


if (
    editing_row is not None
    and edit_dialog_open
):

    edit_record = df[
        df["_sheet_row"].astype(int)
        == int(editing_row)
    ]

    if edit_record.empty:

        close_edit_form()

        st.warning(
            "The selected lead could not be found in Google Sheets."
        )

    else:

        edit_lead_dialog(
            int(editing_row),
            edit_record.iloc[0].to_dict(),
        )


# ============================================================
# FOOTER
# ============================================================

st.caption(
    f"Showing {len(filtered_df)} of "
    f"{len(df)} leads • "
    "Google Sheets is the shared source of truth."
)
