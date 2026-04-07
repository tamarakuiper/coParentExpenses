import uuid
from datetime import date
from pathlib import Path

import streamlit as st

from utils.auth import require_login
from utils.db import get_connection
from utils.household_admin import fetch_household_members

st.set_page_config(page_title="Add Expense", page_icon="🧾", layout="wide")

current_user = require_login()

UPLOAD_DIR = Path("uploads/receipts")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_OPTIONS = [
    "Medical",
    "School",
    "Childcare",
    "Activities",
    "Clothing",
    "Food",
    "Transportation",
    "Other",
]


def save_receipt(uploaded_file):
    if uploaded_file is None:
        return None

    file_ext = Path(uploaded_file.name).suffix
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as file_handle:
        file_handle.write(uploaded_file.getbuffer())

    return str(file_path).replace("\\", "/")


def insert_expense(
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
    paid_by_user_id,
    owed_by_user_id,
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
            paid_by_user_id,
            owed_by_user_id,
            split_type,
            split_value,
            amount_owed,
            amount_paid,
            status,
            receipt_path,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
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
            paid_by_user_id,
            owed_by_user_id,
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


household_id = current_user.get("household_id")
if not household_id:
    st.error("Your account is not linked to a household yet.")
    st.stop()

members = fetch_household_members(
    household_id,
    current_user["user_id"],
)

if not members:
    st.error("No household members were found for your account.")
    st.stop()

member_options = {
    f"{member['full_name']} ({member['email']})": {
        "id": member["user_id"],
        "name": member["full_name"],
        "email": member["email"],
        "role": member["role"],
    }
    for member in members
}
member_labels = list(member_options.keys())

default_paid_by_index = 0
for i, label in enumerate(member_labels):
    if member_options[label]["id"] == current_user["user_id"]:
        default_paid_by_index = i
        break

default_owed_by_index = default_paid_by_index
if len(member_labels) > 1:
    for i, label in enumerate(member_labels):
        if member_options[label]["id"] != current_user["user_id"]:
            default_owed_by_index = i
            break

st.title("🧾 Add Expense")
st.write("Record a shared child-related expense for your household.")
st.caption(
    f"Signed in as {current_user['user_name']} • "
    f"Household: {current_user.get('household_name', 'Unknown Household')}"
)

with st.form("add_expense_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        child_name = st.text_input("Child Name")
        category = st.selectbox("Category", CATEGORY_OPTIONS)
        description = st.text_input("Description")
        amount = st.number_input("Total Amount", min_value=0.0, format="%.2f")
        expense_date = st.date_input("Expense Date", value=date.today())

    with col2:
        paid_by_label = st.selectbox(
            "Paid By",
            member_labels,
            index=default_paid_by_index,
        )
        owed_by_label = st.selectbox(
            "Owed By",
            member_labels,
            index=default_owed_by_index,
        )
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
    paid_by_member = member_options[paid_by_label]
    owed_by_member = member_options[owed_by_label]

    if not child_name.strip():
        st.error("Child Name is required.")
    elif amount <= 0:
        st.error("Amount must be greater than 0.")
    else:
        amount_owed = round(amount * (split_value / 100), 2)
        amount_paid = 0.0
        status = "outstanding"
        receipt_path = save_receipt(receipt_file)

        insert_expense(
            household_id=household_id,
            created_by_user_id=current_user["user_id"],
            updated_by_user_id=current_user["user_id"],
            child_name=child_name.strip(),
            category=category,
            description=description.strip(),
            amount=round(amount, 2),
            expense_date=str(expense_date),
            paid_by=paid_by_member["name"],
            owed_by=owed_by_member["name"],
            paid_by_user_id=paid_by_member["id"],
            owed_by_user_id=owed_by_member["id"],
            split_type=split_type,
            split_value=round(split_value, 2),
            amount_owed=amount_owed,
            amount_paid=amount_paid,
            status=status,
            receipt_path=receipt_path,
            notes=notes.strip(),
        )

        st.success("Expense saved successfully.")
        st.info(f"Amount owed: ${amount_owed:,.2f}")