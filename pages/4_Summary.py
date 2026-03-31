import streamlit as st
from utils.db import get_connection

st.set_page_config(page_title="Summary", page_icon="📊", layout="wide")


def fetch_expenses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            id,
            child_name,
            category,
            description,
            amount,
            expense_date,
            paid_by,
            owed_by,
            split_type,
            split_value,
            amount_owed,
            amount_paid,
            status,
            receipt_path,
            notes,
            created_at
        FROM expenses
        ORDER BY expense_date DESC, id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


rows = fetch_expenses()

st.title("📊 Summary Dashboard")
st.write("See totals, balances, and overall reimbursement flow between co-parents.")

if not rows:
    st.info("No expenses found yet. Add an expense first.")
    st.stop()

expenses = []
for row in rows:
    amount = float(row[4] or 0)
    amount_owed = float(row[10] or 0)
    amount_paid = float(row[11] or 0)
    outstanding = round(amount_owed - amount_paid, 2)

    expenses.append(
        {
            "id": row[0],
            "child_name": row[1] or "",
            "category": row[2] or "",
            "description": row[3] or "",
            "amount": amount,
            "expense_date": row[5],
            "paid_by": row[6] or "",
            "owed_by": row[7] or "",
            "split_type": row[8] or "",
            "split_value": float(row[9] or 0),
            "amount_owed": amount_owed,
            "amount_paid": amount_paid,
            "outstanding": outstanding,
            "status": row[12] or "",
            "receipt_path": row[13] or "",
            "notes": row[14] or "",
            "created_at": row[15] or "",
        }
    )

# Overall totals
total_expenses = round(sum(item["amount"] for item in expenses), 2)
total_owed = round(sum(item["amount_owed"] for item in expenses), 2)
total_paid = round(sum(item["amount_paid"] for item in expenses), 2)
total_outstanding = round(sum(item["outstanding"] for item in expenses), 2)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Expenses", f"${total_expenses:,.2f}")
m2.metric("Total Owed", f"${total_owed:,.2f}")
m3.metric("Total Paid", f"${total_paid:,.2f}")
m4.metric("Outstanding", f"${total_outstanding:,.2f}")

st.divider()

# Status breakdown
outstanding_count = sum(1 for item in expenses if item["status"] == "outstanding")
partial_count = sum(1 for item in expenses if item["status"] == "partial")
paid_count = sum(1 for item in expenses if item["status"] == "paid")

s1, s2, s3 = st.columns(3)
s1.metric("Outstanding Items", outstanding_count)
s2.metric("Partial Items", partial_count)
s3.metric("Paid Items", paid_count)

st.divider()

# Per-child summary
child_summary = {}
for item in expenses:
    child = item["child_name"] or "Unknown"
    if child not in child_summary:
        child_summary[child] = {
            "expenses": 0.0,
            "owed": 0.0,
            "paid": 0.0,
            "outstanding": 0.0,
        }

    child_summary[child]["expenses"] += item["amount"]
    child_summary[child]["owed"] += item["amount_owed"]
    child_summary[child]["paid"] += item["amount_paid"]
    child_summary[child]["outstanding"] += item["outstanding"]

st.subheader("By Child")

child_rows = []
for child, values in child_summary.items():
    child_rows.append(
        {
            "Child": child,
            "Total Expenses": f"${values['expenses']:,.2f}",
            "Total Owed": f"${values['owed']:,.2f}",
            "Total Paid": f"${values['paid']:,.2f}",
            "Outstanding": f"${values['outstanding']:,.2f}",
        }
    )

st.dataframe(child_rows, use_container_width=True)

st.divider()

# Parent-to-parent balance summary
pair_summary = {}

for item in expenses:
    pair_key = f"{item['owed_by']} owes {item['paid_by']}"
    if pair_key not in pair_summary:
        pair_summary[pair_key] = {
            "owed": 0.0,
            "paid": 0.0,
            "outstanding": 0.0,
        }

    pair_summary[pair_key]["owed"] += item["amount_owed"]
    pair_summary[pair_key]["paid"] += item["amount_paid"]
    pair_summary[pair_key]["outstanding"] += item["outstanding"]

st.subheader("Who Owes Whom")

pair_rows = []
for pair, values in pair_summary.items():
    pair_rows.append(
        {
            "Relationship": pair,
            "Total Owed": f"${values['owed']:,.2f}",
            "Total Paid": f"${values['paid']:,.2f}",
            "Outstanding": f"${values['outstanding']:,.2f}",
        }
    )

st.dataframe(pair_rows, use_container_width=True)

st.divider()

# Category summary
category_summary = {}

for item in expenses:
    category = item["category"] or "Uncategorized"
    if category not in category_summary:
        category_summary[category] = {
            "amount": 0.0,
            "outstanding": 0.0,
        }

    category_summary[category]["amount"] += item["amount"]
    category_summary[category]["outstanding"] += item["outstanding"]

st.subheader("By Category")

category_rows = []
for category, values in category_summary.items():
    category_rows.append(
        {
            "Category": category,
            "Total Expenses": f"${values['amount']:,.2f}",
            "Outstanding": f"${values['outstanding']:,.2f}",
        }
    )

st.dataframe(category_rows, use_container_width=True)

st.divider()

# Recent expenses
st.subheader("Recent Expenses")

recent_rows = []
for item in expenses[:10]:
    recent_rows.append(
        {
            "Date": item["expense_date"],
            "Child": item["child_name"],
            "Category": item["category"],
            "Description": item["description"],
            "Paid By": item["paid_by"],
            "Owed By": item["owed_by"],
            "Amount": f"${item['amount']:,.2f}",
            "Outstanding": f"${item['outstanding']:,.2f}",
            "Status": item["status"],
        }
    )

st.dataframe(recent_rows, use_container_width=True)