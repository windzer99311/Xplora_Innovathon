import sqlite3

# Connect to database
conn = sqlite3.connect('K002.db')
cursor = conn.cursor()

# Get all requests
cursor.execute('SELECT * FROM requests')
requests = cursor.fetchall()

print("All Requests:")
print("-" * 80)
for req in requests:
    print(f"ID: {req[0]}")
    print(f"Name: {req[1]}")
    print(f"Phone: {req[2]}")
    print(f"Location: {req[3]}, {req[4]}")
    print(f"Address: {req[5]}")
    print(f"Status: {req[6]}")
    print(f"Created: {req[7]}")
    print("-" * 80)

conn.close()