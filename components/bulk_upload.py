from io import BytesIO

import pandas as pd
import streamlit as st

from config import AGENTS, HEADERS, SOURCES, STATUSES
from google_sheet import normalize_phone

CANONICAL_COLUMNS = [
    "Date", "Name", "Number", "Email", "Check In Date", "Check Out Date",
    "Booking Confirmation Date", "Agent", "Status", "Source", "Last Follow Up",
    "Follow Up Count", "Remarks", "Total Amount",
]
REQUIRED_COLUMNS = ["Date", "Name", "Number"]


def _template_bytes():
    df = pd.DataFrame(columns=CANONICAL_COLUMNS)
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Leads")
    bio.seek(0)
    return bio.getvalue()


def _read_upload(uploaded):
    name = uploaded.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded)
    return pd.read_excel(uploaded, engine="openpyxl")


def _clean_text(value):
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _date_value(value):
    if value is None or pd.isna(value) or str(value).strip() == "":
        return None
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def render_bulk_upload(existing_df):
    st.caption("Upload Excel/CSV → validate → preview → add all new leads in one batch.")

    st.download_button(
        "📄 Download Excel Template",
        data=_template_bytes(),
        file_name="lead_bulk_upload_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )

    uploaded = st.file_uploader(
        "Upload Excel or CSV",
        type=["xlsx", "xls", "csv"],
        key="bulk_lead_file",
    )

    if uploaded is None:
        return None

    try:
        raw = _read_upload(uploaded)
    except Exception as exc:
        st.error(f"Could not read the file: {exc}")
        return None

    if raw.empty:
        st.warning("The uploaded file is empty.")
        return None

    # Normalize uploaded column names using common variants.
    aliases = {
        "DATE": "Date", "NAME": "Name", "NUMBER": "Number", "PHONE": "Number",
        "PHONE NUMBER": "Number", "EMAIL": "Email", "CHECK IN DATE": "Check In Date",
        "CHECK OUT DATE": "Check Out Date", "BOOKING CONFIRMATION DATE": "Booking Confirmation Date",
        "AGENT": "Agent", "STATUS": "Status", "SOURCE": "Source",
        "LAST FOLLOW UP": "Last Follow Up", "LAST FOLLOW UP DONE ON": "Last Follow Up",
        "FOLLOW UP COUNT": "Follow Up Count", "REMARKS": "Remarks", "TOTAL AMOUNT": "Total Amount",
    }
    raw.columns = [aliases.get(str(c).strip().upper(), str(c).strip()) for c in raw.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    if missing:
        st.error("Missing required columns: " + ", ".join(missing))
        return None

    existing_phones = set()
    if existing_df is not None and not existing_df.empty and "Number" in existing_df.columns:
        existing_phones = {
            normalize_phone(x) for x in existing_df["Number"].tolist() if normalize_phone(x)
        }

    seen_upload = set()
    valid = []
    errors = []
    duplicates = []

    for excel_row, row in raw.iterrows():
        display_row = excel_row + 2
        name = _clean_text(row.get("Name"))
        phone = normalize_phone(row.get("Number"))
        status = _clean_text(row.get("Status")) or "Quotation Given"
        agent = _clean_text(row.get("Agent"))
        source = _clean_text(row.get("Source"))

        row_errors = []
        if not _date_value(row.get("Date")):
            row_errors.append("Date is required/invalid")
        if not name:
            row_errors.append("Name is required")
        if not phone:
            row_errors.append("Phone number is required/invalid")
        if status not in STATUSES:
            row_errors.append(f"Invalid status: {status}")
        if agent and agent not in AGENTS:
            row_errors.append(f"Invalid agent: {agent}")
        if source and source not in SOURCES:
            row_errors.append(f"Invalid source: {source}")

        if phone and (phone in existing_phones or phone in seen_upload):
            duplicates.append((display_row, phone, "Duplicate phone number"))
            continue

        if row_errors:
            errors.append((display_row, "; ".join(row_errors)))
            continue

        lead = {
            "Date": _date_value(row.get("Date")),
            "Name": name,
            "Number": phone,
            "Email": _clean_text(row.get("Email")),
            "Check In Date": _date_value(row.get("Check In Date")),
            "Check Out Date": _date_value(row.get("Check Out Date")),
            "Booking Confirmation Date": _date_value(row.get("Booking Confirmation Date")),
            "Agent": agent,
            "Status": status,
            "Source": source,
            "Last Follow Up": _date_value(row.get("Last Follow Up")),
            "Follow Up Count": _clean_text(row.get("Follow Up Count")),
            "Remarks": _clean_text(row.get("Remarks")),
            "Total Amount": _clean_text(row.get("Total Amount")),
        }
        if not lead["Follow Up Count"]:
            lead["Follow Up Count"] = ""
        if status != "Converted":
            lead["Total Amount"] = ""
        valid.append(lead)
        seen_upload.add(phone)

    st.write(f"**Rows:** {len(raw)}  |  **New:** {len(valid)}  |  **Duplicates:** {len(duplicates)}  |  **Invalid:** {len(errors)}")

    if duplicates:
        with st.expander(f"⚠️ Duplicates ({len(duplicates)})"):
            st.dataframe(pd.DataFrame(duplicates, columns=["Excel Row", "Phone", "Reason"]), use_container_width=True, hide_index=True)

    if errors:
        with st.expander(f"❌ Invalid rows ({len(errors)})"):
            st.dataframe(pd.DataFrame(errors, columns=["Excel Row", "Reason"]), use_container_width=True, hide_index=True)

    if valid:
        preview = pd.DataFrame(valid)
        st.markdown("#### Preview new leads")
        st.dataframe(preview, use_container_width=True, hide_index=True)

        if st.button(f"✅ Add {len(valid)} New Leads", type="primary", use_container_width=True, key="bulk_add_confirm"):
            return {"__action__": "add_bulk", "leads": valid}

    if st.button("✖ Close Bulk Add", use_container_width=True, key="bulk_close"):
        return {"__action__": "cancel"}

    return None
