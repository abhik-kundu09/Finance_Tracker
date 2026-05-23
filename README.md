# Personal Finance Tracker

A web-based personal finance dashboard built with Python and Streamlit.

🚀 **Live demo:** https://financetracker-0921.streamlit.app/

## Features
- Track income and expenses across 10 categories
- Interactive charts — monthly bar, category donut, daily heatmap
- Savings forecast using linear regression (up to 12 months ahead)
- Upload your own CSV or use the built-in sample data generator
- Filter by date range and category; export filtered data as CSV

## Tech stack
Python · Streamlit · Pandas · Plotly · scikit-learn

## Run locally
```bash
git clone  https://github.com/abhik-kundu09/Finance_Tracker.git
cd finance-tracker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## CSV format
If uploading your own data, the CSV must have these columns:
| Column | Example |
|---|---|
| date | 2024-01-15 |
| amount | 45.00 |
| category | Food & Dining |
| type | expense or income |
| description | Grocery run |