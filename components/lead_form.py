from datetime import date, datetime, timedelta

import streamlit as st

from config import (
    STATUSES,
    SOURCES,
    AGENTS,
    FOLLOW_UP_OPTIONS,
)


# ============================================================
# DATE PARSER
# ============================================================

def _parse_date(value):
    """
    Convert different date formats into a Python date object.
    """

    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    for fmt in (
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(
                str(value).strip(),
                fmt,
            ).date()

        except ValueError:
            pass

    return None


# ============================================================
# ADD LEAD - CHECKOUT CALLBACK
# ============================================================

def _update_add_checkout():
    """
    Whenever the Add Lead check-in date changes,
    automatically set checkout to the next day.
    """

    check_in = st.session_state.get(
        "add_check_in_date"
    )

    if check_in:

        st.session_state[
            "add_check_out_date"
        ] = check_in + timedelta(days=1)


# ============================================================
# EDIT LEAD - CHECKOUT CALLBACK
# ============================================================

def _update_edit_checkout(row_number):
    """
    Whenever the Edit Lead check-in date changes,
    automatically set checkout to the next day.
    """

    check_in_key = (
        f"edit_check_in_date_{row_number}"
    )

    check_out_key = (
        f"edit_check_out_date_{row_number}"
    )

    check_in = st.session_state.get(
        check_in_key
    )

    if check_in:

        st.session_state[
            check_out_key
        ] = check_in + timedelta(days=1)


# ============================================================
# ADD LEAD FORM
# ============================================================

def render_add_lead_form():

    # --------------------------------------------------------
    # SESSION STATE INITIALIZATION
    # --------------------------------------------------------

    today = date.today()

    if "add_inquiry_date" not in st.session_state:

        st.session_state[
            "add_inquiry_date"
        ] = today

    if "add_check_in_date" not in st.session_state:

        st.session_state[
            "add_check_in_date"
        ] = None

    if "add_check_out_date" not in st.session_state:

        st.session_state[
            "add_check_out_date"
        ] = None

    # --------------------------------------------------------
    # CONTAINER
    # --------------------------------------------------------

    with st.container():

        # ====================================================
        # INQUIRY DATE / CLIENT NAME
        # ====================================================

        a, b = st.columns(2)

        with a:

            inquiry_date = st.date_input(
                "Inquiry Date *",
                value=st.session_state[
                    "add_inquiry_date"
                ],
                format="DD-MM-YYYY",
                key="add_inquiry_date",
            )

        with b:

            name = st.text_input(
                "Client Name",
                placeholder="e.g. John Doe",
                key="add_client_name",
            )

        # ====================================================
        # PHONE / EMAIL
        # ====================================================

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

        # ====================================================
        # CHECK-IN / CHECK-OUT
        # ====================================================

        a, b = st.columns(2)

        with a:

            check_in = st.date_input(
                "Check In Date",
                value=st.session_state[
                    "add_check_in_date"
                ],
                format="DD-MM-YYYY",
                key="add_check_in_date",
                on_change=_update_add_checkout,
            )

        with b:

            # ------------------------------------------------
            # CHECKOUT MINIMUM
            # ------------------------------------------------

            if check_in:

                check_out_min = (
                    check_in
                    + timedelta(days=1)
                )

            else:

                check_out_min = None

            # ------------------------------------------------
            # Make sure existing checkout is valid
            # ------------------------------------------------

            current_checkout = st.session_state.get(
                "add_check_out_date"
            )

            if (
                check_out_min
                and (
                    current_checkout is not None
                    and current_checkout < check_out_min
                )
            ):

                st.session_state[
                    "add_check_out_date"
                ] = check_out_min

            check_out = st.date_input(
                "Check Out Date",
                value=st.session_state[
                    "add_check_out_date"
                ],
                min_value=check_out_min,
                format="DD-MM-YYYY",
                key="add_check_out_date",
            )

        # ====================================================
        # AGENT / STATUS / SOURCE
        # ====================================================

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

        # ====================================================
        # BOOKING CONFIRMATION DATE
        # ====================================================

        booking_date = st.date_input(
            "Booking Confirmation Date",
            value=None,
            format="DD-MM-YYYY",
            key="add_booking_date",
        )

        # ====================================================
        # LAST FOLLOW-UP / FOLLOW-UP COUNT
        # ====================================================

        a, b = st.columns(2)

        with a:

            last_follow = st.date_input(
                "Last Follow-up Done On",
                value=None,
                format="DD-MM-YYYY",
                key="add_last_follow",
            )

        with b:

            count = st.selectbox(
                "Follow-up Count",
                [""] + FOLLOW_UP_OPTIONS,
                index=1,
                key="add_followup_count",
            )

        # ====================================================
        # REMARKS
        # ====================================================

        remarks = st.text_area(
            "Remarks",
            placeholder=(
                "Any client notes, preference or comments..."
            ),
            key="add_remarks",
        )

        # ====================================================
        # ADD BUTTON
        # ====================================================

        submitted = st.button(
            "➕ Add Lead",
            type="primary",
            use_container_width=True,
            key="submit_add_lead",
        )

        if submitted:

            # ------------------------------------------------
            # PHONE VALIDATION
            # ------------------------------------------------

            if not phone.strip():

                st.error(
                    "Phone number is required."
                )

                return None

            # ------------------------------------------------
            # CHECKOUT VALIDATION
            # ------------------------------------------------

            if (
                check_in
                and check_out
                and check_out <= check_in
            ):

                st.error(
                    "Check-out date must be after "
                    "the check-in date."
                )

                return None

            # ------------------------------------------------
            # FOLLOW-UP VALIDATION
            # ------------------------------------------------

            if last_follow and not count:

                st.error(
                    "Please select the follow-up count."
                )

                return None

            # ------------------------------------------------
            # RETURN NEW LEAD
            # ------------------------------------------------

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
            }

    return None


