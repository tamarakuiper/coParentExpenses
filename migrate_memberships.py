import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

old_rows = cur.execute("""
    SELECT household_id, user_id, role
    FROM household_memberships
""").fetchall()

migrated = 0

for household_id, user_id, role in old_rows:
    cur.execute("""
        INSERT OR IGNORE INTO household_members (household_id, user_id, role)
        VALUES (?, ?, ?)
    """, (household_id, user_id, role or "member"))
    migrated += 1

conn.commit()
conn.close()

print(f"Migrated {migrated} row(s).")