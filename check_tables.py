import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

for table in ["household_members", "household_invites", "households", "expenses", "users"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count}")

print("\nexpenses columns:")
cols = cur.execute("PRAGMA table_info(expenses)").fetchall()
for c in cols:
    print(c[1])

conn.close()