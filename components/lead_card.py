import html
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from config import STATUSES


FOLLOW_UP_OPTIONS = [
    f"Follow up {i}"
    for i in range(1, 9)
]


def copy_phone_button(phone, row_number):

    phone = str(phone or "").strip()

    if not phone:
        st.caption("No phone")

        return

    safe_phone = html.escape(
        phone,
        quote=True
    )

    components.html(
        f"""
        <div style="
            display:flex;
            align-items:center;
            gap:6px;
            font-family:Arial,sans-serif;
        ">

            <span style="
                font-size:13px;
                color:#374151;
                white-space:nowrap;
            ">
                📞 {safe_phone}
            </span>

            <button
                onclick="copyPhone()"
                style="
                    border:1px solid #d1d5db;
                    background:white;
                    border-radius:6px;
                    padding:4px 8px;
                    cursor:pointer;
                    font-size:11px;
                    color:#374151;
                "
            >
                📋 Copy
            </button>

            <span
                id="copied"
                style="
                    display:none;
                    font-size:10px;
                    color:#059669;
                "
            >
                Copied!
            </span>

        </div>

        <script>

        function copyPhone() {{

            const phone = `{safe_phone}`;

            if (
                navigator.clipboard &&
                window.isSecureContext
            ) {{

                navigator.clipboard
                    .writeText(phone)
                    .then(function() {{
                        showCopied();
                    }});

            }} else {{

                const textarea =
                    document.createElement("textarea");

                textarea.value = phone;

                document.body.appendChild(
                    textarea
                );

                textarea.select();

                document.execCommand(
                    "copy"
                );

                textarea.remove();

                showCopied();
            }}
        }}

        function showCopied() {{

            const element =
                document.getElementById(
                    "copied"
                );

            element.style.display =
                "inline";

            setTimeout(
                function() {{
                    element.style.display =
                        "none";
                }},
                1500
            );
        }}

        </script>
        """,
        height=42,
    )


