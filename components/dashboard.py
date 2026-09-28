import streamlit as st
from config import STATUSES

def render_dashboard(df):
    counts={s:int((df["Status"].astype(str).str.strip()==s).sum()) for s in STATUSES}
    total=len(df); converted=counts.get("Converted",0)
    rate=converted/total*100 if total else 0
    c=st.columns(6)
    c[0].metric("TOTAL LEADS",total)
    c[1].metric("FOLLOW UP",counts.get("Follow up",0))
    c[2].metric("QUOTATION GIVEN",counts.get("Quotation Given",0))
    c[3].metric("CONVERTED",converted,f"{rate:.1f}%")
    c[4].metric("NO AVAILABILITY",counts.get("No Availability",0))
    c[5].metric("OUT OF BUDGET",counts.get("Out of Budget",0))
