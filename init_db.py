from utils.schema import ensure_expense_schema


def init_db():
    ensure_expense_schema()
    print("Database initialized.")
    print("Expense, payment, and allocation schema is ready.")


if __name__ == "__main__":
    init_db()
