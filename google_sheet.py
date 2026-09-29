from datetime import date, datetime, timedelta
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


# =========================================================
# Google API scopes
# =========================================================

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# =========================================================
# Date fields
# =========================================================

DATE_FIELDS = {
    "Date",
    "Check In Date",
    "Check Out Date",
    "Booking Confirmation Date",
    "Last Follow Up",
}


# =========================================================
# Expected columns
# =========================================================

EXPECTED_COLUMNS = [
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
]


# =========================================================
# Google client
# =========================================================

def _get_client():
    info = dict(st.secrets["google_service_account"])

    key = info.get("private_key", "")

    if "\\n" in key:
        key = key.replace("\\n", "\n")

    info["private_key"] = key.strip() + "\n"

    credentials = Credentials.from_service_account_info(
        info,
        scopes=SCOPES,
    )

    return gspread.authorize(credentials)


# =========================================================
# Worksheet
# =========================================================

@st.cache_resource
def get_worksheet():
    client = _get_client()

    spreadsheet = client.open(SHEET_NAME)

    try:
        ws = spreadsheet.worksheet(WORKSHEET_NAME)

    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=WORKSHEET_NAME,
            rows=1000,
            cols=max(len(HEADERS), len(EXPECTED_COLUMNS)),
        )

        ws.append_row(
            HEADERS,
            value_input_option="USER_ENTERED",
        )

    ensure_headers(ws)

    return ws


# =========================================================
# Header normalization
# =========================================================

def _norm(header):
    """
    Convert Google Sheet header into canonical header name.
    """

    return HEADER_ALIASES.get(
        str(header).strip().upper(),
        str(header).strip(),
    )


# =========================================================
# Ensure required headers exist
# =========================================================

def ensure_headers(ws):
    current = ws.row_values(1)

    if not current:
        headers = list(HEADERS)

        # Make sure Total Amount exists
        normalized_headers = [_norm(h) for h in headers]

        if "Total Amount" not in normalized_headers:
            headers.append("Total Amount")

        ws.update(
            "A1",
            [headers],
            value_input_option="USER_ENTERED",
        )

        return

    normalized = [_norm(h) for h in current]

    required_headers = [
        ("Booking Confirmation Date", "BOOKING CONFIRMATION DATE"),
        ("Follow Up Count", "Follow Up Count"),
        ("Total Amount", "Total Amount"),
    ]

    missing = []

    for canonical, header in required_headers:
        if canonical not in normalized:
            missing.append(header)

    if missing:
        start_col = len(current) + 1

        # Add all missing headers in one operation
        end_col = start_col + len(missing) - 1

        def column_letter(number):
            result = ""

            while number:
                number, remainder = divmod(number - 1, 26)
                result = chr(65 + remainder) + result

            return result

        cell_range = (
            f"{column_letter(start_col)}1:"
            f"{column_letter(end_col)}1"
        )

        ws.update(
            cell_range,
            [missing],
            value_input_option="USER_ENTERED",
        )


# =========================================================
# Value cleaning
# =========================================================

def _clean(value):
    """
    Convert Python values into values suitable for Google Sheets.
    """

    if value is None:
        return ""

    if isinstance(value, (datetime, date)):
        return value.strftime("%d-%m-%Y")

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if text.lower() in {
        "nan",
        "nat",
        "none",
        "null",
    }:
        return ""

    return text


# =========================================================
# Date parsing
# =========================================================

