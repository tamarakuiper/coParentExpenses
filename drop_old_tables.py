import sqlite3

conn = sqlite3.connect("database/app.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS household_memberships")
cur.execute("DROP TABLE IF EXISTS invitations")

conn.commit()
conn.close()

print("Old tables dropped.")