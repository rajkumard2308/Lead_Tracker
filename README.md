# 2026 Lead Conversion Board

This version fixes the Windows PyArrow/DLL crash by removing `st.dataframe()` from analytics.

Changes:
- Agent dropdown: Shweta, Mayank, Puneya
- Booking Confirmation Date calendar
- Pipeline Status includes Past Dated
- Lead Source includes Call
- Referral and Walk-in removed
- Last Follow-up Done On calendar
- Follow-up Count: Follow up 1 through Follow up 20
- Google Sheet automatically adds Booking Confirmation Date and Follow Up Count columns if missing

Run:
`pip install -r requirements.txt`
`streamlit run app.py`
