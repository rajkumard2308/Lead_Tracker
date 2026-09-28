import re
def validate_phone(phone):
    cleaned=re.sub(r"[\s\-()]","",str(phone).strip())
    return (True,"") if re.fullmatch(r"\+?\d{10,13}",cleaned) else (False,"Enter a valid phone number.")
def validate_email(email):
    email=str(email).strip()
    return (True,"") if not email or re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$",email) else (False,"Enter a valid email address.")
