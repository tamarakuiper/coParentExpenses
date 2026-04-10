from utils.db import get_connection


def ensure_column(cursor, table_name, column_name, definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row["name"] for row in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_allocations (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   payment_id INTEGER NOT NULL,
                   expense_id INTEGER NOT NULL,
                   allocated_amount REAL NOT NULL,
                   created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                   FOREIGN KEY (payment_id) REFERENCES expense_payments(id),
                   FOREIGN KEY (expense_id) REFERENCES expenses(id)
                )
                   
                   """)
    print([row["name"] for row in cursor.fetchall()])

    conn.commit()
    conn.close()

    print("Database initialized.")
    print("Users are ready for payment allocations.")


if __name__ == "__main__":
    init_db()