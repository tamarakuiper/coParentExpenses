from utils.db import get_connection


def calculate_status(amount_owed, amount_paid):
    amount_owed = round(float(amount_owed or 0), 2)
    amount_paid = round(float(amount_paid or 0), 2)

    if amount_paid <= 0:
        return "outstanding"
    if amount_paid < amount_owed:
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
        ORDER BY e.expense_date ASC, e.id ASC
        """,
        (household_id, user_id),
    )

    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_payments_by_expense(household_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            ep.id,
            ep.expense_id,
            ep.household_id,
            ep.paid_by_user_id,
            ep.received_by_user_id,
            ep.method,
            ep.amount,
            ep.external_reference,
            ep.note,
            ep.paid_at,
            ep.created_at,
            payer.full_name AS payer_name,
            receiver.full_name AS receiver_name
        FROM expense_payments ep
        LEFT JOIN users payer
            ON payer.id = ep.paid_by_user_id
        LEFT JOIN users receiver
            ON receiver.id = ep.received_by_user_id
        WHERE ep.household_id = ?
        ORDER BY ep.paid_at DESC, ep.id DESC
        """,
        (household_id,),
    )

    rows = cursor.fetchall()
    conn.close()

    payments_by_expense = {}
    for row in rows:
        expense_id = row["expense_id"]
        payments_by_expense.setdefault(expense_id, []).append(
            {
                "id": row["id"],
                "expense_id": row["expense_id"],
                "method": row["method"] or "",
                "amount": float(row["amount"] or 0),
                "external_reference": row["external_reference"] or "",
                "note": row["note"] or "",
                "paid_at": row["paid_at"] or "",
                "created_at": row["created_at"] or "",
                "payer_name": row["payer_name"] or "",
                "receiver_name": row["receiver_name"] or "",
            }
        )

    return payments_by_expense


def apply_payment_to_expenses(
    household_id,
    paying_user_id,
    selected_expenses,
    total_payment_amount,
    method,
    external_reference,
    note,
    paid_at,
):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        remaining_payment = round(float(total_payment_amount or 0), 2)

        if remaining_payment <= 0:
            conn.close()
            return False, "Enter a payment amount greater than 0."

        unique_expenses = {}
        for expense in selected_expenses:
            unique_expenses[expense["id"]] = expense

        ordered_expenses = sorted(
            unique_expenses.values(),
            key=lambda x: (x.get("expense_date", ""), x.get("id", 0)),
        )

        allocations = []
        total_applied = 0.0

        for expense in ordered_expenses:
            if remaining_payment <= 0:
                break

            expense_id = expense["id"]
            receiving_user_id = expense["paid_by_user_id"]

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
                continue

            amount_owed = round(float(row["amount_owed"] or 0), 2)
            current_amount_paid = round(float(row["amount_paid"] or 0), 2)
            outstanding = round(amount_owed - current_amount_paid, 2)

            if outstanding <= 0:
                continue

            amount_to_apply = round(min(remaining_payment, outstanding), 2)
            if amount_to_apply <= 0:
                continue

            new_amount_paid = round(current_amount_paid + amount_to_apply, 2)
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
                    amount_to_apply,
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

            allocations.append(
                {
                    "expense_id": expense_id,
                    "description": expense.get("description", "") or "",
                    "child_name": expense.get("child_name", "") or "",
                    "expense_date": expense.get("expense_date", ""),
                    "applied_amount": amount_to_apply,
                    "new_amount_paid": new_amount_paid,
                    "new_status": new_status,
                    "remaining_outstanding": round(amount_owed - new_amount_paid, 2),
                }
            )

            total_applied = round(total_applied + amount_to_apply, 2)
            remaining_payment = round(remaining_payment - amount_to_apply, 2)

        if total_applied <= 0:
            conn.rollback()
            conn.close()
            return False, "No payment could be applied to the selected expenses."

        conn.commit()
        conn.close()

        return True, {
            "allocations": allocations,
            "total_applied": total_applied,
            "unapplied_amount": remaining_payment,
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error recording payment: {e}"