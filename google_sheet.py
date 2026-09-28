from datetime import date, datetime
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from config import SHEET_NAME, WORKSHEET_NAME, HEADERS, HEADER_ALIASES

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

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
    return ws

def _norm(h):
    return HEADER_ALIASES.get(str(h).strip().upper(), str(h).strip())

def ensure_headers(ws):
    current = ws.row_values(1)
    if not current:
        ws.update("A1:M1", [HEADERS])
        return
    normalized = [_norm(x) for x in current]
    for canonical, header in [
        ("Booking Confirmation Date", "BOOKING CONFIRMATION DATE"),
        ("Follow Up Count", "Follow Up Count"),
    ]:
        if canonical not in normalized:
            ws.update_cell(1, len(current)+1, header)
            current.append(header)
            normalized.append(canonical)

def _clean(v):
    if v is None:
        return ""
    if isinstance(v, (datetime, date)):
        return v.strftime("%d-%m-%Y")
    s = str(v).strip()
    return "" if s.lower() in {"nan","nat","none"} else s

@st.cache_data(ttl=10)
def get_leads():
    ws = get_worksheet()
    values = ws.get_all_values()
    expected = ["Date","Name","Number","Email","Check In Date","Check Out Date",
                "Booking Confirmation Date","Agent","Status","Source",
                "Last Follow Up","Follow Up Count","Remarks"]
    if not values or len(values) < 2:
        return pd.DataFrame(columns=expected + ["_sheet_row"])
    headers = [_norm(x) for x in values[0]]
    rows = []
    for rownum, row in enumerate(values[1:], start=2):
        row = row + [""] * (len(headers)-len(row))
        rec = {headers[i]: row[i] for i in range(len(headers))}
        if any(str(v).strip() for v in rec.values()):
            rec["_sheet_row"] = rownum
            rows.append(rec)
    df = pd.DataFrame(rows)
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    return df[expected + ["_sheet_row"]]

def _mapping(ws):
    return {_norm(h): i for i,h in enumerate(ws.row_values(1), start=1)}

def add_lead(lead):
    ws = get_worksheet()
    mp = _mapping(ws)
    headers = ws.row_values(1)
    row = [""] * len(headers)
    for key, value in lead.items():
        if key in mp:
            row[mp[key]-1] = _clean(value)
    ws.append_row(row, value_input_option="USER_ENTERED")

def update_lead(row_number, updates):
    ws = get_worksheet()
    mp = _mapping(ws)
    for field, value in updates.items():
        if field in mp:
            ws.update_cell(int(row_number), mp[field], _clean(value))

def delete_lead(row_number):
    """
    Delete a lead using its actual Google Sheet row number.
    """

    worksheet = get_worksheet()

    row_number = int(row_number)

    if row_number < 2:
        raise ValueError(
            "Invalid row number. Header row cannot be deleted."
        )

    # Delete the complete row from Google Sheets
    worksheet.delete_rows(row_number)

    return True
