"""
predictor.py
Predict future monthly savings using linear regression on historical data.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from analytics import monthly_summary


def predict_savings(df: pd.DataFrame, months_ahead: int = 3) -> pd.DataFrame:
    """
    Fit a linear trend on monthly savings and extrapolate forward.

    Returns a DataFrame with columns:
        month_str | savings | type ('actual' or 'predicted')
    """
    summary = monthly_summary(df)

    if len(summary) < 2:
        return pd.DataFrame(columns=["month_str", "savings", "type"])

    # Encode month as integer index for regression
    summary = summary.reset_index(drop=True)
    summary["idx"] = np.arange(len(summary))

    X = summary[["idx"]].values
    y = summary["savings"].values

    model = LinearRegression()
    model.fit(X, y)

    # Build forecast rows
    last_idx   = summary["idx"].iloc[-1]
    last_period = summary["month"].iloc[-1]

    future_rows = []
    for i in range(1, months_ahead + 1):
        future_period = last_period + i
        pred_savings  = float(model.predict([[last_idx + i]])[0])
        future_rows.append({
            "month_str": str(future_period),
            "savings":   round(pred_savings, 2),
            "type":      "predicted",
        })

    actual_rows = summary[["month_str", "savings"]].copy()
    actual_rows["type"] = "actual"

    result = pd.concat([actual_rows, pd.DataFrame(future_rows)], ignore_index=True)
    return result


def savings_trend_stats(df: pd.DataFrame) -> dict:
    """Return slope and R² of the savings trend."""
    summary = monthly_summary(df)
    if len(summary) < 2:
        return {"slope": 0.0, "r2": 0.0, "direction": "neutral"}

    X = np.arange(len(summary)).reshape(-1, 1)
    y = summary["savings"].values
    model = LinearRegression().fit(X, y)
    ss_res = np.sum((y - model.predict(X)) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    direction = "up" if model.coef_[0] > 10 else ("down" if model.coef_[0] < -10 else "neutral")
    return {
        "slope":     round(float(model.coef_[0]), 2),
        "r2":        round(r2, 3),
        "direction": direction,
    }
