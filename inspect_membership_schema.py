import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

for table in ["household_memberships", "household_members"]:
    print(f"\n--- {table} ---")
    cols = cur.execute(f"PRAGMA table_info({table})").fetchall()
    for col in cols:
        print(col)

    rows = cur.execute(f"SELECT * FROM {table}").fetchall()
    print("rows:")
    for row in rows:
        print(row)

conn.close()