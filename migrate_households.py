import sqlite3

DB_PATH = "database/app.db"

def column_exists(conn, table_name, column_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create households table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS households (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by_user_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    """)

    # Create household_members table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS household_members (
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

    # Create household_invites table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS household_invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_id INTEGER NOT NULL,
            invited_email TEXT NOT NULL,
            invited_by_user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT 'pending',
            expires_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            accepted_by_user_id INTEGER,
            FOREIGN KEY (household_id) REFERENCES households(id),
            FOREIGN KEY (invited_by_user_id) REFERENCES users(id),
            FOREIGN KEY (accepted_by_user_id) REFERENCES users(id)
        )
    """)

    # Add columns to expenses only if missing
    if not column_exists(conn, "expenses", "household_id"):
        cur.execute("ALTER TABLE expenses ADD COLUMN household_id INTEGER")

    if not column_exists(conn, "expenses", "created_by_user_id"):
        cur.execute("ALTER TABLE expenses ADD COLUMN created_by_user_id INTEGER")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    main()