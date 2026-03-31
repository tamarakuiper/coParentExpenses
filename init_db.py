from utils.db import get_connection

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        paid_by TEXT NOT NULL,
        owed_by TEXT NOT NULL,
        split_type TEXT DEFAULT 'equal',
        split_value REAL DEFAULT 50,
        amount_owed REAL NOT NULL,
        amount_paid REAL DEFAULT 0,
        status TEXT DEFAULT 'outstanding',
        receipt_path TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Database initialized.")

if __name__ == "__main__":
    init_db()
