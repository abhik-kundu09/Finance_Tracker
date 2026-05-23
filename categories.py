"""
categories.py
Expense category definitions and colour mapping.
"""

CATEGORIES = [
    "Housing",
    "Food & Dining",
    "Transport",
    "Shopping",
    "Entertainment",
    "Health",
    "Utilities",
    "Education",
    "Travel",
    "Other",
]

INCOME_CATEGORIES = ["Salary", "Freelance", "Investment", "Gift", "Other Income"]

# Plotly-friendly colour palette — one per category
CATEGORY_COLORS = {
    "Housing":        "#5B8FF9",
    "Food & Dining":  "#5AD8A6",
    "Transport":      "#F6BD16",
    "Shopping":       "#E86452",
    "Entertainment":  "#6DC8EC",
    "Health":         "#945FB9",
    "Utilities":      "#FF9845",
    "Education":      "#1E9493",
    "Travel":         "#FF99C3",
    "Other":          "#B8B8B8",
    "Salary":         "#2EC25B",
    "Freelance":      "#00C2D4",
    "Investment":     "#7B61FF",
    "Gift":           "#FF6B6B",
    "Other Income":   "#96CEB4",
}
