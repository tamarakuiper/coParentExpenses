import streamlit as st

from utils.auth import require_login
from utils.db import get_connection

st.set_page_config(page_title="Summary", page_icon="📊", layout="wide")

current_user = require_login()

def render_sidebar_nav():
    with st.sidebar:
        st.page_link("Home.py", label="Home")
        st.page_link("pages/01_Summary.py", label="Summary")
        st.page_link("pages/02_Add_Expense.py", label="Add Expense")
        st.page_link("pages/05_Update_Payment.py", label="Update Payment")
        st.page_link("pages/04_Ledger.py", label="Ledger")
        st.page_link("pages/07_Profile.py", label="Profile")

render_sidebar_nav()


def fetch_expenses(household_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            household_id,
            created_by_user_id,
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
        WHERE household_id = ?
        ORDER BY expense_date DESC, id DESC
        """,
        (household_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


household_id = current_user.get("household_id")
if not household_id:
    st.error("Your account is not linked to a household yet.")
    st.stop()

rows = fetch_expenses(household_id)

st.title("📊 Summary Dashboard")
st.write("See totals, balances, and overall reimbursement flow between co-parents.")
st.caption(
    f"Signed in as {current_user['user_name']} • "
    f"Household: {current_user.get('household_name', 'Unknown Household')}"
)

if not rows:
    st.info("No expenses found yet. Add an expense first.")
    st.stop()

expenses = []
for row in rows:
    amount = float(row["amount"] or 0)
    amount_owed = float(row["amount_owed"] or 0)
    amount_paid = float(row["amount_paid"] or 0)
    outstanding = round(amount_owed - amount_paid, 2)

    expenses.append(
        {
            "id": row["id"],
            "child_name": row["child_name"] or "",
            "category": row["category"] or "",
            "description": row["description"] or "",
            "amount": amount,
            "expense_date": row["expense_date"],
            "paid_by": row["paid_by"] or "",
            "owed_by": row["owed_by"] or "",
            "split_type": row["split_type"] or "",
            "split_value": float(row["split_value"] or 0),
            "amount_owed": amount_owed,
            "amount_paid": amount_paid,
            "outstanding": outstanding,
            "status": row["status"] or "",
            "receipt_path": row["receipt_path"] or "",
            "notes": row["notes"] or "",
            "created_at": row["created_at"] or "",
        }
    )

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

outstanding_count = sum(1 for item in expenses if item["status"] == "outstanding")
partial_count = sum(1 for item in expenses if item["status"] == "partial")
paid_count = sum(1 for item in expenses if item["status"] == "paid")

s1, s2, s3 = st.columns(3)
s1.metric("Outstanding Items", outstanding_count)
s2.metric("Partial Items", partial_count)
s3.metric("Paid Items", paid_count)

st.divider()

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
