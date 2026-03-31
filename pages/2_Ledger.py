from pathlib import Path

import streamlit as st

from utils.auth import require_login
from utils.db import get_connection
from utils.receipt_utils import render_receipt

st.set_page_config(page_title="Ledger", page_icon="📒", layout="wide")

current_user = require_login()


def fetch_expenses(household_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            household_id,
            created_by_user_id,
            updated_by_user_id,
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

st.title("📒 Expense Ledger")
st.write("View all shared expenses, payment status, and outstanding balances.")
st.caption(
    f"Signed in as {current_user['user_name']} • "
    f"Household: {current_user.get('household_name', 'Unknown Household')}"
)

rows = fetch_expenses(household_id)

if not rows:
    st.info("No expenses saved yet. Go to Add Expense and create your first entry.")
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

total_amount = round(sum(item["amount"] for item in expenses), 2)
total_owed = round(sum(item["amount_owed"] for item in expenses), 2)
total_paid = round(sum(item["amount_paid"] for item in expenses), 2)
total_outstanding = round(sum(item["outstanding"] for item in expenses), 2)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Expenses", f"${total_amount:,.2f}")
m2.metric("Total Owed", f"${total_owed:,.2f}")
m3.metric("Total Paid", f"${total_paid:,.2f}")
m4.metric("Outstanding", f"${total_outstanding:,.2f}")

st.divider()

child_options = sorted({item["child_name"] for item in expenses if item["child_name"]})
category_options = sorted({item["category"] for item in expenses if item["category"]})
status_options = sorted({item["status"] for item in expenses if item["status"]})

f1, f2, f3 = st.columns(3)

with f1:
    selected_child = st.selectbox("Filter by Child", ["All"] + child_options)

with f2:
    selected_category = st.selectbox("Filter by Category", ["All"] + category_options)

with f3:
    selected_status = st.selectbox("Filter by Status", ["All"] + status_options)

filtered = expenses

if selected_child != "All":
    filtered = [item for item in filtered if item["child_name"] == selected_child]

if selected_category != "All":
    filtered = [item for item in filtered if item["category"] == selected_category]

if selected_status != "All":
    filtered = [item for item in filtered if item["status"] == selected_status]

if not filtered:
    st.warning("No expenses match the selected filters.")
    st.stop()

display_rows = []
for item in filtered:
    receipt_name = Path(item["receipt_path"]).name if item["receipt_path"] else ""
    receipt_status = "View below" if item["receipt_path"] else "No receipt"

    display_rows.append(
        {
            "ID": item["id"],
            "Date": item["expense_date"],
            "Child": item["child_name"],
            "Category": item["category"],
            "Description": item["description"],
            "Amount": f"${item['amount']:,.2f}",
            "Paid By": item["paid_by"],
            "Owed By": item["owed_by"],
            "Amount Owed": f"${item['amount_owed']:,.2f}",
            "Amount Paid": f"${item['amount_paid']:,.2f}",
            "Outstanding": f"${item['outstanding']:,.2f}",
            "Status": item["status"],
            "Receipt": receipt_status,
            "Receipt File": receipt_name,
        }
    )

st.subheader("Saved Expenses")
st.dataframe(display_rows, use_container_width=True)

st.subheader("Expense Details")
st.caption("Open an expense below to preview or download its receipt.")

for item in filtered:
    header = (
        f"#{item['id']} • {item['expense_date']} • "
        f"{item['category']} • ${item['amount']:,.2f}"
    )
    with st.expander(header):
        left, right = st.columns(2)

        with left:
            st.write(f"**Child:** {item['child_name']}")
            st.write(f"**Description:** {item['description'] or '-'}")
            st.write(f"**Paid By:** {item['paid_by']}")
            st.write(f"**Owed By:** {item['owed_by']}")
            st.write(f"**Status:** {item['status']}")

        with right:
            st.write(f"**Total Amount:** ${item['amount']:,.2f}")
            st.write(f"**Amount Owed:** ${item['amount_owed']:,.2f}")
            st.write(f"**Amount Paid:** ${item['amount_paid']:,.2f}")
            st.write(f"**Outstanding:** ${item['outstanding']:,.2f}")
            st.write(f"**Split:** {item['split_value']:,.2f}%")

        st.write(f"**Notes:** {item['notes'] or '-'}")
        render_receipt(item["receipt_path"], key_prefix=f"ledger_{item['id']}")
