import streamlit as st
from utils.db import get_connection
from utils.receipt_utils import render_receipt
from pathlib import Path


st.set_page_config(page_title="Ledger", page_icon="📒", layout="wide")


def fetch_expenses():
    conn = get_connection()
    conn.row_factory = None
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


st.title("📒 Expense Ledger")
st.write("View all shared expenses, payment status, and outstanding balances.")

rows = fetch_expenses()

if not rows:
    st.info("No expenses saved yet. Go to Add Expense and create your first entry.")
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
            "created_at": row[15] if len(row) > 15 else "",
        }
    )

total_amount = round(sum(item.get("amount", 0) for item in expenses), 2)
total_owed = round(sum(item.get("amount_owed", 0) for item in expenses), 2)
total_paid = round(sum(item.get("amount_paid", 0) for item in expenses), 2)
total_outstanding = round(sum(item.get("outstanding", 0) for item in expenses), 2)

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
st.dataframe(display_rows, width="stretch")

st.subheader("Expense Details")
st.caption("Open an expense below to preview or download its receipt.")

for item in filtered:
    with st.expander(f"#{item['id']} • {item['expense_date']} • {item['category']} • ${item['amount']:,.2f}"):
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