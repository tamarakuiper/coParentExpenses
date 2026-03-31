import uuid
from pathlib import Path
from datetime import datetime

import streamlit as st

from utils.db import get_connection
from utils.receipt_utils import render_receipt
from utils.auth import require_login

st.set_page_config(page_title="Ledger", page_icon="📒", layout="wide")

current_user = require_login()

UPLOAD_DIR = Path("uploads/receipts")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
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

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path).replace("\\", "/")


def fetch_household_members(household_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            u.id,
            u.full_name,
            u.email,
            hm.role
        FROM household_members hm
        JOIN users u
            ON u.id = hm.user_id
        WHERE hm.household_id = ?
        ORDER BY u.full_name ASC
        """,
        (household_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


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
            paid_by_user_id,
            owed_by_user_id,
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


def update_expense(
    expense_id,
    household_id,
    current_user_id,
    child_name,
    category,
    description,
    amount,
    expense_date,
    paid_by_name,
    owed_by_name,
    paid_by_user_id,
    owed_by_user_id,
    split_type,
    split_value,
    amount_owed,
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
            updated_by_user_id = ?,
            child_name = ?,
            category = ?,
            description = ?,
            amount = ?,
            expense_date = ?,
            paid_by = ?,
            owed_by = ?,
            paid_by_user_id = ?,
            owed_by_user_id = ?,
            split_type = ?,
            split_value = ?,
            amount_owed = ?,
            status = ?,
            receipt_path = ?,
            notes = ?
        WHERE id = ?
          AND household_id = ?
          AND created_by_user_id = ?
        """,
        (
            current_user_id,
            child_name,
            category,
            description,
            amount,
            expense_date,
            paid_by_name,
            owed_by_name,
            paid_by_user_id,
            owed_by_user_id,
            split_type,
            split_value,
            amount_owed,
            status,
            receipt_path,
            notes,
            expense_id,
            household_id,
            current_user_id,
        ),
    )

    changed = cursor.rowcount
    conn.commit()
    conn.close()
    return changed > 0


st.title("📒 Expense Ledger")
st.write("View all shared expenses, payment status, and outstanding balances.")

members = fetch_household_members(current_user["household_id"])

if not members:
    st.error("No household members found.")
    st.stop()

member_options = {
    f"{member['full_name']} ({member['email']})": {
        "id": member["id"],
        "name": member["full_name"],
        "email": member["email"],
        "role": member["role"],
    }
    for member in members
}
member_labels = list(member_options.keys())

rows = fetch_expenses(current_user["household_id"])

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
            "household_id": row["household_id"],
            "created_by_user_id": row["created_by_user_id"],
            "updated_by_user_id": row["updated_by_user_id"],
            "child_name": row["child_name"] or "",
            "category": row["category"] or "",
            "description": row["description"] or "",
            "amount": amount,
            "expense_date": row["expense_date"],
            "paid_by": row["paid_by"] or "",
            "owed_by": row["owed_by"] or "",
            "paid_by_user_id": row["paid_by_user_id"],
            "owed_by_user_id": row["owed_by_user_id"],
            "split_type": row["split_type"] or "percent",
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
            "Entered By You": "Yes" if item["created_by_user_id"] == current_user["user_id"] else "No",
            "Receipt File": receipt_name,
        }
    )

st.subheader("Saved Expenses")
st.dataframe(display_rows, use_container_width=True)

st.subheader("Expense Details")
st.caption("You can edit only expenses that you entered.")

