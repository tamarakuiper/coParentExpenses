import uuid
from pathlib import Path
from datetime import datetime, date

import streamlit as st

from utils.auth import require_login
from utils.db import get_connection
from utils.receipt_utils import render_receipt


st.set_page_config(page_title="Edit or Delete Expense", page_icon="✏️", layout="wide")

current_user = require_login()

UPLOAD_DIR = Path("uploads/receipts")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def fetch_expenses():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
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
            created_at,
            created_by_user_id
        FROM expenses
        ORDER BY expense_date DESC, id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def save_receipt(uploaded_file):
    if uploaded_file is None:
        return None

    extension = Path(uploaded_file.name).suffix
    filename = f"{uuid.uuid4().hex}{extension}"
    filepath = UPLOAD_DIR / filename

    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(filepath).replace("\\", "/")


def calculate_status(amount_owed, amount_paid):
    if amount_paid <= 0:
        return "outstanding"
    if amount_paid < amount_owed:
        return "partial"
    return "paid"


def parse_expense_date(value):
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def update_expense(
    expense_id,
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
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE expenses
        SET
            child_name = ?,
            category = ?,
            description = ?,
            amount = ?,
            expense_date = ?,
            paid_by = ?,
            owed_by = ?,
            split_type = ?,
            split_value = ?,
            amount_owed = ?,
            amount_paid = ?,
            status = ?,
            receipt_path = ?,
            notes = ?
        WHERE id = ?
          AND created_by_user_id = ?
        """,
        (
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
            expense_id,
            created_by_user_id,
        ),
    )
    updated_count = cursor.rowcount
    conn.commit()
    conn.close()
    return updated_count


def delete_expense(expense_id, created_by_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM expenses
        WHERE id = ?
          AND created_by_user_id = ?
        """,
        (expense_id, created_by_user_id),
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


st.title("✏️ Edit or Delete Expense")
st.write("Update an existing expense or remove it from the ledger.")

if st.session_state.get("expense_saved"):
    st.success(st.session_state.pop("expense_saved"))

if st.session_state.get("expense_deleted"):
    st.success(st.session_state.pop("expense_deleted"))

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
    split_type = row[8] or "percent"
    split_value = float(row[9] or 50)
    amount_owed = float(row[10] or 0)
    amount_paid = float(row[11] or 0)
    status = row[12] or "outstanding"
    receipt_path = row[13] or ""
    notes = row[14] or ""
    created_at = row[15] or ""
    created_by_user_id = row[16]

    label = f"#{expense_id} | {expense_date} | {child_name} | {category} | ${amount:,.2f}"
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
        "split_type": split_type,
        "split_value": split_value,
        "amount_owed": amount_owed,
        "amount_paid": amount_paid,
        "status": status,
        "receipt_path": receipt_path,
        "notes": notes,
        "created_at": created_at,
        "created_by_user_id": created_by_user_id,
    }

selected_label = st.selectbox("Select Expense", expense_options)
selected = expense_lookup[selected_label]

if selected["created_by_user_id"] != current_user["user_id"]:
    st.error("You can only edit or delete expenses you created.")
    st.stop()

st.subheader("Current Record")
c1, c2, c3 = st.columns(3)
c1.write(f"**ID:** {selected['id']}")
c1.write(f"**Child:** {selected['child_name']}")
c1.write(f"**Category:** {selected['category']}")
c2.write(f"**Amount:** ${selected['amount']:,.2f}")
c2.write(f"**Amount Owed:** ${selected['amount_owed']:,.2f}")
c2.write(f"**Amount Paid:** ${selected['amount_paid']:,.2f}")
c3.write(f"**Status:** {selected['status']}")
c3.write(f"**Date:** {selected['expense_date']}")
c3.write(f"**Receipt:** {'Yes' if selected['receipt_path'] else 'No'}")

st.divider()

categories = [
    "Medical",
    "School",
    "Childcare",
    "Activities",
    "Clothing",
    "Food",
    "Transportation",
    "Other",
]

with st.form("edit_expense_form"):
    left, right = st.columns(2)

    with left:
        child_name = st.text_input("Child Name", value=selected["child_name"])
        category = st.selectbox(
            "Category",
            categories,
            index=categories.index(selected["category"]) if selected["category"] in categories else 0,
        )
        description = st.text_input("Description", value=selected["description"])
        amount = st.number_input(
            "Total Amount",
            min_value=0.0,
            value=float(selected["amount"]),
            format="%.2f",
        )

        parsed_date = parse_expense_date(selected["expense_date"])
        expense_date = st.date_input("Expense Date", value=parsed_date)

    with right:
        paid_by = st.text_input("Paid By", value=selected["paid_by"])
        owed_by = st.text_input("Owed By", value=selected["owed_by"])
        split_type = st.selectbox("Split Type", ["percent"], index=0)
        split_value = st.number_input(
            "Percent Owed",
            min_value=0.0,
            max_value=100.0,
            value=float(selected["split_value"]),
            format="%.2f",
        )
        amount_paid = st.number_input(
            "Amount Paid So Far",
            min_value=0.0,
            value=float(selected["amount_paid"]),
            format="%.2f",
        )
        receipt_file = st.file_uploader(
            "Replace Receipt (optional)",
            type=["png", "jpg", "jpeg", "pdf"],
        )

    notes = st.text_area("Notes", value=selected["notes"])

    save_changes = st.form_submit_button("Save Changes", type="primary")

if save_changes:
    if not child_name.strip():
        st.error("Child Name is required.")
    elif not paid_by.strip():
        st.error("Paid By is required.")
    elif not owed_by.strip():
        st.error("Owed By is required.")
    elif amount <= 0:
        st.error("Amount must be greater than 0.")
    else:
        amount_owed = round(amount * (split_value / 100), 2)
        amount_paid = round(amount_paid, 2)

        if amount_paid > amount_owed:
            amount_paid = amount_owed

        status = calculate_status(amount_owed, amount_paid)

        new_receipt_path = save_receipt(receipt_file)
        receipt_path = new_receipt_path if new_receipt_path else selected["receipt_path"]

        updated_count = update_expense(
            expense_id=selected["id"],
            created_by_user_id=current_user["user_id"],
            child_name=child_name.strip(),
            category=category,
            description=description.strip(),
            amount=round(amount, 2),
            expense_date=str(expense_date),
            paid_by=paid_by.strip(),
            owed_by=owed_by.strip(),
            split_type=split_type,
            split_value=round(split_value, 2),
            amount_owed=amount_owed,
            amount_paid=amount_paid,
            status=status,
            receipt_path=receipt_path,
            notes=notes.strip(),
        )

        if updated_count == 0:
            st.error("No expense was updated. Check that this expense belongs to your account.")
        else:
            st.session_state["expense_saved"] = (
                f"Expense updated successfully. Amount owed: ${amount_owed:,.2f} | "
                f"Amount paid: ${amount_paid:,.2f} | Status: {status}"
            )
            st.rerun()

st.divider()
st.subheader("Delete Expense")

confirm_delete = st.checkbox("I understand this will permanently delete the selected expense.")

if st.button("Delete Expense"):
    if not confirm_delete:
        st.warning("Check the confirmation box before deleting.")
    else:
        deleted_count = delete_expense(selected["id"], current_user["user_id"])
        if deleted_count == 0:
            st.error("No expense was deleted. Check that this expense belongs to your account.")
        else:
            st.session_state["expense_deleted"] = "Expense deleted successfully."
            st.rerun()

st.subheader("Current Receipt")
render_receipt(selected["receipt_path"], key_prefix=f"edit_{selected['id']}")
