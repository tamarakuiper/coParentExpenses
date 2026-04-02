
import sqlite3

DB_PATH = "database/app.db"


def column_exists(conn, table_name, column_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expense_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            household_id INTEGER NOT NULL,
            paid_by_user_id INTEGER NOT NULL,
            received_by_user_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            amount REAL NOT NULL,
            external_reference TEXT,
            note TEXT,
            paid_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (expense_id) REFERENCES expenses(id),
            FOREIGN KEY (household_id) REFERENCES households(id),
            FOREIGN KEY (paid_by_user_id) REFERENCES users(id),
            FOREIGN KEY (received_by_user_id) REFERENCES users(id)
        )
    """)

    # Optional: add payment destination fields to users
    if not column_exists(conn, "users", "venmo_handle"):
        cur.execute("ALTER TABLE users ADD COLUMN venmo_handle TEXT")

    if not column_exists(conn, "users", "zelle_email"):
        cur.execute("ALTER TABLE users ADD COLUMN zelle_email TEXT")

    if not column_exists(conn, "users", "zelle_phone"):
        cur.execute("ALTER TABLE users ADD COLUMN zelle_phone TEXT")

    conn.commit()
    conn.close()
    print("Migration complete.")
    print("Created table: expense_payments")
    print("Added optional user fields: venmo_handle, zelle_email, zelle_phone")


if __name__ == "__main__":
    main()