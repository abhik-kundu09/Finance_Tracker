"""
data_loader.py
Load, validate, and clean transaction data.
Also provides a sample-data generator so the app works out of the box.
"""

import io
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

from categories import CATEGORIES, INCOME_CATEGORIES


# ── Schema ────────────────────────────────────────────────────────────────────

REQUIRED_COLUMNS = {"date", "amount", "category", "type", "description"}

EXPENSE_RANGES = {
    "Housing":        (800, 1800),
    "Food & Dining":  (10,   120),
    "Transport":      (5,    150),
    "Shopping":       (15,   300),
    "Entertainment":  (10,   100),
    "Health":         (20,   200),
    "Utilities":      (50,   250),
    "Education":      (30,   500),
    "Travel":         (100, 1500),
    "Other":          (5,    200),
}

INCOME_RANGES = {
    "Salary":       (3000, 6000),
    "Freelance":    (200,  1500),
    "Investment":   (50,   800),
    "Gift":         (20,   500),
    "Other Income": (10,   300),
}


# ── Sample generator ──────────────────────────────────────────────────────────

def generate_sample_data(months: int = 6) -> pd.DataFrame:
    """Return a realistic synthetic transaction DataFrame."""
    records = []
    today = date.today()
    start = date(today.year, today.month, 1) - timedelta(days=months * 30)

    current = start
    while current <= today:
        # Monthly salary on the 1st
        if current.day == 1:
            records.append({
                "date": current,
                "amount": round(random.uniform(*INCOME_RANGES["Salary"]), 2),
                "category": "Salary",
                "type": "income",
                "description": "Monthly salary",
            })

        # Housing on the 1st
        if current.day == 1:
            records.append({
                "date": current,
                "amount": round(random.uniform(*EXPENSE_RANGES["Housing"]), 2),
                "category": "Housing",
                "type": "expense",
                "description": "Rent",
            })

        # 0–4 random expenses every day
        for _ in range(random.randint(0, 4)):
            cat = random.choice(CATEGORIES[1:])   # skip Housing
            lo, hi = EXPENSE_RANGES[cat]
            records.append({
                "date": current,
                "amount": round(random.uniform(lo, hi), 2),
                "category": cat,
                "type": "expense",
                "description": f"{cat} purchase",
            })

        # Occasional extra income
        if random.random() < 0.03:
            cat = random.choice(INCOME_CATEGORIES[1:])
            lo, hi = INCOME_RANGES[cat]
            records.append({
                "date": current,
                "amount": round(random.uniform(lo, hi), 2),
                "category": cat,
                "type": "income",
                "description": f"{cat} payment",
            })

        current += timedelta(days=1)

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


# ── CSV loader ────────────────────────────────────────────────────────────────

def load_csv(uploaded_file) -> tuple[pd.DataFrame, list[str]]:
    """
    Parse an uploaded CSV file.
    Returns (dataframe, list_of_warnings).
    Expected columns: date, amount, category, type, description
    """
    warnings: list[str] = []
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as exc:
        return pd.DataFrame(), [f"Could not read file: {exc}"]

    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        return pd.DataFrame(), [f"Missing columns: {', '.join(sorted(missing))}"]

    # Parse dates
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna().sum()
    if bad_dates:
        warnings.append(f"{bad_dates} rows had unparseable dates and were dropped.")
        df = df.dropna(subset=["date"])

    # Parse amounts
    df["amount"] = pd.to_numeric(df["amount"].astype(str).str.replace(r"[^\d.]", "", regex=True), errors="coerce")
    bad_amounts = df["amount"].isna().sum()
    if bad_amounts:
        warnings.append(f"{bad_amounts} rows had invalid amounts and were dropped.")
        df = df.dropna(subset=["amount"])

    df["amount"] = df["amount"].abs()

    # Normalise type column
    df["type"] = df["type"].str.strip().str.lower()
    unknown_types = ~df["type"].isin(["income", "expense"])
    if unknown_types.any():
        warnings.append(f"{unknown_types.sum()} rows had unknown type values; defaulted to 'expense'.")
        df.loc[unknown_types, "type"] = "expense"

    df = df.sort_values("date").reset_index(drop=True)
    return df, warnings


# ── Helpers ───────────────────────────────────────────────────────────────────

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Serialise a DataFrame to UTF-8 CSV bytes for Streamlit download."""
    return df.to_csv(index=False).encode("utf-8")
