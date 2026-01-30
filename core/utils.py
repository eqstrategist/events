import re, html
import pandas as pd
from datetime import datetime

# Input validation constants
MAX_TEXT_LENGTH = 500
MAX_CLIENT_LENGTH = 200
MAX_NOTES_LENGTH = 2000

def sanitize_text(text, max_length=MAX_TEXT_LENGTH):
    """Sanitize text input by stripping and limiting length."""
    if text is None:
        return ""
    text = str(text).strip()
    if len(text) > max_length:
        text = text[:max_length]
    return text

def validate_text_input(text, field_name, max_length=MAX_TEXT_LENGTH):
    """Validate text input and return (is_valid, error_message)."""
    if text is None:
        return True, None
    text = str(text)
    if len(text) > max_length:
        return False, f"{field_name} must be less than {max_length} characters."
    # Check for potentially dangerous characters
    if any(c in text for c in ['<script', 'javascript:', 'onerror=', 'onclick=']):
        return False, f"{field_name} contains invalid characters."
    return True, None

def validate_email(email):
    """Validate email format."""
    if not email:
        return False, "Email is required."
    email = str(email).strip().lower()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email format."
    if len(email) > 254:
        return False, "Email too long."
    return True, None

def generate_title(row):
    base = f"{row['Status']}-{row['Source']}-{row['Client']} {row['Course/Description']}"
    medium = row.get('Medium', '')
    trainer = row.get('Trainer Calendar', '')
    location = row.get('Location', '')

    # Include Medium for all event types
    if medium:
        base += f" ({medium})"
    if trainer:
        base += f" {trainer}"
    if location:
        base += f" {location}"

    return str(base).strip()

def trainer_matches(series, trainer):
    pattern = rf"(^|,\s*){re.escape(trainer)}(\s*,|$)"
    return series.fillna("").str.contains(pattern, regex=True)

def get_events_for_day(df_all, date_obj):
    return df_all[pd.to_datetime(df_all['Date']).dt.date == date_obj]

def marked_for_includes(marked_for_value, trainer):
    if pd.isna(marked_for_value):
        return False
    val = str(marked_for_value).strip()
    if val.lower() == 'all':
        return True
    parts = [p.strip() for p in val.split(',') if p.strip()]
    return trainer in parts
