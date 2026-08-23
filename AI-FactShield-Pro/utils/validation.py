import re


def clean_text(text):
    text = (text or "").strip()
    return re.sub(r"\s+", " ", text)


def valid_email(email):
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email or ""))


def strong_password(password):
    return len(password or "") >= 6
