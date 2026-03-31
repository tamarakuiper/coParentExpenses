import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

for table in ["household_members", "household_memberships", "household_invites", "invitations"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count}")

conn.close()