PAGE_TITLE = "2026 Lead Conversion Board"
PAGE_ICON = "📈"
SHEET_NAME = "Lead tracker"
WORKSHEET_NAME = "Sheet 2026"

STATUSES = [
    "Follow up",
    "Quotation Given",
    "Converted",
    "No Availability",
    "Out of Budget",
    "Past Dated",
    "Not Interested",
]

AGENTS = ["Shweta", "Mayank", "Punya"]
SOURCES = ["Whatsapp business", "Eazotel", "Meta Park Cafe", "Meta EBC", "AiSensy", "Call", "Custom"]
FOLLOW_UP_OPTIONS = [f"Follow up {i}" for i in range(1, 21)]

HEADERS = [
    "DATE", "NAME", "NUMBER", "EMAIL", "CHECK IN DATE", "CHECK OUT DATE",
    "BOOKING CONFIRMATION DATE", "Agent", "Status", "Source",
    "Last follow us done on", "Follow Up Count", "Remarks", "Total Amount"
]

HEADER_ALIASES = {
    "DATE": "Date",
    "NAME": "Name",
    "NUMBER": "Number",
    "PHONE": "Number",
    "PHONE NUMBER": "Number",
    "EMAIL": "Email",
    "CHECK IN": "Check In Date",
    "CHECK IN DATE": "Check In Date",
    "CHECK OUT": "Check Out Date",
    "CHECK OUT DATE": "Check Out Date",
    "BOOKING NOTE": "Booking Confirmation Date",
    "BOOKING CONFIRMATION NOTE": "Booking Confirmation Date",
    "BOOKING CONFIRMATION DATE": "Booking Confirmation Date",
    "AGENT": "Agent",
    "STATUS": "Status",
    "SOURCE": "Source",
    "LAST FOLLOW UP": "Last Follow Up",
    "LAST FOLLOW UP DONE ON": "Last Follow Up",
    "LAST FOLLOW US DONE ON": "Last Follow Up",
    "FOLLOW UP COUNT": "Follow Up Count",
    "REMARKS": "Remarks",
    "TOTAL AMOUNT": "Total Amount",
    "AMOUNT": "Total Amount",
    "REVENUE": "Total Amount",
}
