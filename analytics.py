"""
analytics.py
All Pandas aggregation logic — KPIs, monthly summaries, category breakdowns.
"""

import pandas as pd


# ── KPI helpers ───────────────────────────────────────────────────────────────

def compute_kpis(df: pd.DataFrame) -> dict:
    """Return a dict of headline KPI values from a filtered DataFrame."""
    income_df  = df[df["type"] == "income"]
    expense_df = df[df["type"] == "expense"]

    total_income   = income_df["amount"].sum()
    total_expenses = expense_df["amount"].sum()
    net_savings    = total_income - total_expenses
    savings_rate   = (net_savings / total_income * 100) if total_income > 0 else 0.0
    avg_daily_spend = (
        expense_df.groupby(expense_df["date"].dt.date)["amount"].sum().mean()
        if not expense_df.empty else 0.0
    )

    return {
        "total_income":     round(total_income, 2),
        "total_expenses":   round(total_expenses, 2),
        "net_savings":      round(net_savings, 2),
        "savings_rate":     round(savings_rate, 1),
        "avg_daily_spend":  round(avg_daily_spend, 2),
        "num_transactions": len(df),
    }


# ── Monthly summaries ─────────────────────────────────────────────────────────

def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame with one row per month:
    month | income | expenses | savings
    """
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")

    income  = df[df["type"] == "income" ].groupby("month")["amount"].sum()
    expense = df[df["type"] == "expense"].groupby("month")["amount"].sum()

    summary = pd.DataFrame({"income": income, "expenses": expense}).fillna(0)
    summary["savings"] = summary["income"] - summary["expenses"]
    summary = summary.reset_index()
    summary["month_str"] = summary["month"].astype(str)
    return summary.sort_values("month")


# ── Category breakdowns ───────────────────────────────────────────────────────

def category_breakdown(df: pd.DataFrame, tx_type: str = "expense") -> pd.DataFrame:
    """Return (category, total, pct) sorted by total descending."""
    sub = df[df["type"] == tx_type].copy()
    if sub.empty:
        return pd.DataFrame(columns=["category", "total", "pct"])

    totals = sub.groupby("category")["amount"].sum().reset_index()
    totals.columns = ["category", "total"]
    totals["pct"] = (totals["total"] / totals["total"].sum() * 100).round(1)
    return totals.sort_values("total", ascending=False).reset_index(drop=True)


# ── Daily spending ────────────────────────────────────────────────────────────

def daily_spending(df: pd.DataFrame) -> pd.DataFrame:
    """Return daily expense totals with day-of-week annotation."""
    exp = df[df["type"] == "expense"].copy()
    daily = exp.groupby(exp["date"].dt.date)["amount"].sum().reset_index()
    daily.columns = ["date", "amount"]
    daily["date"] = pd.to_datetime(daily["date"])
    daily["dow"] = daily["date"].dt.day_name()
    return daily.sort_values("date")


# ── Top expenses ──────────────────────────────────────────────────────────────

def top_transactions(df: pd.DataFrame, n: int = 10, tx_type: str = "expense") -> pd.DataFrame:
    """Return the n largest transactions of a given type."""
    sub = df[df["type"] == tx_type].copy()
    return sub.nlargest(n, "amount")[["date", "description", "category", "amount"]].reset_index(drop=True)
