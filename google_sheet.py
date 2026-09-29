from datetime import date, datetime, timedelta
import re

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

from config import SHEET_NAME, WORKSHEET_NAME, HEADERS, HEADER_ALIASES

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


def _get_client():
    info = dict(st.secrets["google_service_account"])
    key = info.get("private_key", "")
    if "\\n" in key:
        key = key.replace("\\n", "\n")
    info["private_key"] = key.strip() + "\n"
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource
def get_worksheet():
    client = _get_client()
    spreadsheet = client.open(SHEET_NAME)
    try:
        ws = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(WORKSHEET_NAME, rows=1000, cols=len(HEADERS))
        ws.append_row(HEADERS)
    ensure_headers(ws)
    _format_sheet_date_columns(ws)
    return ws


def _norm(h):
    return HEADER_ALIASES.get(str(h).strip().upper(), str(h).strip())


def ensure_headers(ws):
    current = ws.row_values(1)
    if not current:
        ws.update("A1:N1", [HEADERS])
        return

    normalized = [_norm(x) for x in current]

    for canonical, header in [
        ("Booking Confirmation Date", "BOOKING CONFIRMATION DATE"),
        ("Follow Up Count", "Follow Up Count"),
        ("Total Amount", "Total Amount"),
    ]:
        if canonical not in normalized:
            ws.update_cell(1, len(current) + 1, header)
            current.append(header)
            normalized.append(canonical)


def _clean(v):
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%d-%m-%Y")
    s = str(v).strip()
    return "" if s.lower() in {"nan", "nat", "none"} else s


def _parse_date_value(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text or text.lower() in {"nan", "nat", "none"}:
        return None

    formats = (
        "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y",
        "%Y/%m/%d", "%d.%m.%Y", "%d %B %Y", "%d %b %Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass

    # Handle Google/Excel-style serial date values if returned as digits.
    try:
        if re.fullmatch(r"\d+(?:\.\d+)?", text):
            serial = float(text)
            if 20000 <= serial <= 70000:
                return (datetime(1899, 12, 30) + timedelta(days=serial)).date()
    except (ValueError, OverflowError):
        pass

    return None


def _format_date_for_app(value):
    parsed = _parse_date_value(value)
    return parsed.strftime("%d-%m-%Y") if parsed else _clean(value)


@st.cache_data(ttl=10)
def get_leads():
    ws = get_worksheet()
    values = ws.get_all_values()

    expected = [
        "Date", "Name", "Number", "Email", "Check In Date", "Check Out Date",
        "Booking Confirmation Date", "Agent", "Status", "Source",
        "Last Follow Up", "Follow Up Count", "Remarks", "Total Amount",
    ]

    if not values or len(values) < 2:
        return pd.DataFrame(columns=expected + ["_sheet_row"])

    headers = [_norm(x) for x in values[0]]
    rows = []

    for rownum, row in enumerate(values[1:], start=2):
        row = row + [""] * (len(headers) - len(row))
        rec = {headers[i]: row[i] for i in range(len(headers))}

        if any(str(v).strip() for v in rec.values()):
            for field in DATE_FIELDS:
                if field in rec:
                    rec[field] = _format_date_for_app(rec[field])

            rec["_sheet_row"] = rownum
            rows.append(rec)

    df = pd.DataFrame(rows)

    for col in expected:
        if col not in df.columns:
            df[col] = ""

    return df[expected + ["_sheet_row"]]


def _mapping(ws):
    return {_norm(h): i for i, h in enumerate(ws.row_values(1), start=1)}


def normalize_phone(phone):
    if phone is None:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    return digits


def _format_sheet_date_columns(ws):
    """Keep all date columns in Google Sheets visually formatted as dd-mm-yyyy."""
    mp = _mapping(ws)
    requests = []
    for field in DATE_FIELDS:
        col = mp.get(field)
        if col:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": ws.id,
                        "startRowIndex": 1,
                        "startColumnIndex": col - 1,
                        "endColumnIndex": col,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "DATE",
                                "pattern": "dd-mm-yyyy",
                            }
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat",
                }
            })
    if requests:
        ws.spreadsheet.batch_update({"requests": requests})


def add_lead(lead):
    ws = get_worksheet()
    mp = _mapping(ws)
    headers = ws.row_values(1)

    new_phone = normalize_phone(lead.get("Number", ""))
    if new_phone:
        phone_column = mp.get("Number")
        if phone_column is not None:
            values = ws.get_all_values()
            for row in values[1:]:
                existing_phone = row[phone_column - 1] if len(row) >= phone_column else ""
                if normalize_phone(existing_phone) == new_phone:
                    raise ValueError(
                        "Phone number already exists. This customer is already present."
                    )

    row = [""] * len(headers)
    for key, value in lead.items():
        if key in mp:
            row[mp[key] - 1] = _clean(value)

    ws.append_row(row, value_input_option="USER_ENTERED")
    _format_sheet_date_columns(ws)


def update_lead(row_number, updates):
    ws = get_worksheet()
    mp = _mapping(ws)

    # Prevent changing a lead to another customer's phone number.
    if "Number" in updates:
        new_phone = normalize_phone(updates.get("Number", ""))
        phone_column = mp.get("Number")
        if new_phone and phone_column is not None:
            values = ws.get_all_values()
            target_row = int(row_number)
            for sheet_row, row in enumerate(values[1:], start=2):
                if sheet_row == target_row:
                    continue
                existing_phone = row[phone_column - 1] if len(row) >= phone_column else ""
                if normalize_phone(existing_phone) == new_phone:
                    raise ValueError(
                        "Phone number already exists for another customer."
                    )

    for field, value in updates.items():
        if field in mp:
            ws.update_cell(int(row_number), mp[field], _clean(value))

    _format_sheet_date_columns(ws)


def delete_lead(row_number):
    ws = get_worksheet()
    row_number = int(row_number)
    if row_number < 2:
        raise ValueError("Invalid row number. Header row cannot be deleted.")
    ws.delete_rows(row_number)
    return True
