import streamlit as st

from utils.auth import require_login
from utils.db import get_connection

st.set_page_config(page_title="Update Payment", page_icon="💳", layout="wide")

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
            child_name,
            category,
            description,
            amount,
            expense_date,
            paid_by,
            owed_by,
            amount_owed,
            amount_paid,
            status
        FROM expenses
        WHERE household_id = ?
        ORDER BY expense_date DESC, id DESC
        """,
        (household_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def calculate_status(amount_owed, amount_paid):
    if amount_paid <= 0:
        return "outstanding"
    if amount_paid < amount_owed:
        return "partial"
    return "paid"


def update_payment(expense_id, household_id, current_user_id, new_amount_paid, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE expenses
        SET
            amount_paid = ?,
            status = ?,
            updated_by_user_id = ?
        WHERE id = ?
          AND household_id = ?
          AND created_by_user_id = ?
        """,
        (
            new_amount_paid,
            new_status,
            current_user_id,
            expense_id,
            household_id,
            current_user_id,
        ),
    )
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


household_id = current_user.get("household_id")
if not household_id:
    st.error("Your account is not linked to a household yet.")
    st.stop()

st.title("💳 Update Payment")
st.write("Apply a reimbursement payment to one of your household expenses.")
st.caption(
    f"Signed in as {current_user['user_name']} • "
    f"Household: {current_user.get('household_name', 'Unknown Household')}"
)

rows = fetch_expenses(household_id)

if not rows:
    st.info("No expenses found yet. Add an expense first.")
    st.stop()

expense_options = []
expense_lookup = {}

for row in rows:
    amount = float(row["amount"] or 0)
    amount_owed = float(row["amount_owed"] or 0)
    amount_paid = float(row["amount_paid"] or 0)
    outstanding = round(amount_owed - amount_paid, 2)

    label = (
        f"#{row['id']} | {row['expense_date']} | {row['child_name'] or ''} | "
        f"{row['category'] or ''} | ${amount:,.2f} | Outstanding: ${outstanding:,.2f}"
    )
    expense_options.append(label)
    expense_lookup[label] = {
        "id": row["id"],
        "created_by_user_id": row["created_by_user_id"],
        "child_name": row["child_name"] or "",
        "category": row["category"] or "",
        "description": row["description"] or "",
        "amount": amount,
        "expense_date": row["expense_date"],
        "paid_by": row["paid_by"] or "",
        "owed_by": row["owed_by"] or "",
        "amount_owed": amount_owed,
        "amount_paid": amount_paid,
        "status": row["status"] or "",
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

if selected["created_by_user_id"] != current_user["user_id"]:
    st.warning("Only the person who created this expense can update the payment on it.")
    st.stop()

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
        if new_amount_paid > selected["amount_owed"]:
            new_amount_paid = selected["amount_owed"]

        new_status = calculate_status(selected["amount_owed"], new_amount_paid)
        new_outstanding = round(selected["amount_owed"] - new_amount_paid, 2)

        updated = update_payment(
            expense_id=selected["id"],
            household_id=household_id,
            current_user_id=current_user["user_id"],
            new_amount_paid=new_amount_paid,
            new_status=new_status,
        )

        if updated:
            st.success("Payment updated successfully.")
            st.info(
                f"New amount paid: ${new_amount_paid:,.2f} | "
                f"New outstanding balance: ${new_outstanding:,.2f} | "
                f"Status: {new_status}"
            )
            st.rerun()
        else:
            st.error("Update failed. You may not have permission to update this expense.")
