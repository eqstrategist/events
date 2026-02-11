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

def _safe_str(value):
    """Convert a value to string, treating NaN/None as empty string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)

def generate_title(row):
    status = _safe_str(row.get('Status', ''))
    source = _safe_str(row.get('Source', ''))
    client = _safe_str(row.get('Client', ''))
    course = _safe_str(row.get('Course/Description', ''))
    medium = _safe_str(row.get('Medium', ''))
    trainer = _safe_str(row.get('Trainer Calendar', ''))
    location = _safe_str(row.get('Location', ''))

    base = f"{status}-{source}-{client} {course}"

    if medium:
        base += f" ({medium})"
    if trainer:
        base += f" {trainer}"
    if location:
        base += f" {location}"

    return base.strip()

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