for item in filtered:
    can_edit = item["created_by_user_id"] == current_user["user_id"]

    with st.expander(f"#{item['id']} • {item['expense_date']} • {item['category']} • ${item['amount']:,.2f}"):
        left, right = st.columns(2)

        with left:
            st.write(f"**Child:** {item['child_name']}")
            st.write(f"**Description:** {item['description'] or '-'}")
            st.write(f"**Paid By:** {item['paid_by']}")
            st.write(f"**Owed By:** {item['owed_by']}")
            st.write(f"**Status:** {item['status']}")
            st.write(f"**Entered By You:** {'Yes' if can_edit else 'No'}")

        with right:
            st.write(f"**Total Amount:** ${item['amount']:,.2f}")
            st.write(f"**Amount Owed:** ${item['amount_owed']:,.2f}")
            st.write(f"**Amount Paid:** ${item['amount_paid']:,.2f}")
            st.write(f"**Outstanding:** ${item['outstanding']:,.2f}")
            st.write(f"**Split:** {item['split_value']:,.2f}%")

        st.write(f"**Notes:** {item['notes'] or '-'}")
        render_receipt(item["receipt_path"], key_prefix=f"ledger_{item['id']}")

        if not can_edit:
            st.info("Only the person who entered this expense can edit it.")
            continue

        st.markdown("---")
        st.markdown("### Edit Expense")

        paid_by_default = 0
        owed_by_default = 0

        for idx, label in enumerate(member_labels):
            if member_options[label]["id"] == item["paid_by_user_id"]:
                paid_by_default = idx
            if member_options[label]["id"] == item["owed_by_user_id"]:
                owed_by_default = idx

        try:
            default_category_index = CATEGORIES.index(item["category"])
        except ValueError:
            default_category_index = 0

        try:
            default_date = datetime.strptime(item["expense_date"], "%Y-%m-%d").date()
        except Exception:
            default_date = datetime.today().date()

        with st.form(f"edit_expense_{item['id']}"):
            c1, c2 = st.columns(2)

            with c1:
                edit_child_name = st.text_input("Child Name", value=item["child_name"])
                edit_category = st.selectbox(
                    "Category",
                    CATEGORIES,
                    index=default_category_index,
                    key=f"category_{item['id']}",
                )
                edit_description = st.text_input("Description", value=item["description"])
                edit_amount = st.number_input(
                    "Total Amount",
                    min_value=0.0,
                    value=float(item["amount"]),
                    format="%.2f",
                    key=f"amount_{item['id']}",
                )
                edit_expense_date = st.date_input(
                    "Expense Date",
                    value=default_date,
                    key=f"date_{item['id']}",
                )

            with c2:
                edit_paid_by_label = st.selectbox(
                    "Paid By",
                    member_labels,
                    index=paid_by_default,
                    key=f"paid_by_{item['id']}",
                )
                edit_owed_by_label = st.selectbox(
                    "Owed By",
                    member_labels,
                    index=owed_by_default,
                    key=f"owed_by_{item['id']}",
                )
                edit_split_type = st.selectbox(
                    "Split Type",
                    ["percent"],
                    index=0,
                    key=f"split_type_{item['id']}",
                )
                edit_split_value = st.number_input(
                    "Percent Owed",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(item["split_value"]),
                    format="%.2f",
                    key=f"split_{item['id']}",
                )
                new_receipt = st.file_uploader(
                    "Replace Receipt (optional)",
                    type=["png", "jpg", "jpeg", "pdf"],
                    key=f"receipt_{item['id']}",
                )

            edit_notes = st.text_area("Notes", value=item["notes"], key=f"notes_{item['id']}")
            submitted = st.form_submit_button("Save Changes", type="primary")

        if submitted:
            paid_by_member = member_options[edit_paid_by_label]
            owed_by_member = member_options[edit_owed_by_label]

            if not edit_child_name.strip():
                st.error("Child Name is required.")
            elif edit_amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                new_receipt_path = item["receipt_path"]
                if new_receipt is not None:
                    new_receipt_path = save_receipt(new_receipt)

                new_amount_owed = round(edit_amount * (edit_split_value / 100), 2)
                existing_amount_paid = float(item["amount_paid"] or 0)

                if existing_amount_paid <= 0:
                    new_status = "outstanding"
                elif existing_amount_paid < new_amount_owed:
                    new_status = "partial"
                else:
                    new_status = "paid"

                ok = update_expense(
                    expense_id=item["id"],
                    household_id=current_user["household_id"],
                    current_user_id=current_user["user_id"],
                    child_name=edit_child_name.strip(),
                    category=edit_category,
                    description=edit_description.strip(),
                    amount=round(edit_amount, 2),
                    expense_date=str(edit_expense_date),
                    paid_by_name=paid_by_member["name"],
                    owed_by_name=owed_by_member["name"],
                    paid_by_user_id=paid_by_member["id"],
                    owed_by_user_id=owed_by_member["id"],
                    split_type=edit_split_type,
                    split_value=round(edit_split_value, 2),
                    amount_owed=new_amount_owed,
                    status=new_status,
                    receipt_path=new_receipt_path,
                    notes=edit_notes.strip(),
                )

                if ok:
                    st.success("Expense updated successfully.")
                    st.rerun()
                else:
                    st.error("You can only edit expenses that you entered.")