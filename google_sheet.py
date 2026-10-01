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

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

DATE_FIELDS = {
    "Date",
    "Check In Date",
    "Check Out Date",
    "Booking Confirmation Date",
    "Last Follow Up",
}

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
            value_input_option="RAW",
        )

    ensure_headers(ws)
    return ws


def _norm(header):
    return HEADER_ALIASES.get(
        str(header).strip().upper(),
        str(header).strip(),
    )


def ensure_headers(ws):
    current = ws.row_values(1)

    if not current:
        headers = list(HEADERS)
        normalized = [_norm(h) for h in headers]

        if "Total Amount" not in normalized:
            headers.append("Total Amount")

        ws.update(
            "A1",
            [headers],
            value_input_option="RAW",
        )
        return

    normalized = [_norm(h) for h in current]

    required_headers = [
        ("Booking Confirmation Date", "BOOKING CONFIRMATION DATE"),
        ("Follow Up Count", "Follow Up Count"),
        ("Total Amount", "Total Amount"),
    ]

    missing = [
        header
        for canonical, header in required_headers
        if canonical not in normalized
    ]

    if not missing:
        return

    start_col = len(current) + 1
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
        value_input_option="RAW",
    )


def _clean(value):
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
        "",
        "nan",
        "nat",
        "none",
        "null",
    }:
        return ""

    return text


