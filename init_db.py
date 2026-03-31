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
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS households (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_by_user_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS household_memberships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL DEFAULT 'member',
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(household_id, user_id),
        FOREIGN KEY (household_id) REFERENCES households(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invitations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        household_id INTEGER NOT NULL,
        invited_by_user_id INTEGER NOT NULL,
        email TEXT NOT NULL,
        token TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL DEFAULT 'pending',
        expires_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        accepted_at TEXT,
        FOREIGN KEY (household_id) REFERENCES households(id),
        FOREIGN KEY (invited_by_user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        child_name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        expense_date TEXT NOT NULL,
        paid_by TEXT,
        owed_by TEXT,
        split_type TEXT DEFAULT 'percent',
        split_value REAL DEFAULT 50,
        amount_owed REAL NOT NULL,
        amount_paid REAL DEFAULT 0,
        status TEXT DEFAULT 'outstanding',
        receipt_path TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    ensure_column(cursor, "expenses", "household_id", "INTEGER")
    ensure_column(cursor, "expenses", "created_by_user_id", "INTEGER")
    ensure_column(cursor, "expenses", "updated_by_user_id", "INTEGER")
    ensure_column(cursor, "expenses", "paid_by_user_id", "INTEGER")
    ensure_column(cursor, "expenses", "owed_by_user_id", "INTEGER")
    ensure_column(cursor, "expenses", "updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP")

    conn.commit()
    conn.close()
    print("Database initialized.")
    print("Users, households, memberships, invitations, and expenses are ready.")


if __name__ == "__main__":
    init_db()