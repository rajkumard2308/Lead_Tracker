from datetime import date, datetime
import re

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from config import (
    SHEET_NAME,
    WORKSHEET_NAME,
    HEADERS,
    HEADER_ALIASES,
)


# ============================================================
# GOOGLE API SCOPES
# ============================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ============================================================
# GOOGLE CLIENT
# ============================================================

def _get_client():
    """
    Create and authorize Google Sheets client
    using Streamlit secrets.
    """

    info = dict(
        st.secrets["google_service_account"]
    )

    key = info.get(
        "private_key",
        ""
    )

    # Convert escaped \\n into real newlines
    if "\\n" in key:
        key = key.replace(
            "\\n",
            "\n"
        )

    info["private_key"] = (
        key.strip() + "\n"
    )

    creds = Credentials.from_service_account_info(
        info,
        scopes=SCOPES,
    )

    return gspread.authorize(
        creds
    )


# ============================================================
# GET WORKSHEET
# ============================================================

@st.cache_resource
def get_worksheet():
    """
    Connect to the configured Google Sheet
    and return the requested worksheet.
    """

    client = _get_client()

    spreadsheet = client.open(
        SHEET_NAME
    )

    try:

        ws = spreadsheet.worksheet(
            WORKSHEET_NAME
        )

    except gspread.WorksheetNotFound:

        ws = spreadsheet.add_worksheet(
            WORKSHEET_NAME,
            rows=1000,
            cols=len(HEADERS),
        )

        ws.append_row(
            HEADERS
        )

    ensure_headers(
        ws
    )

    return ws


# ============================================================
# HEADER NORMALIZATION
# ============================================================

def _norm(h):
    """
    Normalize a Google Sheet header using
    configured aliases.
    """

    return HEADER_ALIASES.get(
        str(h).strip().upper(),
        str(h).strip(),
    )


# ============================================================
# ENSURE REQUIRED HEADERS
# ============================================================

def ensure_headers(ws):
    """
    Make sure required additional columns exist.
    """

    current = ws.row_values(
        1
    )

    if not current:

        ws.update(
            "A1:M1",
            [HEADERS]
        )

        return

    normalized = [
        _norm(x)
        for x in current
    ]

    for canonical, header in [
        (
            "Booking Confirmation Date",
            "BOOKING CONFIRMATION DATE",
        ),
        (
            "Follow Up Count",
            "Follow Up Count",
        ),
    ]:

        if canonical not in normalized:

            ws.update_cell(
                1,
                len(current) + 1,
                header,
            )

            current.append(
                header
            )

            normalized.append(
                canonical
            )


# ============================================================
# CLEAN VALUE
# ============================================================

def _clean(v):
    """
    Convert values into clean strings before
    writing them to Google Sheets.
    """

    if v is None:
        return ""

    if isinstance(
        v,
        (datetime, date)
    ):
        return v.strftime(
            "%d-%m-%Y"
        )

    s = str(v).strip()

    if s.lower() in {
        "nan",
        "nat",
        "none",
    }:
        return ""

    return s


# ============================================================
# NORMALIZE PHONE NUMBER
# ============================================================

def normalize_phone(phone):
    """
    Normalize phone numbers so different formatting
    does not create duplicate customers.

    Examples:

        9876543210
        +91 9876543210
        +91-9876543210
        91 9876543210

    All become:

        9876543210
    """

    if phone is None:
        return ""

    # Keep only digits
    digits = re.sub(
        r"\D",
        "",
        str(phone),
    )

    # Remove Indian country code
    # when number is 12 digits.
    if (
        len(digits) == 12
        and digits.startswith("91")
    ):
        digits = digits[2:]

    return digits


# ============================================================
# GET ALL LEADS
# ============================================================

