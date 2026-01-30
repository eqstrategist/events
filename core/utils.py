import re, html
import pandas as pd
from datetime import datetime

def generate_title(row):
    base = f"{row['Status']}-{row['Source']}-{row['Client']} {row['Course/Description']}"
    if row.get('Type') == 'W':
        base += f" ({row.get('Medium','')}) {row.get('Trainer Calendar','')} {row.get('Location','')}"
    elif row.get('Type') == 'M':
        base += f" {row.get('Trainer Calendar','')} {row.get('Location','')}"
    else:
        base += f" {row.get('Trainer Calendar','')}"
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