# ============================================================
# EDIT LEAD FORM
# ============================================================

def render_edit_lead_form(r):

    # --------------------------------------------------------
    # CURRENT VALUES
    # --------------------------------------------------------

    row_number = r.get(
        "_sheet_row"
    )

    cur_agent = str(
        r.get("Agent", "")
        or ""
    )

    cur_status = str(
        r.get("Status", "")
        or ""
    )

    cur_source = str(
        r.get("Source", "")
        or ""
    )

    cur_count = str(
        r.get("Follow Up Count", "")
        or ""
    )

    # --------------------------------------------------------
    # UNIQUE SESSION KEYS
    # --------------------------------------------------------

    inquiry_key = (
        f"edit_inquiry_date_{row_number}"
    )

    check_in_key = (
        f"edit_check_in_date_{row_number}"
    )

    check_out_key = (
        f"edit_check_out_date_{row_number}"
    )

    # --------------------------------------------------------
    # INITIAL VALUES
    # --------------------------------------------------------

    if inquiry_key not in st.session_state:

        st.session_state[
            inquiry_key
        ] = _parse_date(
            r.get("Date")
        )

    if check_in_key not in st.session_state:

        st.session_state[
            check_in_key
        ] = _parse_date(
            r.get("Check In Date")
        )

    if check_out_key not in st.session_state:

        st.session_state[
            check_out_key
        ] = _parse_date(
            r.get("Check Out Date")
        )

    # --------------------------------------------------------
    # CONTAINER
    # --------------------------------------------------------

    with st.container():

        # ====================================================
        # INQUIRY DATE / CLIENT NAME
        # ====================================================

        a, b = st.columns(2)

        with a:

            inquiry_date = st.date_input(
                "Inquiry Date",
                value=st.session_state[
                    inquiry_key
                ],
                format="DD-MM-YYYY",
                key=inquiry_key,
            )

        with b:

            name = st.text_input(
                "Client Name",
                value=str(
                    r.get("Name", "")
                    or ""
                ),
                key=f"edit_name_{row_number}",
            )

        # ====================================================
        # PHONE / EMAIL
        # ====================================================

        a, b = st.columns(2)

        with a:

            phone = st.text_input(
                "Phone Number",
                value=str(
                    r.get("Number", "")
                    or ""
                ),
                key=f"edit_phone_{row_number}",
            )

        with b:

            email = st.text_input(
                "Email",
                value=str(
                    r.get("Email", "")
                    or ""
                ),
                key=f"edit_email_{row_number}",
            )

        # ====================================================
        # CHECK-IN / CHECK-OUT
        # ====================================================

        a, b = st.columns(2)

        with a:

            check_in = st.date_input(
                "Check In Date",
                value=st.session_state[
                    check_in_key
                ],
                format="DD-MM-YYYY",
                key=check_in_key,
                on_change=lambda: _update_edit_checkout(
                    row_number
                ),
            )

        with b:

            if check_in:

                check_out_min = (
                    check_in
                    + timedelta(days=1)
                )

            else:

                check_out_min = None

            # ------------------------------------------------
            # Prevent invalid checkout
            # ------------------------------------------------

            current_checkout = st.session_state.get(
                check_out_key
            )

            if (
                check_out_min
                and current_checkout is not None
                and current_checkout < check_out_min
            ):

                st.session_state[
                    check_out_key
                ] = check_out_min

            check_out = st.date_input(
                "Check Out Date",
                value=st.session_state[
                    check_out_key
                ],
                min_value=check_out_min,
                format="DD-MM-YYYY",
                key=check_out_key,
            )

        # ====================================================
        # AGENT / STATUS / SOURCE
        # ====================================================

        a, b, c = st.columns(3)

        with a:

            agent = st.selectbox(
                "Assigned Agent",
                AGENTS,
                index=(
                    AGENTS.index(cur_agent)
                    if cur_agent in AGENTS
                    else 0
                ),
                key=f"edit_agent_{row_number}",
            )

        with b:

            status = st.selectbox(
                "Pipeline Status",
                STATUSES,
                index=(
                    STATUSES.index(cur_status)
                    if cur_status in STATUSES
                    else 0
                ),
                key=f"edit_status_{row_number}",
            )

        with c:

            source = st.selectbox(
                "Lead Source",
                SOURCES,
                index=(
                    SOURCES.index(cur_source)
                    if cur_source in SOURCES
                    else 0
                ),
                key=f"edit_source_{row_number}",
            )

        # ====================================================
        # BOOKING CONFIRMATION DATE
        # ====================================================

        booking_date = st.date_input(
            "Booking Confirmation Date",
            value=_parse_date(
                r.get(
                    "Booking Confirmation Date"
                )
            ),
            format="DD-MM-YYYY",
            key=f"edit_booking_date_{row_number}",
        )

        # ====================================================
        # LAST FOLLOW-UP / COUNT
        # ====================================================

        a, b = st.columns(2)

        with a:

            last_follow = st.date_input(
                "Last Follow-up Done On",
                value=_parse_date(
                    r.get(
                        "Last Follow Up"
                    )
                ),
                format="DD-MM-YYYY",
                key=f"edit_last_follow_{row_number}",
            )

        with b:

            idx = (
                FOLLOW_UP_OPTIONS.index(
                    cur_count
                ) + 1
                if cur_count in FOLLOW_UP_OPTIONS
                else 0
            )

            count = st.selectbox(
                "Follow-up Count",
                [""] + FOLLOW_UP_OPTIONS,
                index=idx,
                key=f"edit_followup_count_{row_number}",
            )

        # ====================================================
        # REMARKS
        # ====================================================

        remarks = st.text_area(
            "Remarks",
            value=str(
                r.get("Remarks", "")
                or ""
            ),
            key=f"edit_remarks_{row_number}",
        )

        # ====================================================
        # SAVE BUTTON
        # ====================================================

        submitted = st.button(
            "💾 Save Changes",
            type="primary",
            use_container_width=True,
            key=f"save_edit_{row_number}",
        )

        if submitted:

            # ------------------------------------------------
            # PHONE VALIDATION
            # ------------------------------------------------

            if not phone.strip():

                st.error(
                    "Phone number is required."
                )

                return None

            # ------------------------------------------------
            # CHECKOUT VALIDATION
            # ------------------------------------------------

            if (
                check_in
                and check_out
                and check_out <= check_in
            ):

                st.error(
                    "Check-out date must be after "
                    "the check-in date."
                )

                return None

            # ------------------------------------------------
            # FOLLOW-UP VALIDATION
            # ------------------------------------------------

            if last_follow and not count:

                st.error(
                    "Please select the follow-up count."
                )

                return None

            # ------------------------------------------------
            # RETURN UPDATED LEAD
            # ------------------------------------------------

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
            }

    return None