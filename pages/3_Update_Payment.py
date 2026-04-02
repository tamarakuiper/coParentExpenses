import streamlit as st
from utils.db import get_connection
from utils.auth import require_login

current_user = require_login()

st.set_page_config(page_title="Update Payment", page_icon="💳", layout="wide")


def calculate_status(amount_owed, amount_paid):
    if amount_paid <= 0:
        return "outstanding"
    elif amount_paid < amount_owed:
        return "partial"
    return "paid"


def fetch_expenses_user_owes(household_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            e.id,
            e.child_name,
            e.category,
            e.description,
            e.amount,
            e.expense_date,
            e.paid_by,
            e.owed_by,
            e.paid_by_user_id,
            e.owed_by_user_id,
            e.split_type,
            e.split_value,
            e.amount_owed,
            e.amount_paid,
            e.status,
            e.receipt_path,
            e.notes,
            e.created_at,
            u.full_name AS receiver_name,
            u.venmo_handle,
            u.zelle_email,
            u.zelle_phone
        FROM expenses e
        LEFT JOIN users u
            ON u.id = e.paid_by_user_id
        WHERE e.household_id = ?
          AND e.owed_by_user_id = ?
          AND e.amount_owed > e.amount_paid
        ORDER BY e.expense_date DESC, e.id DESC
        """,
        (household_id, user_id),
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def apply_payment(
    expense_id,
    household_id,
    paying_user_id,
    receiving_user_id,
    amount,
    method,
    external_reference,
    note,
    paid_at,
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT amount_owed, amount_paid
        FROM expenses
        WHERE id = ?
          AND household_id = ?
          AND owed_by_user_id = ?
        LIMIT 1
        """,
        (expense_id, household_id, paying_user_id),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, "Expense not found or you are not allowed to update it."

    amount_owed = float(row["amount_owed"] or 0)
    current_amount_paid = float(row["amount_paid"] or 0)
    new_amount_paid = round(current_amount_paid + amount, 2)

    if new_amount_paid > amount_owed:
        conn.close()
        return False, "Payment exceeds the outstanding amount."

    new_status = calculate_status(amount_owed, new_amount_paid)

    cursor.execute(
        """
        INSERT INTO expense_payments (
            expense_id,
            household_id,
            paid_by_user_id,
            received_by_user_id,
            method,
            amount,
            external_reference,
            note,
            paid_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            expense_id,
            household_id,
            paying_user_id,
            receiving_user_id,
            method,
            amount,
            external_reference,
            note,
            paid_at,
        ),
    )

    cursor.execute(
        """
        UPDATE expenses
        SET amount_paid = ?, status = ?, updated_by_user_id = ?
        WHERE id = ?
          AND household_id = ?
          AND owed_by_user_id = ?
        """,
        (
            new_amount_paid,
            new_status,
            paying_user_id,
            expense_id,
            household_id,
            paying_user_id,
        ),
    )

    conn.commit()
    conn.close()

    outstanding = round(amount_owed - new_amount_paid, 2)
    return True, {
        "amount_paid": new_amount_paid,
        "status": new_status,
        "outstanding": outstanding,
    }


st.title("💳 Update Payment")
st.write("Record a reimbursement payment for expenses you owe.")

rows = fetch_expenses_user_owes(current_user["household_id"], current_user["user_id"])

if not rows:
    st.info("You do not currently owe any outstanding expense payments.")
    st.stop()

expense_options = []
expense_lookup = {}

for row in rows:
    expense_id = row["id"]
    child_name = row["child_name"] or ""
    category = row["category"] or ""
    description = row["description"] or ""
    amount = float(row["amount"] or 0)
    expense_date = row["expense_date"]
    paid_by = row["paid_by"] or ""
    owed_by = row["owed_by"] or ""
    amount_owed = float(row["amount_owed"] or 0)
    amount_paid = float(row["amount_paid"] or 0)
    status = row["status"] or ""
    outstanding = round(amount_owed - amount_paid, 2)

    label = (
        f"#{expense_id} | {expense_date} | {child_name} | {category} | "
        f"${amount:,.2f} | Outstanding: ${outstanding:,.2f}"
    )

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
        "paid_by_user_id": row["paid_by_user_id"],
        "owed_by_user_id": row["owed_by_user_id"],
        "amount_owed": amount_owed,
        "amount_paid": amount_paid,
        "status": status,
        "outstanding": outstanding,
        "receiver_name": row["receiver_name"] or paid_by,
        "venmo_handle": row["venmo_handle"] or "",
        "zelle_email": row["zelle_email"] or "",
        "zelle_phone": row["zelle_phone"] or "",
    }

selected_label = st.selectbox("Select Expense", expense_options)
selected = expense_lookup[selected_label]

left, right = st.columns(2)

with left:
    st.write(f"**Child:** {selected['child_name']}")
    st.write(f"**Category:** {selected['category']}")
    st.write(f"**Description:** {selected['description'] or '-'}")
    st.write(f"**Expense Date:** {selected['expense_date']}")
    st.write(f"**You Owe:** {selected['paid_by']}")
    st.write(f"**Current Status:** {selected['status']}")

with right:
    st.write(f"**Total Expense:** ${selected['amount']:,.2f}")
    st.write(f"**Amount Owed:** ${selected['amount_owed']:,.2f}")
    st.write(f"**Amount Paid So Far:** ${selected['amount_paid']:,.2f}")
    st.write(f"**Outstanding Balance:** ${selected['outstanding']:,.2f}")

st.divider()
st.subheader("Payment Details")

payment_method = st.selectbox(
    "Payment Method",
    ["Venmo", "Zelle", "Cash", "Check", "Other"],
)

if payment_method == "Venmo":
    if selected["venmo_handle"]:
        st.info(f"Send Venmo payment to **{selected['receiver_name']}** at **{selected['venmo_handle']}**")
    else:
        st.warning("This user has not added a Venmo handle yet.")
elif payment_method == "Zelle":
    zelle_targets = []
    if selected["zelle_email"]:
        zelle_targets.append(f"Email: {selected['zelle_email']}")
    if selected["zelle_phone"]:
        zelle_targets.append(f"Phone: {selected['zelle_phone']}")

    if zelle_targets:
        st.info(f"Send Zelle payment to **{selected['receiver_name']}** via " + " | ".join(zelle_targets))
    else:
        st.warning("This user has not added Zelle details yet.")

payment_amount = st.number_input(
    "Payment Amount",
    min_value=0.0,
    max_value=float(selected["outstanding"]) if selected["outstanding"] > 0 else 0.0,
    value=0.0,
    format="%.2f",
)

external_reference = st.text_input(
    "Reference / Confirmation (optional)",
    placeholder="Example: Venmo note, bank confirmation, check number",
)

payment_note = st.text_area(
    "Payment Note (optional)",
    placeholder="Optional note about this payment",
)

paid_at = st.date_input("Payment Date")

if st.button("Record Payment", type="primary"):
    if selected["outstanding"] <= 0:
        st.warning("This expense is already fully paid.")
    elif payment_amount <= 0:
        st.error("Enter a payment amount greater than 0.")
    else:
        ok, result = apply_payment(
            expense_id=selected["id"],
            household_id=current_user["household_id"],
            paying_user_id=current_user["user_id"],
            receiving_user_id=selected["paid_by_user_id"],
            amount=round(payment_amount, 2),
            method=payment_method.lower(),
            external_reference=external_reference.strip(),
            note=payment_note.strip(),
            paid_at=str(paid_at),
        )

        if ok:
            st.success("Payment recorded successfully.")
            st.info(
                f"New amount paid: ${result['amount_paid']:,.2f} | "
                f"Outstanding balance: ${result['outstanding']:,.2f} | "
                f"Status: {result['status']}"
            )
            st.rerun()
        else:
            st.error(result)