@st.cache_data(ttl=10)
def get_leads():
    """
    Read all leads from Google Sheets
    and return them as a DataFrame.
    """

    ws = get_worksheet()

    values = ws.get_all_values()

    expected = [
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
    ]

    if (
        not values
        or len(values) < 2
    ):

        return pd.DataFrame(
            columns=expected + [
                "_sheet_row"
            ]
        )

    headers = [
        _norm(x)
        for x in values[0]
    ]

    rows = []

    for rownum, row in enumerate(
        values[1:],
        start=2,
    ):

        # Make row length equal to header length
        row = row + [
            ""
        ] * (
            len(headers)
            - len(row)
        )

        rec = {
            headers[i]: row[i]
            for i in range(
                len(headers)
            )
        }

        if any(
            str(v).strip()
            for v in rec.values()
        ):

            rec[
                "_sheet_row"
            ] = rownum

            rows.append(
                rec
            )

    df = pd.DataFrame(
        rows
    )

    for col in expected:

        if col not in df.columns:

            df[col] = ""

    return df[
        expected + [
            "_sheet_row"
        ]
    ]


# ============================================================
# SHEET COLUMN MAPPING
# ============================================================

def _mapping(ws):
    """
    Return mapping:

        {
            "Date": 1,
            "Name": 2,
            "Number": 3,
            ...
        }
    """

    return {
        _norm(h): i
        for i, h in enumerate(
            ws.row_values(1),
            start=1,
        )
    }


# ============================================================
# ADD LEAD
# ============================================================

def add_lead(lead):
    """
    Add a new lead to Google Sheets.

    Duplicate protection:
    A lead cannot be added if the same
    normalized phone number already exists.
    """

    ws = get_worksheet()

    mp = _mapping(
        ws
    )

    headers = ws.row_values(
        1
    )

    # --------------------------------------------------------
    # PHONE NUMBER FROM NEW LEAD
    # --------------------------------------------------------

    new_phone = normalize_phone(
        lead.get(
            "Number",
            ""
        )
    )

    # --------------------------------------------------------
    # DUPLICATE PHONE CHECK
    # --------------------------------------------------------

    if new_phone:

        phone_column = mp.get(
            "Number"
        )

        if phone_column is not None:

            # Get all existing values
            values = ws.get_all_values()

            # Skip header row
            for row in values[1:]:

                # Protect against short rows
                if (
                    len(row)
                    >= phone_column
                ):

                    existing_phone = row[
                        phone_column - 1
                    ]

                else:

                    existing_phone = ""

                existing_normalized = (
                    normalize_phone(
                        existing_phone
                    )
                )

                if (
                    existing_normalized
                    and existing_normalized
                    == new_phone
                ):

                    raise ValueError(
                        "Phone number already exists. "
                        "This customer is already present."
                    )

    # --------------------------------------------------------
    # BUILD NEW ROW
    # --------------------------------------------------------

    row = [
        ""
    ] * len(headers)

    for key, value in lead.items():

        if key in mp:

            row[
                mp[key] - 1
            ] = _clean(
                value
            )

    # --------------------------------------------------------
    # APPEND TO GOOGLE SHEET
    # --------------------------------------------------------

    ws.append_row(
        row,
        value_input_option="USER_ENTERED",
    )

    return True


# ============================================================
# UPDATE LEAD
# ============================================================

def update_lead(
    row_number,
    updates,
):
    """
    Update fields for an existing lead.
    """

    ws = get_worksheet()

    mp = _mapping(
        ws
    )

    for field, value in updates.items():

        if field in mp:

            ws.update_cell(
                int(row_number),
                mp[field],
                _clean(value),
            )


# ============================================================
# DELETE LEAD
# ============================================================

def delete_lead(row_number):
    """
    Delete a lead using its actual
    Google Sheet row number.
    """

    worksheet = get_worksheet()

    row_number = int(
        row_number
    )

    if row_number < 2:

        raise ValueError(
            "Invalid row number. "
            "Header row cannot be deleted."
        )

    # Delete complete row
    worksheet.delete_rows(
        row_number
    )

    return True