def _parse_date_value(value):
    """
    Parse common date formats and return datetime.date.
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

    formats = (
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%d-%m-%y",
        "%d/%m/%y",
        "%m/%d/%y",
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

    # -----------------------------------------------------
    # Google / Excel serial date
    # -----------------------------------------------------

    try:
        if re.fullmatch(
            r"\d+(?:\.\d+)?",
            text,
        ):
            serial = float(text)

            if 20000 <= serial <= 70000:
                return (
                    datetime(1899, 12, 30)
                    + timedelta(days=serial)
                ).date()

    except (ValueError, OverflowError):
        pass

    return None


# =========================================================
# Normalize date for application
# =========================================================

def _normalize_date_value(value):
    """
    Convert date values to DD-MM-YYYY.

    If the value cannot be parsed, preserve the original
    text instead of deleting it.
    """

    if value is None:
        return ""

    parsed = _parse_date_value(value)

    if parsed:
        return parsed.strftime("%d-%m-%Y")

    text = str(value).strip()

    if text.lower() in {
        "",
        "nan",
        "nat",
        "none",
        "null",
    }:
        return ""

    return text


# =========================================================
# Phone normalization
# =========================================================

def normalize_phone(phone):
    """
    Normalize Indian phone numbers for duplicate detection.

    Examples:

        9876543210
        +91 9876543210
        +91-9876543210
        91 9876543210

    become:

        9876543210
    """

    if phone is None:
        return ""

    digits = re.sub(
        r"\D",
        "",
        str(phone),
    )

    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    return digits


# =========================================================
# Header mapping
# =========================================================

def _mapping(ws):
    """
    Return:

        {
            "Date": 1,
            "Name": 2,
            ...
        }

    Google Sheets columns are 1-based.
    """

    headers = ws.row_values(1)

    return {
        _norm(header): index
        for index, header in enumerate(
            headers,
            start=1,
        )
    }


# =========================================================
# Get all leads
# =========================================================

@st.cache_data(ttl=15)
def get_leads():
    """
    Read leads from Google Sheets.

    Dates are normalized to DD-MM-YYYY for the application.
    """

    ws = get_worksheet()

    values = ws.get_all_values()

    if not values or len(values) < 2:
        return pd.DataFrame(
            columns=EXPECTED_COLUMNS + ["_sheet_row"]
        )

    # -----------------------------------------------------
    # Headers
    # -----------------------------------------------------

    headers = [
        _norm(header)
        for header in values[0]
    ]

    rows = []

    # -----------------------------------------------------
    # Data rows
    # -----------------------------------------------------

    for row_number, row in enumerate(
        values[1:],
        start=2,
    ):

        # Make row same length as headers
        if len(row) < len(headers):
            row = row + [""] * (
                len(headers) - len(row)
            )

        record = {
            headers[index]: row[index]
            for index in range(len(headers))
        }

        # Skip completely empty rows
        if not any(
            str(value).strip()
            for value in record.values()
        ):
            continue

        # -------------------------------------------------
        # Normalize date fields
        # -------------------------------------------------

        for field in DATE_FIELDS:

            if field in record:
                record[field] = _normalize_date_value(
                    record[field]
                )

        record["_sheet_row"] = row_number

        rows.append(record)

    # -----------------------------------------------------
    # DataFrame
    # -----------------------------------------------------

    df = pd.DataFrame(rows)

    # Make sure all expected columns exist
    for column in EXPECTED_COLUMNS:

        if column not in df.columns:
            df[column] = ""

    return df[
        EXPECTED_COLUMNS + ["_sheet_row"]
    ]


# =========================================================
# Duplicate phone check
# =========================================================

def _phone_exists(
    ws,
    phone,
    exclude_row=None,
):
    """
    Check whether a normalized phone number already exists.

    exclude_row is used during editing so a lead can keep
    its own phone number.
    """

    normalized_phone = normalize_phone(phone)

    if not normalized_phone:
        return False

    mapping = _mapping(ws)

    phone_column = mapping.get("Number")

    if not phone_column:
        return False

    values = ws.get_all_values()

    for sheet_row, row in enumerate(
        values[1:],
        start=2,
    ):

        if (
            exclude_row is not None
            and sheet_row == int(exclude_row)
        ):
            continue

        if len(row) < phone_column:
            continue

        existing_phone = row[
            phone_column - 1
        ]

        if (
            normalize_phone(existing_phone)
            == normalized_phone
        ):
            return True

    return False


# =========================================================
# Add lead
# =========================================================

def add_lead(lead):
    ws = get_worksheet()

    mapping = _mapping(ws)

    headers = ws.row_values(1)

    # -----------------------------------------------------
    # Duplicate phone protection
    # -----------------------------------------------------

    phone = lead.get("Number", "")

    if _phone_exists(ws, phone):

        raise ValueError(
            "Phone number already exists. "
            "This customer is already present."
        )

    # -----------------------------------------------------
    # Build row
    # -----------------------------------------------------

    row = [""] * len(headers)

    for field, value in lead.items():

        column = mapping.get(field)

        if column:
            row[column - 1] = _clean(value)

    # -----------------------------------------------------
    # Append
    # -----------------------------------------------------

    ws.append_row(
        row,
        value_input_option="USER_ENTERED",
    )

    # Clear cached data
    get_leads.clear()


# =========================================================
# Update lead
# =========================================================

def update_lead(
    row_number,
    updates,
):
    ws = get_worksheet()

    row_number = int(row_number)

    mapping = _mapping(ws)

    # -----------------------------------------------------
    # Duplicate phone protection
    # -----------------------------------------------------

    if "Number" in updates:

        phone = updates.get(
            "Number",
            "",
        )

        if _phone_exists(
            ws,
            phone,
            exclude_row=row_number,
        ):

            raise ValueError(
                "Phone number already exists "
                "for another customer."
            )

    # -----------------------------------------------------
    # Batch update
    #
    # This is significantly faster than calling
    # update_cell() separately for every field.
    # -----------------------------------------------------

    update_data = []

    for field, value in updates.items():

        column = mapping.get(field)

        if not column:
            continue

        # Convert column number to A1 letter
        column_letter = ""

        number = column

        while number:
            number, remainder = divmod(
                number - 1,
                26,
            )

            column_letter = (
                chr(65 + remainder)
                + column_letter
            )

        update_data.append(
            {
                "range": (
                    f"{column_letter}{row_number}"
                ),
                "values": [
                    [_clean(value)]
                ],
            }
        )

    if update_data:

        ws.batch_update(
            update_data,
            value_input_option="USER_ENTERED",
        )

    # Clear cached data
    get_leads.clear()


# =========================================================
# Delete lead
# =========================================================

def delete_lead(row_number):
    ws = get_worksheet()

    row_number = int(row_number)

    if row_number < 2:
        raise ValueError(
            "Invalid row number. "
            "Header row cannot be deleted."
        )

    ws.delete_rows(row_number)

    # Clear cached data
    get_leads.clear()

    return True