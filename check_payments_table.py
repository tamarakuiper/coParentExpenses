import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

print("Tables:")
tables = cur.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

for t in tables:
    print("-", t[0])

print("\nexpense_payments columns:")
cols = cur.execute("PRAGMA table_info(expense_payments)").fetchall()
for c in cols:
    print("-", c[1])

print("\nusers columns:")
user_cols = cur.execute("PRAGMA table_info(users)").fetchall()
for c in user_cols:
    print("-", c[1])

conn.close()