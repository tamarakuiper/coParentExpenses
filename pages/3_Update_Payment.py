import streamlit as st
from utils.db import get_connection

st.set_page_config(page_title="Update Payment", page_icon="💳", layout="wide")


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


def calculate_status(amount_owed, amount_paid):
    if amount_paid <= 0:
        return "outstanding"
    elif amount_paid < amount_owed:
        return "partial"
    return "paid"


def update_payment(expense_id, new_amount_paid, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE expenses
        SET amount_paid = ?, status = ?
        WHERE id = ?
        """,
        (new_amount_paid, new_status, expense_id),
    )
    conn.commit()
    conn.close()


st.title("💳 Update Payment")
st.write("Apply a reimbursement payment to an expense and update its status.")

rows = fetch_expenses()

if not rows:
    st.info("No expenses found yet. Add an expense first.")
    st.stop()

expense_options = []
expense_lookup = {}

for row in rows:
    expense_id = row[0]
    child_name = row[1] or ""
    category = row[2] or ""
    description = row[3] or ""
    amount = float(row[4] or 0)
    expense_date = row[5]
    paid_by = row[6] or ""
    owed_by = row[7] or ""
    amount_owed = float(row[10] or 0)
    amount_paid = float(row[11] or 0)
    status = row[12] or ""
    outstanding = round(amount_owed - amount_paid, 2)

    label = f"#{expense_id} | {expense_date} | {child_name} | {category} | ${amount:,.2f} | Outstanding: ${outstanding:,.2f}"
    expense_options.append(label)
    expense_lookup[label] = {
        "id": expense_id,
        "child_name": child_name,
        "category": category,
        "description": description,
        "amount": amount,
        "expense_date": expense_date,
        "paid_by": paid_by,
        "owed_by": owed_by,
        "amount_owed": amount_owed,
        "amount_paid": amount_paid,
        "status": status,
        "outstanding": outstanding,
    }

selected_label = st.selectbox("Select Expense", expense_options)
selected = expense_lookup[selected_label]

left, right = st.columns(2)

with left:
    st.write(f"**Child:** {selected['child_name']}")
    st.write(f"**Category:** {selected['category']}")
    st.write(f"**Description:** {selected['description'] or '-'}")
    st.write(f"**Expense Date:** {selected['expense_date']}")
    st.write(f"**Paid By:** {selected['paid_by']}")
    st.write(f"**Owed By:** {selected['owed_by']}")

with right:
    st.write(f"**Total Expense:** ${selected['amount']:,.2f}")
    st.write(f"**Amount Owed:** ${selected['amount_owed']:,.2f}")
    st.write(f"**Amount Paid So Far:** ${selected['amount_paid']:,.2f}")
    st.write(f"**Outstanding Balance:** ${selected['outstanding']:,.2f}")
    st.write(f"**Current Status:** {selected['status']}")

st.divider()

payment_amount = st.number_input(
    "Payment Received",
    min_value=0.0,
    max_value=float(selected["outstanding"]) if selected["outstanding"] > 0 else 0.0,
    value=0.0,
    format="%.2f",
)

if st.button("Apply Payment", type="primary"):
    if selected["outstanding"] <= 0:
        st.warning("This expense is already fully paid.")
    elif payment_amount <= 0:
        st.error("Enter a payment amount greater than 0.")
    else:
        new_amount_paid = round(selected["amount_paid"] + payment_amount, 2)
        new_status = calculate_status(selected["amount_owed"], new_amount_paid)
        new_outstanding = round(selected["amount_owed"] - new_amount_paid, 2)

        update_payment(selected["id"], new_amount_paid, new_status)

        st.success("Payment updated successfully.")
        st.info(
            f"New amount paid: ${new_amount_paid:,.2f} | "
            f"New outstanding balance: ${new_outstanding:,.2f} | "
            f"Status: {new_status}"
        )