from utils.db import get_connection


def _columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row["name"]: row for row in cursor.fetchall()}


def _ensure_column(cursor, table_name, column_name, definition):
    if column_name not in _columns(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def _ensure_payment_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS expense_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            household_id INTEGER NOT NULL,
            paid_by_user_id INTEGER NOT NULL,
            received_by_user_id INTEGER,
            received_by_name TEXT,
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
        """
    )

    columns = _columns(cursor, "expense_payments")
    if "received_by_name" not in columns:
        cursor.execute("ALTER TABLE expense_payments ADD COLUMN received_by_name TEXT")
        columns = _columns(cursor, "expense_payments")

    # Older copies had received_by_user_id as NOT NULL, which prevents recording
    # payments to external/non-household people. Rebuild the table with that
    # column nullable while preserving existing rows.
    received_by = columns.get("received_by_user_id")
    if received_by and received_by["notnull"]:
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("ALTER TABLE expense_payments RENAME TO expense_payments_old")
        cursor.execute(
            """
            CREATE TABLE expense_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER NOT NULL,
                household_id INTEGER NOT NULL,
                paid_by_user_id INTEGER NOT NULL,
                received_by_user_id INTEGER,
                received_by_name TEXT,
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
            """
        )
        old_columns = _columns(cursor, "expense_payments_old")
        received_by_name_expr = "received_by_name" if "received_by_name" in old_columns else "NULL"
        cursor.execute(
            f"""
            INSERT INTO expense_payments (
                id, expense_id, household_id, paid_by_user_id, received_by_user_id,
                received_by_name, method, amount, external_reference, note, paid_at, created_at
            )
            SELECT
                id, expense_id, household_id, paid_by_user_id, received_by_user_id,
                {received_by_name_expr}, method, amount, external_reference, note, paid_at, created_at
            FROM expense_payments_old
            """
        )
        cursor.execute("DROP TABLE expense_payments_old")
        cursor.execute("PRAGMA foreign_keys = ON")


def ensure_expense_schema():
    conn = get_connection()
    cursor = conn.cursor()

    _ensure_column(cursor, "expenses", "household_id", "INTEGER")
    _ensure_column(cursor, "expenses", "created_by_user_id", "INTEGER")
    _ensure_column(cursor, "expenses", "updated_by_user_id", "INTEGER")
    _ensure_column(cursor, "expenses", "paid_by_user_id", "INTEGER")
    _ensure_column(cursor, "expenses", "owed_by_user_id", "INTEGER")
    _ensure_column(cursor, "expenses", "updated_at", "TEXT")

    _ensure_payment_table(cursor)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS household_children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            UNIQUE(household_id, name),
            FOREIGN KEY (household_id) REFERENCES households(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER NOT NULL,
            expense_id INTEGER NOT NULL,
            allocated_amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (payment_id) REFERENCES expense_payments(id),
            FOREIGN KEY (expense_id) REFERENCES expenses(id)
        )
        """
    )

    conn.commit()
    conn.close()



def ensure_household_children_schema():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS household_children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            UNIQUE(household_id, name),
            FOREIGN KEY (household_id) REFERENCES households(id)
        )
        """
    )
    conn.commit()
    conn.close()
