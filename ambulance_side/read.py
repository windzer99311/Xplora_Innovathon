import sqlite3

conn = sqlite3.connect('ambulances.db')
c = conn.cursor()

# Get table schema
c.execute("PRAGMA table_info(ambulances)")
columns = c.fetchall()

print("Table Schema:")
for col in columns:
    print(col)

print("\n" + "="*50 + "\n")

# Get all data
c.execute("SELECT * FROM ambulances")
rows = c.fetchall()

print("Data:")
for row in rows:
    print(row)

conn.close()