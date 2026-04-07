from utils.db import get_connection


def ensure_column(cursor, table_name, column_name, definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row["name"] for row in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    ensure_column(cursor, "users", "last_login_at", "TEXT")

    cursor.execute("PRAGMA table_info(users)")
    print([row["name"] for row in cursor.fetchall()])

    conn.commit()
    conn.close()

    print("Database initialized.")
    print("Users are ready for last_login_at tracking.")


if __name__ == "__main__":
    init_db()