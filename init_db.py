from utils.schema import ensure_expense_schema
from utils.db import get_connection, DB_PATH


def init_db():
    print(f"Database path: {DB_PATH}")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    print("Tables:", [row["name"] for row in cursor.fetchall()])

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name='expenses'
    """)

    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM expenses")
        print("Expense count:", cursor.fetchone()[0])
    else:
        print("Expenses table does not exist.")

    # existing init_db code continues below...


    ensure_expense_schema()
    print("Database initialized.")
    print("Expense, payment, and allocation schema is ready.")


if __name__ == "__main__":
    init_db()
