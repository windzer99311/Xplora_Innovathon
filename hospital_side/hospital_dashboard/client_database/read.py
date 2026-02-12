import sqlite3

conn = sqlite3.connect('hospital001.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM patient_bookings')
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()