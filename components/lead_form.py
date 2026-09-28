from datetime import date, datetime
import streamlit as st
from config import STATUSES, SOURCES, AGENTS, FOLLOW_UP_OPTIONS

def _parse_date(value):
    if not value: return None
    if isinstance(value, date): return value
    for fmt in ("%d-%m-%Y","%Y-%m-%d","%d/%m/%Y","%m/%d/%Y","%d %B %Y","%d %b %Y"):
        try: return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError: pass
    return None

def render_add_lead_form():
    with st.form("add_lead_form"):
        a,b=st.columns(2)
        with a: inquiry_date=st.date_input("Inquiry Date *", date.today(), format="DD-MM-YYYY")
        with b: name=st.text_input("Client Name", placeholder="e.g. John Doe")
        a,b=st.columns(2)
        with a: phone=st.text_input("Phone Number *", placeholder="e.g. 98111 22233")
        with b: email=st.text_input("Email", placeholder="client@example.com")
        a,b=st.columns(2)
        with a: check_in=st.date_input("Check In Date", value=None, format="DD-MM-YYYY")
        with b: check_out=st.date_input("Check Out Date", value=None, format="DD-MM-YYYY")
        a,b,c=st.columns(3)
        with a: agent=st.selectbox("Assigned Agent", AGENTS)
        with b: status=st.selectbox("Pipeline Status", STATUSES)
        with c: source=st.selectbox("Lead Source", SOURCES)
        booking_date=st.date_input("Booking Confirmation Date", value=None, format="DD-MM-YYYY")
        a,b=st.columns(2)
        with a: last_follow=st.date_input("Last Follow-up Done On", value=None, format="DD-MM-YYYY")
        with b: count=st.selectbox("Follow-up Count", [""]+FOLLOW_UP_OPTIONS, index=1)
        remarks=st.text_area("Remarks", placeholder="Any client notes, preference or comments...")
        submitted=st.form_submit_button("➕ Add Lead", type="primary", use_container_width=True)
        if submitted:
            if not phone.strip():
                st.error("Phone number is required."); return None
            if last_follow and not count:
                st.error("Please select the follow-up count."); return None
            return {"Date":inquiry_date,"Name":name.strip(),"Number":phone.strip(),"Email":email.strip(),
                    "Check In Date":check_in,"Check Out Date":check_out,
                    "Booking Confirmation Date":booking_date,"Agent":agent,"Status":status,"Source":source,
                    "Last Follow Up":last_follow,"Follow Up Count":count,"Remarks":remarks.strip()}
    return None

def render_edit_lead_form(r):
    cur_agent=str(r.get("Agent","") or "")
    cur_status=str(r.get("Status","") or "")
    cur_source=str(r.get("Source","") or "")
    cur_count=str(r.get("Follow Up Count","") or "")
    with st.form(f"edit_{r.get('_sheet_row')}"):
        a,b=st.columns(2)
        with a: inquiry_date=st.date_input("Inquiry Date", _parse_date(r.get("Date")), format="DD-MM-YYYY")
        with b: name=st.text_input("Client Name", value=str(r.get("Name","") or ""))
        a,b=st.columns(2)
        with a: phone=st.text_input("Phone Number", value=str(r.get("Number","") or ""))
        with b: email=st.text_input("Email", value=str(r.get("Email","") or ""))
        a,b=st.columns(2)
        with a: check_in=st.date_input("Check In Date", _parse_date(r.get("Check In Date")), format="DD-MM-YYYY")
        with b: check_out=st.date_input("Check Out Date", _parse_date(r.get("Check Out Date")), format="DD-MM-YYYY")
        a,b,c=st.columns(3)
        with a: agent=st.selectbox("Assigned Agent", AGENTS, index=AGENTS.index(cur_agent) if cur_agent in AGENTS else 0)
        with b: status=st.selectbox("Pipeline Status", STATUSES, index=STATUSES.index(cur_status) if cur_status in STATUSES else 0)
        with c: source=st.selectbox("Lead Source", SOURCES, index=SOURCES.index(cur_source) if cur_source in SOURCES else 0)
        booking_date=st.date_input("Booking Confirmation Date", _parse_date(r.get("Booking Confirmation Date")), format="DD-MM-YYYY")
        a,b=st.columns(2)
        with a: last_follow=st.date_input("Last Follow-up Done On", _parse_date(r.get("Last Follow Up")), format="DD-MM-YYYY")
        with b:
            idx=FOLLOW_UP_OPTIONS.index(cur_count)+1 if cur_count in FOLLOW_UP_OPTIONS else 0
            count=st.selectbox("Follow-up Count", [""]+FOLLOW_UP_OPTIONS, index=idx)
        remarks=st.text_area("Remarks", value=str(r.get("Remarks","") or ""))
        submitted=st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
        if submitted:
            if not phone.strip(): st.error("Phone number is required."); return None
            if last_follow and not count: st.error("Please select the follow-up count."); return None
            return {"Date":inquiry_date,"Name":name.strip(),"Number":phone.strip(),"Email":email.strip(),
                    "Check In Date":check_in,"Check Out Date":check_out,
                    "Booking Confirmation Date":booking_date,"Agent":agent,"Status":status,"Source":source,
                    "Last Follow Up":last_follow,"Follow Up Count":count,"Remarks":remarks.strip()}
    return None
