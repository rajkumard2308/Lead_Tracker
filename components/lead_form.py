from datetime import date, datetime, timedelta
import streamlit as st
from config import STATUSES, SOURCES, AGENTS, FOLLOW_UP_OPTIONS


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in (
        "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%d %B %Y", "%d %b %Y", "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def _parse_amount(value):
    if value in (None, "", "nan", "None"):
        return 0.0
    try:
        text = str(value).replace(",", "").replace("₹", "").strip()
        return float(text) if text else 0.0
    except (ValueError, TypeError):
        return 0.0


def _update_add_checkout():
    check_in = st.session_state.get("add_check_in_date")
    if check_in:
        st.session_state["add_check_out_date"] = check_in + timedelta(days=1)


def _update_edit_checkout(row_number):
    check_in = st.session_state.get(f"edit_check_in_date_{row_number}")
    if check_in:
        st.session_state[f"edit_check_out_date_{row_number}"] = check_in + timedelta(days=1)


def render_add_lead_form():
    today = date.today()
    st.session_state.setdefault("add_inquiry_date", today)
    st.session_state.setdefault("add_check_in_date", None)
    st.session_state.setdefault("add_check_out_date", None)

    a, b = st.columns(2)
    with a:
        inquiry_date = st.date_input("Inquiry Date *", key="add_inquiry_date", format="DD-MM-YYYY")
    with b:
        name = st.text_input("Client Name", placeholder="e.g. John Doe", key="add_client_name")

    a, b = st.columns(2)
    with a:
        phone = st.text_input("Phone Number *", placeholder="e.g. 98111 22233", key="add_phone")
    with b:
        email = st.text_input("Email", placeholder="client@example.com", key="add_email")

    a, b = st.columns(2)
    with a:
        check_in = st.date_input(
            "Check In Date",
            value=st.session_state["add_check_in_date"],
            format="DD-MM-YYYY",
            key="add_check_in_date",
            on_change=_update_add_checkout,
        )
    with b:
        check_out_min = check_in + timedelta(days=1) if check_in else None
        current_checkout = st.session_state.get("add_check_out_date")
        if check_out_min and (current_checkout is None or current_checkout <= check_in):
            st.session_state["add_check_out_date"] = check_out_min
        check_out = st.date_input(
            "Check Out Date",
            value=st.session_state["add_check_out_date"],
            min_value=check_out_min,
            format="DD-MM-YYYY",
            key="add_check_out_date",
        )

    a, b, c = st.columns(3)
    with a:
        agent = st.selectbox("Assigned Agent", AGENTS, key="add_agent")
    with b:
        status = st.selectbox("Pipeline Status", STATUSES, key="add_status")
    with c:
        source = st.selectbox("Lead Source", SOURCES, key="add_source")

    booking_date = st.date_input("Booking Confirmation Date", value=None, format="DD-MM-YYYY", key="add_booking_date")

    a, b = st.columns(2)
    with a:
        last_follow = st.date_input("Last Follow-up Done On", value=None, format="DD-MM-YYYY", key="add_last_follow")
    with b:
        count = st.selectbox("Follow-up Count", [""] + FOLLOW_UP_OPTIONS, index=1, key="add_followup_count")

    remarks = st.text_area("Remarks", placeholder="Any client notes, preference or comments...", key="add_remarks")

    total_amount = 0.0
    if status == "Converted":
        total_amount = st.number_input(
            "Total Amount (₹)", min_value=0.0, value=0.0, step=100.0,
            format="%.2f", key="add_total_amount",
        )

    submitted = st.button("➕ Add Lead", type="primary", use_container_width=True, key="submit_add_lead")
    if submitted:
        if not phone.strip():
            st.error("Phone number is required.")
            return None
        if check_in and check_out and check_out <= check_in:
            st.error("Check-out date must be after the check-in date.")
            return None
        if last_follow and not count:
            st.error("Please select the follow-up count.")
            return None
        return {
            "Date": inquiry_date, "Name": name.strip(), "Number": phone.strip(), "Email": email.strip(),
            "Check In Date": check_in, "Check Out Date": check_out,
            "Booking Confirmation Date": booking_date, "Agent": agent, "Status": status, "Source": source,
            "Last Follow Up": last_follow, "Follow Up Count": count, "Remarks": remarks.strip(),
            "Total Amount": total_amount if status == "Converted" else "",
        }
    return None


def render_edit_lead_form(r):
    row_number = int(r.get("_sheet_row"))
    cur_agent = str(r.get("Agent", "") or "")
    cur_status = str(r.get("Status", "") or "")
    cur_source = str(r.get("Source", "") or "")
    cur_count = str(r.get("Follow Up Count", "") or "")

    inquiry_key = f"edit_inquiry_date_{row_number}"
    check_in_key = f"edit_check_in_date_{row_number}"
    check_out_key = f"edit_check_out_date_{row_number}"

    st.session_state.setdefault(inquiry_key, _parse_date(r.get("Date")))
    st.session_state.setdefault(check_in_key, _parse_date(r.get("Check In Date")))
    st.session_state.setdefault(check_out_key, _parse_date(r.get("Check Out Date")))

    a, b = st.columns(2)
    with a:
        inquiry_date = st.date_input("Inquiry Date", key=inquiry_key, format="DD-MM-YYYY")
    with b:
        name = st.text_input("Client Name", value=str(r.get("Name", "") or ""), key=f"edit_name_{row_number}")

    a, b = st.columns(2)
    with a:
        phone = st.text_input("Phone Number", value=str(r.get("Number", "") or ""), key=f"edit_phone_{row_number}")
    with b:
        email = st.text_input("Email", value=str(r.get("Email", "") or ""), key=f"edit_email_{row_number}")

    a, b = st.columns(2)
    with a:
        check_in = st.date_input(
            "Check In Date", key=check_in_key, format="DD-MM-YYYY",
            on_change=lambda: _update_edit_checkout(row_number),
        )
    with b:
        check_out_min = check_in + timedelta(days=1) if check_in else None
        current_checkout = st.session_state.get(check_out_key)
        if check_out_min and (current_checkout is None or current_checkout <= check_in):
            st.session_state[check_out_key] = check_out_min
        check_out = st.date_input(
            "Check Out Date", key=check_out_key, min_value=check_out_min, format="DD-MM-YYYY",
        )

    a, b, c = st.columns(3)
    with a:
        agent = st.selectbox("Assigned Agent", AGENTS, index=AGENTS.index(cur_agent) if cur_agent in AGENTS else 0, key=f"edit_agent_{row_number}")
    with b:
        status = st.selectbox("Pipeline Status", STATUSES, index=STATUSES.index(cur_status) if cur_status in STATUSES else 0, key=f"edit_status_{row_number}")
    with c:
        source = st.selectbox("Lead Source", SOURCES, index=SOURCES.index(cur_source) if cur_source in SOURCES else 0, key=f"edit_source_{row_number}")

    booking_date = st.date_input(
        "Booking Confirmation Date", value=_parse_date(r.get("Booking Confirmation Date")),
        format="DD-MM-YYYY", key=f"edit_booking_date_{row_number}",
    )

    a, b = st.columns(2)
    with a:
        last_follow = st.date_input(
            "Last Follow-up Done On", value=_parse_date(r.get("Last Follow Up")),
            format="DD-MM-YYYY", key=f"edit_last_follow_{row_number}",
        )
    with b:
        idx = FOLLOW_UP_OPTIONS.index(cur_count) + 1 if cur_count in FOLLOW_UP_OPTIONS else 0
        count = st.selectbox("Follow-up Count", [""] + FOLLOW_UP_OPTIONS, index=idx, key=f"edit_followup_count_{row_number}")

    remarks = st.text_area("Remarks", value=str(r.get("Remarks", "") or ""), key=f"edit_remarks_{row_number}")

    total_amount = 0.0
    if status == "Converted":
        total_amount = st.number_input(
            "Total Amount (₹)", min_value=0.0, value=_parse_amount(r.get("Total Amount")),
            step=100.0, format="%.2f", key=f"edit_total_amount_{row_number}",
        )

    submitted = st.button("💾 Save Changes", type="primary", use_container_width=True, key=f"save_edit_{row_number}")
    if submitted:
        if not phone.strip():
            st.error("Phone number is required.")
            return None
        if check_in and check_out and check_out <= check_in:
            st.error("Check-out date must be after the check-in date.")
            return None
        if last_follow and not count:
            st.error("Please select the follow-up count.")
            return None
        return {
            "Date": inquiry_date, "Name": name.strip(), "Number": phone.strip(), "Email": email.strip(),
            "Check In Date": check_in, "Check Out Date": check_out,
            "Booking Confirmation Date": booking_date, "Agent": agent, "Status": status, "Source": source,
            "Last Follow Up": last_follow, "Follow Up Count": count, "Remarks": remarks.strip(),
            "Total Amount": total_amount if status == "Converted" else "",
        }
    return None
