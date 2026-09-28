from datetime import date, datetime
def format_date(value):
    if value is None or value=="": return ""
    return value.strftime("%d %b %Y") if isinstance(value,(date,datetime)) else str(value)
def safe_text(value):
    if value is None: return ""
    s=str(value).strip()
    return "" if s.lower() in {"nan","nat","none"} else s