def _parse_date_value(value):
    """
    Convert a Google Sheets value to datetime.date.

    Application standard is always DD-MM-YYYY.

    Important:
    Google Sheets is read with UNFORMATTED_VALUE +
    SERIAL_NUMBER, so actual date cells are not affected
    by the spreadsheet's locale.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    if not text or text.lower() in {
        "nan",
        "nat",
        "none",
        "null",
    }:
        return None

    # Google Sheets / Excel serial date.
    try:
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            serial = float(text)

            if 20000 <= serial <= 70000:
                return (
                        datetime(1899, 12, 30)
                        + timedelta(days=serial)
                ).date()
    except (ValueError, OverflowError):
        pass

    # Remove time from ordinary datetime strings.
    if " " in text:
        first_part = text.split(" ", 1)[0]
        if re.fullmatch(
                r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}",
                first_part,
        ):
            text = first_part

    # Explicitly resolve slash dates.
    # Ambiguous 09/10/2026 means DD/MM/YYYY.
    slash_match = re.fullmatch(
        r"(\d{1,2})/(\d{1,2})/(\d{2,4})",
        text,
    )

    if slash_match:
        first = int(slash_match.group(1))
        second = int(slash_match.group(2))

        if first > 12 and second <= 12:
            formats = ("%d/%m/%Y", "%d/%m/%y")
        elif second > 12 and first <= 12:
            # Existing US-formatted text can still be read if
            # DD/MM/YYYY is mathematically impossible.
            formats = ("%m/%d/%Y", "%m/%d/%y")
        else:
            formats = ("%d/%m/%Y", "%d/%m/%y")

        for fmt in formats:
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue

    formats = (
        "%d-%m-%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%y",
        "%d.%m.%y",
        "%d %B %Y",
        "%d %b %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def _normalize_date_value(value):
    parsed = _parse_date_value(value)

    if parsed is not None:
        return parsed.strftime("%d-%m-%Y")

    text = "" if value is None else str(value).strip()

    if text.lower() in {
        "",
        "nan",
        "nat",
        "none",
        "null",
    }:
        return ""

    return text


def normalize_phone(phone):
    if phone is None:
        return ""

    digits = re.sub(r"\D", "", str(phone))

    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]

    return digits


def _mapping(headers):
    """Build a canonical header -> 1-based column mapping."""
    return {
        _norm(header): index
        for index, header in enumerate(
            headers,
            start=1,
        )
    }


@st.cache_data(ttl=60, show_spinner=False)
def _get_sheet_values():
    """
    Read unformatted Google Sheet values.

    Actual Google Sheet date cells are returned as serial
    numbers, which removes locale ambiguity such as
    MM/DD versus DD/MM.
    """
    ws = get_worksheet()

    return ws.get_all_values(
        value_render_option="UNFORMATTED_VALUE",
        date_time_render_option="SERIAL_NUMBER",
    )


@st.cache_data(ttl=300, show_spinner=False)
def _get_sheet_headers():
    """Return cached raw sheet headers."""
    values = _get_sheet_values()
    return list(values[0]) if values else []


@st.cache_data(ttl=300, show_spinner=False)
def get_leads():
    values = _get_sheet_values()

    if not values or len(values) < 2:
        return pd.DataFrame(
            columns=EXPECTED_COLUMNS + ["_sheet_row"]
        )

    headers = [_norm(header) for header in values[0]]
    rows = []

    for row_number, row in enumerate(values[1:], start=2):
        if len(row) < len(headers):
            row = row + [""] * (len(headers) - len(row))

        record = {
            headers[index]: row[index]
            for index in range(len(headers))
        }

        if not any(
                str(value).strip()
                for value in record.values()
        ):
            continue

        for field in DATE_FIELDS:
            if field in record:
                record[field] = _normalize_date_value(
                    record[field]
                )

        record["_sheet_row"] = row_number
        rows.append(record)

    df = pd.DataFrame(rows)

    for column in EXPECTED_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    return df[EXPECTED_COLUMNS + ["_sheet_row"]]


def _phone_exists(phone, exclude_row=None):
    normalized_phone = normalize_phone(phone)

    if not normalized_phone:
        return False

    values = _get_sheet_values()

    if not values:
        return False

    headers = values[0]
    mapping = _mapping(headers)
    phone_column = mapping.get("Number")

    if not phone_column:
        return False

    for sheet_row, row in enumerate(values[1:], start=2):

        if (
                exclude_row is not None
                and sheet_row == int(exclude_row)
        ):
            continue

        if len(row) < phone_column:
            continue

        existing_phone = row[phone_column - 1]

        if normalize_phone(existing_phone) == normalized_phone:
            return True

    return False


def _clear_data_caches():
    get_leads.clear()
    _get_sheet_values.clear()
    _get_sheet_headers.clear()


def add_lead(lead):
    ws = get_worksheet()

    values = _get_sheet_values()
    headers = list(values[0]) if values else list(HEADERS)
    mapping = _mapping(headers)

    phone = lead.get("Number", "")

    if _phone_exists(phone):
        raise ValueError(
            "Phone number already exists. "
            "This customer is already present."
        )

    row = [""] * len(headers)

    for field, value in lead.items():

        if field.startswith("__"):
            continue

        column = mapping.get(field)

        if column:
            row[column - 1] = _clean(value)

    ws.append_row(
        row,
        value_input_option="RAW",
    )

    _clear_data_caches()



def add_leads_bulk(leads):
    """Append multiple validated leads in one Google Sheets request."""
    if not leads:
        return 0

    ws = get_worksheet()
    values = _get_sheet_values()
    headers = list(values[0]) if values else list(HEADERS)
    mapping = _mapping(headers)

    # Final duplicate protection against current sheet data and
    # duplicates inside the same upload.
    existing_phones = set()
    if values:
        phone_column = mapping.get("Number")
        if phone_column:
            for row in values[1:]:
                if len(row) >= phone_column:
                    normalized = normalize_phone(row[phone_column - 1])
                    if normalized:
                        existing_phones.add(normalized)

    rows = []
    batch_phones = set()

    for lead in leads:
        phone = normalize_phone(lead.get("Number", ""))
        if phone and (phone in existing_phones or phone in batch_phones):
            raise ValueError(
                f"Duplicate phone number found during bulk insert: {phone}"
            )

        row = [""] * len(headers)
        for field, value in lead.items():
            if field.startswith("__"):
                continue
            column = mapping.get(field)
            if column:
                row[column - 1] = _clean(value)

        rows.append(row)
        if phone:
            batch_phones.add(phone)

    ws.append_rows(
        rows,
        value_input_option="RAW",
    )

    _clear_data_caches()
    return len(rows)

def update_lead(row_number, updates):
    """
    Update a complete existing row in one Google Sheets request.

    The current row is taken from the cached sheet snapshot,
    avoiding an additional row_values() request.
    """
    ws = get_worksheet()
    row_number = int(row_number)

    if row_number < 2:
        raise ValueError(
            "Invalid row number. Header row cannot be updated."
        )

    values = _get_sheet_values()

    if not values:
        raise ValueError(
            "Google Sheet data could not be read."
        )

    headers = list(values[0])
    mapping = _mapping(headers)

    if "Number" in updates:

        phone = updates.get("Number", "")

        if _phone_exists(
                phone,
                exclude_row=row_number,
        ):
            raise ValueError(
                "Phone number already exists "
                "for another customer."
            )

    row_index = row_number - 1

    if row_index >= len(values):
        raise ValueError(
            "The selected lead no longer exists in Google Sheets."
        )

    current_row = list(values[row_index])

    if len(current_row) < len(headers):
        current_row += [""] * (
                len(headers) - len(current_row)
        )
    elif len(current_row) > len(headers):
        current_row = current_row[:len(headers)]

    for field, value in updates.items():

        if field.startswith("__"):
            continue

        column = mapping.get(field)

        if column:
            current_row[column - 1] = _clean(value)

    def column_letter(number):
        result = ""

        while number:
            number, remainder = divmod(
                number - 1,
                26,
            )
            result = (
                    chr(65 + remainder)
                    + result
            )

        return result

    last_column = column_letter(
        len(headers)
    )

    ws.update(
        f"A{row_number}:{last_column}{row_number}",
        [current_row],
        value_input_option="RAW",
    )

    _clear_data_caches()


def delete_lead(row_number):
    ws = get_worksheet()
    row_number = int(row_number)

    if row_number < 2:
        raise ValueError(
            "Invalid row number. "
            "Header row cannot be deleted."
        )

    ws.delete_rows(row_number)
    _clear_data_caches()

    return True
