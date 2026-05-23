"""
app.py
Personal Finance Tracker — Streamlit dashboard.

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

from categories import CATEGORIES, INCOME_CATEGORIES, CATEGORY_COLORS
from data_loader import generate_sample_data, load_csv, df_to_csv_bytes
from analytics  import compute_kpis, monthly_summary, category_breakdown, daily_spending, top_transactions
from predictor  import predict_savings, savings_trend_stats


# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  .metric-card {
      background: var(--background-color, #f8f9fa);
      border: 1px solid rgba(0,0,0,0.08);
      border-radius: 12px;
      padding: 16px 20px;
      text-align: center;
  }
  .metric-positive { color: #2EC25B; font-weight: 600; }
  .metric-negative { color: #E86452; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ── Session state: data ───────────────────────────────────────────────────────

if "df" not in st.session_state:
    st.session_state.df = generate_sample_data(months=6)


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("💰 Finance Tracker")
    st.divider()

    # ── Data source ──────────────────────────────────────────────────────────
    st.subheader("Data source")
    data_source = st.radio("", ["Use sample data", "Upload CSV"], label_visibility="collapsed")

    if data_source == "Upload CSV":
        uploaded = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")
        if uploaded:
            df_uploaded, warnings = load_csv(uploaded)
            if df_uploaded.empty:
                for w in warnings:
                    st.error(w)
            else:
                st.session_state.df = df_uploaded
                for w in warnings:
                    st.warning(w)
                st.success(f"Loaded {len(df_uploaded):,} transactions.")

        st.caption("Expected columns: date, amount, category, type, description")
        with st.expander("CSV template"):
            template = pd.DataFrame([{
                "date": "2024-01-15", "amount": 45.00,
                "category": "Food & Dining", "type": "expense",
                "description": "Grocery run",
            }, {
                "date": "2024-01-01", "amount": 3500.00,
                "category": "Salary", "type": "income",
                "description": "Monthly salary",
            }])
            st.dataframe(template, hide_index=True)
            st.download_button("Download template", df_to_csv_bytes(template),
                               "finance_template.csv", "text/csv")
    else:
        if st.button("🔄 Regenerate sample data"):
            st.session_state.df = generate_sample_data(months=6)
            st.rerun()

    st.divider()

    # ── Add transaction ───────────────────────────────────────────────────────
    st.subheader("Add transaction")
    with st.form("add_tx"):
        tx_date  = st.date_input("Date", value=date.today())
        tx_type  = st.selectbox("Type", ["expense", "income"])
        tx_cat   = st.selectbox(
            "Category",
            CATEGORIES if tx_type == "expense" else INCOME_CATEGORIES,
        )
        tx_amt   = st.number_input("Amount (€)", min_value=0.01, step=0.01, format="%.2f")
        tx_desc  = st.text_input("Description")
        if st.form_submit_button("Add ➕"):
            new_row = pd.DataFrame([{
                "date":        pd.Timestamp(tx_date),
                "amount":      tx_amt,
                "category":    tx_cat,
                "type":        tx_type,
                "description": tx_desc or tx_cat,
            }])
            st.session_state.df = pd.concat(
                [st.session_state.df, new_row], ignore_index=True
            ).sort_values("date").reset_index(drop=True)
            st.success("Transaction added!")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    st.subheader("Filters")
    df_all = st.session_state.df
    min_date = df_all["date"].min().date()
    max_date = df_all["date"].max().date()

    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    all_cats  = sorted(df_all["category"].unique().tolist())
    sel_cats  = st.multiselect("Categories", all_cats, default=all_cats)
    sel_types = st.multiselect("Type", ["expense", "income"], default=["expense", "income"])

    st.divider()
    st.download_button(
        "⬇ Export filtered CSV",
        df_to_csv_bytes(df_all),
        "transactions.csv",
        "text/csv",
    )


# ── Apply filters ─────────────────────────────────────────────────────────────

df = df_all.copy()
if len(date_range) == 2:
    start_d, end_d = date_range
    df = df[(df["date"].dt.date >= start_d) & (df["date"].dt.date <= end_d)]
df = df[df["category"].isin(sel_cats) & df["type"].isin(sel_types)]


# ── Main content ──────────────────────────────────────────────────────────────

st.title("Personal Finance Dashboard")

if df.empty:
    st.warning("No transactions match your filters.")
    st.stop()

kpis = compute_kpis(df)

# KPI row
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("💵 Total Income",    f"€{kpis['total_income']:,.0f}")
with c2:
    st.metric("💸 Total Expenses",  f"€{kpis['total_expenses']:,.0f}")
with c3:
    delta_color = "normal" if kpis["net_savings"] >= 0 else "inverse"
    st.metric("🏦 Net Savings", f"€{kpis['net_savings']:,.0f}", delta_color=delta_color)
with c4:
    st.metric("📊 Savings Rate",    f"{kpis['savings_rate']}%")
with c5:
    st.metric("🛒 Avg Daily Spend", f"€{kpis['avg_daily_spend']:,.2f}")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_overview, tab_trends, tab_predict, tab_table = st.tabs(
    ["📊 Overview", "📈 Trends", "🔮 Prediction", "📋 Transactions"]
)


# ────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ────────────────────────────────────────────────────────────────────────────
with tab_overview:
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("Monthly income vs expenses")
        monthly = monthly_summary(df)
        if not monthly.empty:
            fig = go.Figure()
            fig.add_bar(x=monthly["month_str"], y=monthly["income"],
                        name="Income",   marker_color="#2EC25B")
            fig.add_bar(x=monthly["month_str"], y=monthly["expenses"],
                        name="Expenses", marker_color="#E86452")
            fig.add_scatter(x=monthly["month_str"], y=monthly["savings"],
                            mode="lines+markers", name="Savings",
                            line=dict(color="#5B8FF9", width=2),
                            marker=dict(size=6))
            fig.update_layout(
                barmode="group", height=350,
                margin=dict(l=0, r=0, t=10, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for monthly chart.")

    with col_right:
        st.subheader("Spending by category")
        cat_df = category_breakdown(df, "expense")
        if not cat_df.empty:
            colors = [CATEGORY_COLORS.get(c, "#B8B8B8") for c in cat_df["category"]]
            fig2 = px.pie(
                cat_df, values="total", names="category",
                color="category",
                color_discrete_map=CATEGORY_COLORS,
                hole=0.45,
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(height=350, showlegend=False,
                               margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Daily spending pattern")
    daily_df = daily_spending(df)
    if not daily_df.empty:
        fig3 = px.bar(
            daily_df, x="date", y="amount",
            color="dow",
            labels={"amount": "Amount (€)", "date": "Date", "dow": "Day"},
        )
        fig3.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=40),
                           showlegend=True)
        st.plotly_chart(fig3, use_container_width=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 2 — TRENDS
# ────────────────────────────────────────────────────────────────────────────
with tab_trends:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Cumulative savings over time")
        exp_df = df[df["type"] == "expense"].groupby(df["date"].dt.date)["amount"].sum()
        inc_df = df[df["type"] == "income" ].groupby(df["date"].dt.date)["amount"].sum()
        daily_net = (inc_df - exp_df).fillna(0).cumsum().reset_index()
        daily_net.columns = ["date", "cumulative_savings"]
        daily_net["date"] = pd.to_datetime(daily_net["date"])

        fig4 = px.area(daily_net, x="date", y="cumulative_savings",
                       labels={"cumulative_savings": "Cumulative savings (€)"},
                       color_discrete_sequence=["#5B8FF9"])
        fig4.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=40))
        st.plotly_chart(fig4, use_container_width=True)

    with col_b:
        st.subheader("Category spend over time")
        exp_monthly = (
            df[df["type"] == "expense"]
            .assign(month=lambda d: d["date"].dt.to_period("M").astype(str))
            .groupby(["month", "category"])["amount"]
            .sum()
            .reset_index()
        )
        if not exp_monthly.empty:
            fig5 = px.line(
                exp_monthly, x="month", y="amount", color="category",
                color_discrete_map=CATEGORY_COLORS,
                markers=True,
                labels={"amount": "Amount (€)", "month": "Month"},
            )
            fig5.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=40))
            st.plotly_chart(fig5, use_container_width=True)

    st.subheader("Top 10 expenses")
    top_df = top_transactions(df, n=10, tx_type="expense")
    top_df["amount"] = top_df["amount"].map("€{:,.2f}".format)
    top_df["date"]   = top_df["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(top_df, use_container_width=True, hide_index=True)


# ────────────────────────────────────────────────────────────────────────────
# TAB 3 — PREDICTION
# ────────────────────────────────────────────────────────────────────────────
with tab_predict:
    st.subheader("Savings forecast")
    months_ahead = st.slider("Months to forecast", min_value=1, max_value=12, value=3)

    trend_stats = savings_trend_stats(df)
    forecast_df = predict_savings(df, months_ahead=months_ahead)

    if forecast_df.empty:
        st.info("Need at least 2 months of data to generate a forecast.")
    else:
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            direction_label = {"up": "📈 Improving", "down": "📉 Declining", "neutral": "➡️ Stable"}
            st.metric("Savings trend", direction_label.get(trend_stats["direction"], "—"))
        with col_stat2:
            st.metric("Monthly change", f"€{trend_stats['slope']:+,.2f}")
        with col_stat3:
            st.metric("Model fit (R²)", f"{trend_stats['r2']:.2f}")

        # Split actual vs predicted for colouring
        actual_df    = forecast_df[forecast_df["type"] == "actual"]
        predicted_df = forecast_df[forecast_df["type"] == "predicted"]

        fig6 = go.Figure()
        fig6.add_scatter(
            x=actual_df["month_str"], y=actual_df["savings"],
            mode="lines+markers", name="Actual",
            line=dict(color="#5B8FF9", width=2), marker=dict(size=7),
        )
        fig6.add_scatter(
            x=predicted_df["month_str"], y=predicted_df["savings"],
            mode="lines+markers", name="Forecast",
            line=dict(color="#F6BD16", width=2, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
        )
        fig6.add_shape(
            type="line",
            x0=actual_df["month_str"].iloc[-1], x1=predicted_df["month_str"].iloc[0],
            y0=actual_df["savings"].iloc[-1],   y1=predicted_df["savings"].iloc[0],
            line=dict(color="gray", width=1, dash="dot"),
        )
        fig6.add_hline(y=0, line_color="red", line_dash="dot", opacity=0.4)
        fig6.update_layout(
            height=380, margin=dict(l=0, r=0, t=10, b=40),
            yaxis_title="Savings (€)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig6, use_container_width=True)

        st.subheader("Forecast table")
        forecast_table = forecast_df.copy()
        forecast_table["savings"] = forecast_table["savings"].map("€{:,.2f}".format)
        st.dataframe(
            forecast_table.rename(columns={"month_str": "Month", "savings": "Savings", "type": "Type"}),
            use_container_width=True, hide_index=True,
        )


# ────────────────────────────────────────────────────────────────────────────
# TAB 4 — TRANSACTIONS TABLE
# ────────────────────────────────────────────────────────────────────────────
with tab_table:
    st.subheader(f"All transactions ({len(df):,})")
    display_df = df.copy()
    display_df["date"]   = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df["amount"] = display_df["amount"].map("€{:,.2f}".format)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇ Download this view as CSV",
        df_to_csv_bytes(df),
        "filtered_transactions.csv",
        "text/csv",
    )
