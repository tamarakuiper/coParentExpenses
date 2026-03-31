import os
from pathlib import Path
from datetime import date
import uuid

import streamlit as st

from utils.db import get_connection

st.set_page_config(page_title="Add Expense", page_icon="🧾", layout="wide")

UPLOAD_DIR = Path("uploads/receipts")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_receipt(uploaded_file):
    if uploaded_file is None:
        return None

    file_ext = Path(uploaded_file.name).suffix
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path).replace("\\", "/")


def insert_expense(
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
        INSERT INTO expenses (
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
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ),
    )

    conn.commit()
    conn.close()


st.title("🧾 Add Expense")
st.write("Record a shared child-related expense, attach a receipt, and track what is owed.")

with st.form("add_expense_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        child_name = st.text_input("Child Name")
        category = st.selectbox(
            "Category",
            [
                "Medical",
                "School",
                "Childcare",
                "Activities",
                "Clothing",
                "Food",
                "Transportation",
                "Other",
            ],
        )
        description = st.text_input("Description")
        amount = st.number_input("Total Amount", min_value=0.0, format="%.2f")
        expense_date = st.date_input("Expense Date", value=date.today())

    with col2:
        paid_by = st.text_input("Paid By")
        owed_by = st.text_input("Owed By")
        split_type = st.selectbox("Split Type", ["percent"])
        split_value = st.number_input(
            "Percent Owed",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            format="%.2f",
        )
        receipt_file = st.file_uploader(
            "Upload Receipt",
            type=["png", "jpg", "jpeg", "pdf"],
        )

    notes = st.text_area("Notes")

    submitted = st.form_submit_button("Save Expense", type="primary")

if submitted:
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
        amount_paid = 0.0
        status = "outstanding"
        receipt_path = save_receipt(receipt_file)

        insert_expense(
            child_name=child_name.strip(),
            category=category,
            description=description.strip(),
            amount=amount,
            expense_date=str(expense_date),
            paid_by=paid_by.strip(),
            owed_by=owed_by.strip(),
            split_type=split_type,
            split_value=split_value,
            amount_owed=amount_owed,
            amount_paid=amount_paid,
            status=status,
            receipt_path=receipt_path,
            notes=notes.strip(),
        )

        st.success("Expense saved successfully.")
        st.info(f"Amount owed: ${amount_owed:.2f}")