def render_lead_card(record):

    row_number = int(
        record["_sheet_row"]
    )

    name = str(
        record.get(
            "Name",
            ""
        ) or "Unnamed Lead"
    )

    phone = str(
        record.get(
            "Number",
            ""
        ) or ""
    )

    email = str(
        record.get(
            "Email",
            ""
        ) or ""
    )

    total_amount_raw = record.get(
        "Total Amount",
        ""
    )

    try:
        total_amount = float(
            str(total_amount_raw)
            .replace(",", "")
            .replace("₹", "")
            .strip()
        ) if str(total_amount_raw).strip() else 0.0
    except (ValueError, TypeError):
        total_amount = 0.0

    inquiry_date = str(
        record.get(
            "Date",
            ""
        ) or ""
    )

    check_in = str(
        record.get(
            "Check In Date",
            ""
        ) or ""
    )

    check_out = str(
        record.get(
            "Check Out Date",
            ""
        ) or ""
    )

    agent = str(
        record.get(
            "Agent",
            ""
        ) or ""
    )

    source = str(
        record.get(
            "Source",
            ""
        ) or ""
    )

    booking_date = str(
        record.get(
            "Booking Confirmation Date",
            ""
        ) or ""
    )

    last_followup = str(
        record.get(
            "Last Follow Up",
            ""
        ) or ""
    )

    follow_count = str(
        record.get(
            "Follow Up Count",
            ""
        ) or ""
    )

    remarks = str(
        record.get(
            "Remarks",
            ""
        ) or ""
    )

    current_status = str(
        record.get(
            "Status",
            ""
        ) or ""
    )

    # ------------------------------------------------
    # LEAD ROW
    # ------------------------------------------------

    with st.container(
        border=True
    ):

        columns = st.columns(
            [
                1.25,
                1.35,
                1.40,
                1.35,
                1.55,
                2.10,
            ]
        )

        # ============================================
        # CLIENT
        # ============================================

        with columns[0]:

            st.markdown(
                f"**{html.escape(name)}**"
            )

            st.caption(
                f"📅 {html.escape(inquiry_date)}"
            )

            if email:

                st.caption(
                    f"✉️ {html.escape(email)}"
                )

            # Converted lead amount appears directly below email.
            if current_status == "Converted":
                st.markdown(
                    f"**₹ {total_amount:,.2f}**"
                )

        # ============================================
        # PHONE
        # ============================================

        with columns[1]:

            copy_phone_button(
                phone,
                row_number
            )

        # ============================================
        # STAY DATES
        # ============================================

        with columns[2]:

            if check_in:

                st.caption(
                    "STAY"
                )

                st.write(
                    f"📅 {check_in}"
                )

                if check_out:

                    st.write(
                        f"→ {check_out}"
                    )

            else:

                st.caption(
                    "No stay dates"
                )

            if booking_date:

                st.success(
                    f"✓ Booked {booking_date}"
                )

        # ============================================
        # AGENT / SOURCE
        # ============================================

        with columns[3]:

            st.caption(
                "AGENT"
            )

            st.write(
                f"👤 {agent}"
            )

            st.caption(
                f"🔗 {source}"
            )

        # ============================================
        # FOLLOW-UP
        # ============================================

        with columns[4]:

            if follow_count:

                st.info(
                    f"🔔 {follow_count}"
                )

            if last_followup:

                st.caption(
                    "LAST FOLLOW-UP"
                )

                st.write(
                    last_followup
                )

            if remarks:

                short_remarks = remarks

                if len(short_remarks) > 70:

                    short_remarks = (
                        short_remarks[:70]
                        + "..."
                    )

                st.caption(
                    short_remarks
                )

        # ============================================
        # ACTIONS
        # ============================================

        with columns[5]:

            if st.button(
                "✏️ Edit",
                key=f"edit_{row_number}",
                use_container_width=True,
            ):

                return {
                    "action": "edit",
                    "row_number": row_number,
                }

            if st.button(
                "🗑️ Delete",
                key=f"delete_{row_number}",
                use_container_width=True,
            ):

                return {
                    "action": "delete",
                    "row_number": row_number,
                }

            # ----------------------------------------
            # STATUS
            # ----------------------------------------

            new_status = st.selectbox(
                "Status",
                STATUSES,
                index=(
                    STATUSES.index(
                        current_status
                    )
                    if current_status
                    in STATUSES
                    else 0
                ),
                key=f"status_{row_number}",
                label_visibility="collapsed",
            )

            # ----------------------------------------
            # FOLLOW-UP BOX
            # Automatically appears when Follow up
            # is selected
            # ----------------------------------------

            if new_status == "Follow up":

                current_follow_index = 0

                if follow_count in FOLLOW_UP_OPTIONS:
                    current_follow_index = FOLLOW_UP_OPTIONS.index(
                        follow_count
                    )

                # ------------------------------------------------
                # LAST FOLLOW-UP DATE + FOLLOW-UP COUNT
                # ------------------------------------------------
                follow_date_col, follow_count_col = st.columns(
                    [1.35, 1.25]
                )

                with follow_date_col:

                    existing_followup_date = None

                    if last_followup:
                        try:
                            existing_followup_date = pd.to_datetime(
                                last_followup,
                                dayfirst=True,
                                errors="coerce",
                            )

                            if pd.isna(existing_followup_date):
                                existing_followup_date = None
                            else:
                                existing_followup_date = existing_followup_date.date()

                        except Exception:
                            existing_followup_date = None

                    selected_last_followup = st.date_input(
                        "Last Follow-up Done On",
                        value=existing_followup_date,
                        format="DD-MM-YYYY",
                        key=f"last_followup_{row_number}",
                        label_visibility="visible",
                    )

                with follow_count_col:

                    selected_followup = st.selectbox(
                        "Follow-up Count",
                        FOLLOW_UP_OPTIONS,
                        index=current_follow_index,
                        key=f"followup_{row_number}",
                        label_visibility="visible",
                    )

            else:

                selected_followup = (
                    follow_count
                    if follow_count
                    else ""
                )

                selected_last_followup = None

            # ----------------------------------------
            # UPDATE
            # ----------------------------------------

            changed = (
                    new_status != current_status
                    or (
                            new_status == "Follow up"
                            and selected_followup != follow_count
                    )
                    or (
                            new_status == "Follow up"
                            and (
                                    (
                                            selected_last_followup is not None
                                            and str(selected_last_followup)
                                            != str(last_followup)
                                    )
                                    or (
                                            selected_last_followup is None
                                            and last_followup
                                    )
                            )
                    )
            )

            if changed:

                if st.button(
                    "✓ Update",
                    key=f"update_{row_number}",
                    use_container_width=True,
                    type="primary",
                ):

                    return {
                        "action": "status",
                        "row_number": row_number,
                        "new_status": new_status,
                        "follow_up_count": (
                            selected_followup
                            if new_status
                            == "Follow up"
                            else ""
                        ),
                        "last_follow_up": (
                            selected_last_followup
                            if new_status == "Follow up"
                            else None
                        ),
                    }

    return None