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
            text
            .replace("₹", "")
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
    Format revenue using Indian number formatting.

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

            parts.insert(
                0,
                remaining[-2:]
            )

            remaining = remaining[:-2]

        if remaining:

            parts.insert(
                0,
                remaining
            )

        formatted = ",".join(
            parts + [last_three]
        )

    return f"₹{formatted}"


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
def render_dashboard(df):

    # -----------------------------------------------------
    # Safety check
    # -----------------------------------------------------
    if df is None or df.empty:

        counts = {
            s: 0
            for s in STATUSES
        }

        total = 0

        converted = 0

        rate = 0.0

        revenue = 0.0

    else:

        # -------------------------------------------------
        # Make sure Status exists
        # -------------------------------------------------
        if "Status" not in df.columns:

            status_series = pd.Series(
                "",
                index=df.index
            )

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
            s: int(
                (status_series == s).sum()
            )
            for s in STATUSES
        }

        # -------------------------------------------------
        # Total leads
        # -------------------------------------------------
        total = len(df)

        # -------------------------------------------------
        # Converted leads
        # -------------------------------------------------
        converted = counts.get(
            "Converted",
            0
        )

        # -------------------------------------------------
        # Conversion rate
        # -------------------------------------------------
        rate = (
            converted / total * 100
            if total > 0
            else 0.0
        )

        # -------------------------------------------------
        # Total Revenue
        #
        # Only Converted leads are included.
        # -------------------------------------------------
        revenue = 0.0

        if "Total Amount" in df.columns:

            converted_mask = (
                status_series == "Converted"
            )

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
    revenue_display = _format_revenue(
        revenue
    )

    # =====================================================
    # DASHBOARD METRICS
    # =====================================================
    #
    # ROW 1:
    # TOTAL LEADS
    # QUOTATION GIVEN
    # FOLLOW UP
    # CONVERTED
    # NO AVAILABILITY
    #
    # ROW 2:
    # OUT OF BUDGET
    # GHOSTED
    # NOT INTERESTED
    # TOTAL REVENUE
    # CONVERSION
    # =====================================================

    # -----------------------------------------------------
    # ROW 1
    # -----------------------------------------------------
    row1 = st.columns(5)

    with row1[0]:

        st.metric(
            "TOTAL LEADS",
            total
        )

    with row1[1]:

        st.metric(
            "QUOTATION GIVEN",
            counts.get(
                "Quotation Given",
                0
            )
        )

    with row1[2]:

        st.metric(
            "FOLLOW UP",
            counts.get(
                "Follow up",
                0
            )
        )

    with row1[3]:

        # Converted shows ONLY the number.
        # Example: 22
        st.metric(
            "CONVERTED",
            converted
        )

    with row1[4]:

        st.metric(
            "NO AVAILABILITY",
            counts.get(
                "No Availability",
                0
            )
        )

    # -----------------------------------------------------
    # ROW 2
    # -----------------------------------------------------
    row2 = st.columns(5)

    with row2[0]:

        st.metric(
            "OUT OF BUDGET",
            counts.get(
                "Out of Budget",
                0
            )
        )

    with row2[1]:

        st.metric(
            "GHOSTED",
            counts.get(
                "Ghosted",
                0
            )
        )

    with row2[2]:

        st.metric(
            "NOT INTERESTED",
            counts.get(
                "Not Interested",
                0
            )
        )

    with row2[3]:

        st.metric(
            "TOTAL REVENUE",
            revenue_display
        )

    with row2[4]:

        # Conversion shows ONLY percentage.
        # Example: 4.3%
        st.metric(
            "CONVERSION",
            f"{rate:.1f}%"
        )