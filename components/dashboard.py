import pandas as pd
import streamlit as st

from config import STATUSES


# ---------------------------------------------------------
# Amount helper
# ---------------------------------------------------------
def _amount(value):
    """
    Convert different amount formats into a float.

    Supports values such as:
        25000
        "25000"
        "25,000"
        "₹25,000"
        "₹ 25,000"
        "25000.50"
        "₹25,000.50"
    """
    try:
        if value is None:
            return 0.0

        # Handle pandas NaN / NaT
        if pd.isna(value):
            return 0.0

        text = str(value).strip()

        if not text or text.lower() in {
            "nan",
            "none",
            "nat",
            "null",
            "-",
        }:
            return 0.0

        # Remove currency symbol and commas
        text = (
            text.replace("₹", "")
            .replace(",", "")
            .replace(" ", "")
        )

        # Remove optional INR text
        if text.upper().startswith("INR"):
            text = text[3:]

        return float(text)

    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------
# Revenue formatter
# ---------------------------------------------------------
def _format_revenue(value):
    """
    Format revenue without Streamlit truncating the value.

    Examples:
        5000       -> ₹5,000
        250000     -> ₹2,50,000
        1250000    -> ₹12,50,000
        10000000   -> ₹1,00,00,000
    """

    try:
        value = float(value)
    except (ValueError, TypeError):
        value = 0.0

    # Indian number formatting
    amount = round(value)

    if amount < 1000:
        formatted = str(amount)
    else:
        number = str(amount)
        last_three = number[-3:]
        remaining = number[:-3]

        parts = []

        while len(remaining) > 2:
            parts.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        if remaining:
            parts.insert(0, remaining)

        formatted = ",".join(parts + [last_three])

    return f"₹{formatted}"


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
def render_dashboard(df):

    # -----------------------------------------------------
    # Safety check
    # -----------------------------------------------------
    if df is None or df.empty:
        counts = {s: 0 for s in STATUSES}
        total = 0
        converted = 0
        rate = 0.0
        revenue = 0.0

    else:

        # Make sure Status exists
        if "Status" not in df.columns:
            status_series = pd.Series("", index=df.index)
        else:
            status_series = (
                df["Status"]
                .fillna("")
                .astype(str)
                .str.strip()
            )

        # -------------------------------------------------
        # Status counts
        # -------------------------------------------------
        counts = {
            s: int((status_series == s).sum())
            for s in STATUSES
        }

        total = len(df)

        converted = counts.get("Converted", 0)

        rate = (
            converted / total * 100
            if total > 0
            else 0.0
        )

        # -------------------------------------------------
        # Total Revenue
        # Only Converted leads are included
        # -------------------------------------------------
        revenue = 0.0

        if "Total Amount" in df.columns:

            converted_mask = status_series == "Converted"

            if converted_mask.any():

                revenue = (
                    df.loc[
                        converted_mask,
                        "Total Amount"
                    ]
                    .apply(_amount)
                    .sum()
                )

    # -----------------------------------------------------
    # Revenue display
    # -----------------------------------------------------
    revenue_display = _format_revenue(revenue)

    # -----------------------------------------------------
    # Dashboard metrics
    # -----------------------------------------------------
    c = st.columns(7)

    c[0].metric(
        "TOTAL LEADS",
        total
    )

    c[1].metric(
        "QUOTATION GIVEN",
        counts.get("Quotation Given", 0)
    )

    c[2].metric(
        "FOLLOW UP",
        counts.get("Follow up", 0)
    )

    # Show converted leads as:
    #   CONVERTED
    #   9 / 97
    #   ↑ 9.3%
    # where 9 is converted leads and 97 is total leads.
    c[3].metric(
        "CONVERTED",
        f"{converted} / {total}",
        f"{rate:.1f}%"
    )

    c[4].metric(
        "NO AVAILABILITY",
        counts.get("No Availability", 0)
    )

    c[5].metric(
        "OUT OF BUDGET",
        counts.get("Out of Budget", 0)
    )

    c[6].metric(
        "TOTAL REVENUE",
        revenue_display
    )