import streamlit as st

from utils.auth import require_login
from utils.payments import fetch_expenses_user_owes, apply_payment_to_expenses

current_user = require_login()

st.set_page_config(page_title="Update Payment", page_icon="💳", layout="wide")

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

selected_labels = st.multiselect(
    "Select Expenses",
    options=expense_options,
    default=[],
)

selected_expenses = [expense_lookup[label] for label in selected_labels]

if "payment_success_message" in st.session_state:
    st.success(st.session_state.pop("payment_success_message"))

if selected_expenses:
    st.subheader("Selected Expenses")

    total_selected_outstanding = 0.0

    for selected in selected_expenses:
        total_selected_outstanding += selected["outstanding"]

        with st.container():
            left, right = st.columns(2)

            with left:
                st.write(f"**Expense ID:** {selected['id']}")
                st.write(f"**Child:** {selected['child_name'] or '-'}")
                st.write(f"**Category:** {selected['category'] or '-'}")
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

    st.info(f"Total outstanding across selected expenses: ${total_selected_outstanding:,.2f}")
else:
    st.info("Select one or more expenses to apply a payment.")

st.subheader("Payment Details")

payment_method = st.selectbox(
    "Payment Method",
    ["Venmo", "Zelle", "Cash", "Check", "Other"],
)

if selected_expenses:
    receiver_ids = {expense["paid_by_user_id"] for expense in selected_expenses}

    if len(receiver_ids) == 1:
        first_selected = selected_expenses[0]

        if payment_method == "Venmo":
            if first_selected["venmo_handle"]:
                st.info(
                    f"Send Venmo payment to **{first_selected['receiver_name']}** "
                    f"at **{first_selected['venmo_handle']}**"
                )
            else:
                st.warning("This user has not added a Venmo handle yet.")

        elif payment_method == "Zelle":
            zelle_targets = []
            if first_selected["zelle_email"]:
                zelle_targets.append(f"Email: {first_selected['zelle_email']}")
            if first_selected["zelle_phone"]:
                zelle_targets.append(f"Phone: {first_selected['zelle_phone']}")

            if zelle_targets:
                st.info(
                    f"Send Zelle payment to **{first_selected['receiver_name']}** via "
                    + " | ".join(zelle_targets)
                )
            else:
                st.warning("This user has not added Zelle details yet.")
    else:
        st.warning(
            "You selected expenses owed to different users. Payment instructions may differ by expense."
        )

max_payment = round(sum(expense["outstanding"] for expense in selected_expenses), 2) if selected_expenses else 0.0

payment_amount = st.number_input(
    "Payment Amount",
    min_value=0.0,
    max_value=max_payment if max_payment > 0 else 0.0,
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
    if not selected_expenses:
        st.error("Select at least one expense.")
    elif payment_amount <= 0:
        st.error("Enter a payment amount greater than 0.")
    else:
        ok, result = apply_payment_to_expenses(
            household_id=current_user["household_id"],
            paying_user_id=current_user["user_id"],
            selected_expenses=selected_expenses,
            total_payment_amount=round(payment_amount, 2),
            method=payment_method.lower(),
            external_reference=external_reference.strip(),
            note=payment_note.strip(),
            paid_at=str(paid_at),
        )

        if ok:
            st.session_state["payment_success_message"] = "Payment recorded successfully."
            st.rerun()
            st.write(f"**Total Applied:** ${result['total_applied']:,.2f}")

            if result["unapplied_amount"] > 0:
                st.warning(
                    f"${result['unapplied_amount']:,.2f} could not be applied because the selected "
                    f"expenses were fully covered."
                )

            st.subheader("Applied To")
            for item in result["allocations"]:
                st.write(
                    f"Expense #{item['expense_id']} | "
                    f"{item['expense_date']} | "
                    f"{item['child_name']} | "
                    f"{item['description'] or '-'} | "
                    f"Applied: ${item['applied_amount']:,.2f} | "
                    f"Remaining: ${item['remaining_outstanding']:,.2f} | "
                    f"Status: {item['new_status']}"
                )

            st.rerun()
        else:
            st.error(result)