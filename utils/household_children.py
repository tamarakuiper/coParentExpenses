from utils.db import get_connection

DEFAULT_CHILD_NAMES = [
    "Child 1",
    "Child 2",
]


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


def fetch_household_children(household_id, include_inactive=False):
    ensure_household_children_schema()
    conn = get_connection()
    cursor = conn.cursor()

    if include_inactive:
        cursor.execute(
            """
            SELECT id, household_id, name, sort_order, is_active
            FROM household_children
            WHERE household_id = ?
            ORDER BY sort_order ASC, name ASC
            """,
            (household_id,),
        )
    else:
        cursor.execute(
            """
            SELECT id, household_id, name, sort_order, is_active
            FROM household_children
            WHERE household_id = ?
              AND is_active = 1
            ORDER BY sort_order ASC, name ASC
            """,
            (household_id,),
        )

    rows = cursor.fetchall()
    conn.close()
    return rows


def fetch_household_child_names(household_id):
    rows = fetch_household_children(household_id)
    return [row["name"] for row in rows if row["name"]]


def seed_default_children_if_empty(household_id):
    ensure_household_children_schema()
    existing_names = fetch_household_child_names(household_id)
    if existing_names:
        return existing_names

    save_household_child_names(household_id, DEFAULT_CHILD_NAMES)
    return DEFAULT_CHILD_NAMES[:]


def save_household_child_names(household_id, child_names):
    ensure_household_children_schema()

    cleaned_names = []
    seen = set()
    for raw_name in child_names:
        name = (raw_name or "").strip()
        key = name.lower()
        if name and key not in seen:
            cleaned_names.append(name)
            seen.add(key)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE household_children
        SET is_active = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE household_id = ?
        """,
        (household_id,),
    )

    for index, name in enumerate(cleaned_names):
        cursor.execute(
            """
            INSERT INTO household_children (household_id, name, sort_order, is_active, updated_at)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(household_id, name) DO UPDATE SET
                sort_order = excluded.sort_order,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (household_id, name, index),
        )

    conn.commit()
    conn.close()
    return cleaned_names
