import pandas as pd
import streamlit as st

from config import STATUSES


def _amount(value):
    try:
        text = str(value).replace(",", "").replace("₹", "").strip()
        if not text or text.lower() in {"nan", "none", "nat"}:
            return 0.0
        return float(text)
    except (ValueError, TypeError):
        return 0.0


def render_dashboard(df):
    counts = {
        s: int((df["Status"].astype(str).str.strip() == s).sum())
        for s in STATUSES
    }

    total = len(df)
    converted = counts.get("Converted", 0)
    rate = converted / total * 100 if total else 0

    if "Total Amount" in df.columns:
        converted_mask = df["Status"].astype(str).str.strip() == "Converted"
        revenue = df.loc[converted_mask, "Total Amount"].apply(_amount).sum()
    else:
        revenue = 0.0

    c = st.columns(7)
    c[0].metric("TOTAL LEADS", total)
    c[1].metric("FOLLOW UP", counts.get("Follow up", 0))
    c[2].metric("QUOTATION GIVEN", counts.get("Quotation Given", 0))
    c[3].metric("CONVERTED", converted, f"{rate:.1f}%")
    c[4].metric("NO AVAILABILITY", counts.get("No Availability", 0))
    c[5].metric("OUT OF BUDGET", counts.get("Out of Budget", 0))
    c[6].metric("TOTAL REVENUE", f"₹{revenue:,.2f}")
