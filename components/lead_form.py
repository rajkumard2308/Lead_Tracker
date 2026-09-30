from datetime import date, datetime, timedelta

import streamlit as st

from config import (
    STATUSES,
    SOURCES,
    AGENTS,
    FOLLOW_UP_OPTIONS,
)


# =========================================================
# DATE PARSING
# =========================================================

def _parse_date(value):
    """
    Convert a value to datetime.date.

    The application standard is DD-MM-YYYY.
    Ambiguous slash dates are interpreted as DD/MM/YYYY.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text:
        return None

    if text.lower() in {
        "nan",
        "nat",
        "none",
        "null",
    }:
        return None

    # Google/Excel serial date.
    try:
        numeric = float(text)

        if text.replace(".", "", 1).isdigit() and 20000 <= numeric <= 70000:
            return (
                datetime(1899, 12, 30)
                + timedelta(days=numeric)
            ).date()
    except (ValueError, OverflowError):
        pass

    formats = (
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%y",
        "%d/%m/%y",
        "%d.%m.%y",
        "%d %B %Y",
        "%d %b %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                text,
                fmt,
            ).date()
        except ValueError:
            continue

    return None


# =========================================================
# AMOUNT
# =========================================================

def _parse_amount(value):
    if value in (None, "", "nan", "None", "null"):
        return 0.0

    try:
        text = (
            str(value)
            .replace(",", "")
            .replace("₹", "")
            .strip()
        )

        return float(text) if text else 0.0

    except (ValueError, TypeError):
        return 0.0


# =========================================================
# ADD FORM CALLBACK
# =========================================================

def _update_add_checkout():
    check_in = st.session_state.get(
        "add_check_in_date"
    )

    if check_in:
        st.session_state[
            "add_check_out_date"
        ] = check_in + timedelta(days=1)


# =========================================================
# EDIT FORM CALLBACK
# =========================================================

def _update_edit_checkout(row_number):
    check_in = st.session_state.get(
        f"edit_check_in_date_{row_number}"
    )

    if check_in:
        st.session_state[
            f"edit_check_out_date_{row_number}"
        ] = check_in + timedelta(days=1)


# =========================================================
# CLEAR EDIT WIDGET STATE
# =========================================================

def clear_edit_form_state(row_number):
    """
    Remove all widget state for one edit session.

    This is important because Streamlit keeps widget values
    in session_state after the dialog is closed.
    """

    row_number = int(row_number)

    prefixes = [
        "edit_inquiry_date",
        "edit_check_in_date",
        "edit_check_out_date",
        "edit_name",
        "edit_phone",
        "edit_email",
        "edit_agent",
        "edit_status",
        "edit_source",
        "edit_booking_date",
        "edit_last_follow",
        "edit_followup_count",
        "edit_remarks",
        "edit_total_amount",
    ]

    for prefix in prefixes:
        st.session_state.pop(
            f"{prefix}_{row_number}",
            None,
        )

    st.session_state.pop(
        f"edit_initialized_{row_number}",
        None,
    )


# =========================================================
# ADD LEAD FORM
# =========================================================

def render_add_lead_form():

    today = date.today()

    st.session_state.setdefault(
        "add_inquiry_date",
        today,
    )

    st.session_state.setdefault(
        "add_check_in_date",
        None,
    )

    st.session_state.setdefault(
        "add_check_out_date",
        None,
    )

    # These two date fields must start empty for every new lead.
    # st.date_input otherwise defaults to today's date.
    st.session_state.setdefault(
        "add_booking_date",
        None,
    )

    st.session_state.setdefault(
        "add_last_follow",
        None,
    )

    st.session_state.setdefault(
        "add_followup_count",
        "",
    )

    a, b = st.columns(2)

    with a:
        inquiry_date = st.date_input(
            "Inquiry Date *",
            key="add_inquiry_date",
            format="DD-MM-YYYY",
        )

    with b:
        name = st.text_input(
            "Client Name",
            placeholder="e.g. John Doe",
            key="add_client_name",
        )

    a, b = st.columns(2)

    with a:
        phone = st.text_input(
            "Phone Number *",
            placeholder="e.g. 98111 22233",
            key="add_phone",
        )

    with b:
        email = st.text_input(
            "Email",
            placeholder="client@example.com",
            key="add_email",
        )

    a, b = st.columns(2)

    with a:
        check_in = st.date_input(
            "Check In Date",
            key="add_check_in_date",
            format="DD-MM-YYYY",
            on_change=_update_add_checkout,
        )

    with b:
        check_out_min = (
            check_in + timedelta(days=1)
            if check_in
            else None
        )

        current_checkout = st.session_state.get(
            "add_check_out_date"
        )

        if (
            check_out_min
            and (
                current_checkout is None
                or current_checkout <= check_in
            )
        ):
            st.session_state[
                "add_check_out_date"
            ] = check_out_min

        check_out = st.date_input(
            "Check Out Date",
            key="add_check_out_date",
            min_value=check_out_min,
            format="DD-MM-YYYY",
        )

    a, b, c = st.columns(3)

    with a:
        agent = st.selectbox(
            "Assigned Agent",
            AGENTS,
            key="add_agent",
        )

    with b:
        status = st.selectbox(
            "Pipeline Status",
            STATUSES,
            key="add_status",
        )

    with c:
        source = st.selectbox(
            "Lead Source",
            SOURCES,
            key="add_source",
        )

    booking_date = st.date_input(
        "Booking Confirmation Date",
        value=None,
        key="add_booking_date",
        format="DD-MM-YYYY",
    )

    a, b = st.columns(2)

    with a:
        last_follow = st.date_input(
            "Last Follow-up Done On",
            value=None,
            key="add_last_follow",
            format="DD-MM-YYYY",
        )

    # Follow-up Count is relevant only for Follow up status.
    if status == "Follow up":
        count = st.selectbox(
            "Follow-up Count",
            [""] + FOLLOW_UP_OPTIONS,
            index=1 if not st.session_state.get("add_followup_count") else 0,
            key="add_followup_count",
        )
    else:
        # Clear any previous Follow-up Count when status changes
        # to a non-follow-up status.
        st.session_state["add_followup_count"] = ""
        count = ""

    remarks = st.text_area(
        "Remarks",
        placeholder="Any client notes, preference or comments...",
        key="add_remarks",
    )

    total_amount = 0.0

    if status == "Converted":
        total_amount = st.number_input(
            "Total Amount (₹)",
            min_value=0.0,
            value=0.0,
            step=100.0,
            format="%.2f",
            key="add_total_amount",
        )

    add_col, cancel_col = st.columns(2)

    with add_col:
        submitted = st.button(
            "➕ Add Lead",
            type="primary",
            use_container_width=True,
            key="submit_add_lead",
        )

    with cancel_col:
        cancelled = st.button(
            "✖ Cancel",
            use_container_width=True,
            key="cancel_add_lead",
        )

    if cancelled:
        return {"__action__": "cancel"}

    if not submitted:
        return None

    if not phone.strip():
        st.error("Phone number is required.")
        return None

    if (
        check_in
        and check_out
        and check_out <= check_in
    ):
        st.error(
            "Check-out date must be after the check-in date."
        )
        return None

    if status == "Follow up" and last_follow and not count:
        st.error(
            "Please select the follow-up count."
        )
        return None

    return {
        "Date": inquiry_date,
        "Name": name.strip(),
        "Number": phone.strip(),
        "Email": email.strip(),
        "Check In Date": check_in,
        "Check Out Date": check_out,
        "Booking Confirmation Date": booking_date,
        "Agent": agent,
        "Status": status,
        "Source": source,
        "Last Follow Up": last_follow,
        "Follow Up Count": count,
        "Remarks": remarks.strip(),
        "Total Amount": (
            total_amount
            if status == "Converted"
            else ""
        ),
    }


# =========================================================
# EDIT LEAD FORM
# =========================================================

def render_edit_lead_form(record):

    row_number = int(
        record.get("_sheet_row")
    )

    # -----------------------------------------------------
    # Widget keys
    # -----------------------------------------------------

    inquiry_key = (
        f"edit_inquiry_date_{row_number}"
    )

    check_in_key = (
        f"edit_check_in_date_{row_number}"
    )

    check_out_key = (
        f"edit_check_out_date_{row_number}"
    )

    name_key = f"edit_name_{row_number}"
    phone_key = f"edit_phone_{row_number}"
    email_key = f"edit_email_{row_number}"

    agent_key = f"edit_agent_{row_number}"
    status_key = f"edit_status_{row_number}"
    source_key = f"edit_source_{row_number}"

    booking_key = (
        f"edit_booking_date_{row_number}"
    )

    last_follow_key = (
        f"edit_last_follow_{row_number}"
    )

    follow_count_key = (
        f"edit_followup_count_{row_number}"
    )

    remarks_key = (
        f"edit_remarks_{row_number}"
    )

    amount_key = (
        f"edit_total_amount_{row_number}"
    )

    initialized_key = (
        f"edit_initialized_{row_number}"
    )

    # -----------------------------------------------------
    # Initialize widget state exactly once per edit opening
    # -----------------------------------------------------

    if not st.session_state.get(
        initialized_key,
        False,
    ):

        st.session_state[
            inquiry_key
        ] = _parse_date(
            record.get("Date")
        )

        st.session_state[
            check_in_key
        ] = _parse_date(
            record.get("Check In Date")
        )

        st.session_state[
            check_out_key
        ] = _parse_date(
            record.get("Check Out Date")
        )

        st.session_state[
            name_key
        ] = str(
            record.get("Name", "")
            or ""
        )

        st.session_state[
            phone_key
        ] = str(
            record.get("Number", "")
            or ""
        )

        st.session_state[
            email_key
        ] = str(
            record.get("Email", "")
            or ""
        )

        current_agent = str(
            record.get("Agent", "")
            or ""
        )

        st.session_state[
            agent_key
        ] = (
            current_agent
            if current_agent in AGENTS
            else AGENTS[0]
        )

        current_status = str(
            record.get("Status", "")
            or ""
        )

        st.session_state[
            status_key
        ] = (
            current_status
            if current_status in STATUSES
            else STATUSES[0]
        )

        current_source = str(
            record.get("Source", "")
            or ""
        )

        st.session_state[
            source_key
        ] = (
            current_source
            if current_source in SOURCES
            else SOURCES[0]
        )

        st.session_state[
            booking_key
        ] = _parse_date(
            record.get(
                "Booking Confirmation Date"
            )
        )

        st.session_state[
            last_follow_key
        ] = _parse_date(
            record.get("Last Follow Up")
        )

        current_count = str(
            record.get(
                "Follow Up Count",
                "",
            )
            or ""
        )

        st.session_state[
            follow_count_key
        ] = (
            current_count
            if current_count in FOLLOW_UP_OPTIONS
            else ""
        )

        st.session_state[
            remarks_key
        ] = str(
            record.get(
                "Remarks",
                "",
            )
            or ""
        )

        st.session_state[
            amount_key
        ] = _parse_amount(
            record.get(
                "Total Amount"
            )
        )

        st.session_state[
            initialized_key
        ] = True

    # -----------------------------------------------------
    # Basic details
    # -----------------------------------------------------

    a, b = st.columns(2)

    with a:
        inquiry_date = st.date_input(
            "Inquiry Date",
            key=inquiry_key,
            format="DD-MM-YYYY",
        )

    with b:
        name = st.text_input(
            "Client Name",
            key=name_key,
        )

    a, b = st.columns(2)

    with a:
        phone = st.text_input(
            "Phone Number",
            key=phone_key,
        )

    with b:
        email = st.text_input(
            "Email",
            key=email_key,
        )

    # -----------------------------------------------------
    # Stay dates
    # -----------------------------------------------------

    a, b = st.columns(2)

    with a:
        check_in = st.date_input(
            "Check In Date",
            key=check_in_key,
            format="DD-MM-YYYY",
            on_change=_update_edit_checkout,
            args=(row_number,),
        )

    with b:
        check_out_min = (
            check_in + timedelta(days=1)
            if check_in
            else None
        )

        current_checkout = st.session_state.get(
            check_out_key
        )

        # Automatic checkout only when there is no valid
        # existing/manual checkout.
        if (
            check_out_min
            and (
                current_checkout is None
                or current_checkout < check_out_min
            )
        ):
            st.session_state[
                check_out_key
            ] = check_out_min

        check_out = st.date_input(
            "Check Out Date",
            key=check_out_key,
            min_value=check_out_min,
            format="DD-MM-YYYY",
        )

    # -----------------------------------------------------
    # Agent / status / source
    # -----------------------------------------------------

    a, b, c = st.columns(3)

    with a:
        agent = st.selectbox(
            "Assigned Agent",
            AGENTS,
            key=agent_key,
        )

    with b:
        status = st.selectbox(
            "Pipeline Status",
            STATUSES,
            key=status_key,
        )

    with c:
        source = st.selectbox(
            "Lead Source",
            SOURCES,
            key=source_key,
        )

    # -----------------------------------------------------
    # Booking date
    # -----------------------------------------------------

    booking_date = st.date_input(
        "Booking Confirmation Date",
        key=booking_key,
        format="DD-MM-YYYY",
    )

    # -----------------------------------------------------
    # Follow-up
    # -----------------------------------------------------

    a, b = st.columns(2)

    with a:
        last_follow = st.date_input(
            "Last Follow-up Done On",
            key=last_follow_key,
            format="DD-MM-YYYY",
        )

    if status == "Follow up":
        with b:
            count = st.selectbox(
                "Follow-up Count",
                [""] + FOLLOW_UP_OPTIONS,
                key=follow_count_key,
            )
    else:
        st.session_state[follow_count_key] = ""
        count = ""

    remarks = st.text_area(
        "Remarks",
        key=remarks_key,
    )

    # -----------------------------------------------------
    # Total amount
    # -----------------------------------------------------

    total_amount = 0.0

    if status == "Converted":
        total_amount = st.number_input(
            "Total Amount (₹)",
            min_value=0.0,
            step=100.0,
            format="%.2f",
            key=amount_key,
        )

    # -----------------------------------------------------
    # SAVE
    # -----------------------------------------------------

    submitted = st.button(
        "💾 Save Changes",
        type="primary",
        use_container_width=True,
        key=f"save_edit_{row_number}",
    )

    if not submitted:
        return None

    if not phone.strip():
        st.error("Phone number is required.")
        return None

    if (
        check_in
        and check_out
        and check_out <= check_in
    ):
        st.error(
            "Check-out date must be after the check-in date."
        )
        return None

    if status == "Follow up" and last_follow and not count:
        st.error(
            "Please select the follow-up count."
        )
        return None

    return {
        "Date": inquiry_date,
        "Name": name.strip(),
        "Number": phone.strip(),
        "Email": email.strip(),
        "Check In Date": check_in,
        "Check Out Date": check_out,
        "Booking Confirmation Date": booking_date,
        "Agent": agent,
        "Status": status,
        "Source": source,
        "Last Follow Up": last_follow,
        "Follow Up Count": count,
        "Remarks": remarks.strip(),
        "Total Amount": (
            total_amount
            if status == "Converted"
            else ""
        ),
    }
