import sqlite3

# Add missing columns to existing ambulances table
conn = sqlite3.connect('ambulances.db')
c = conn.cursor()

columns_to_add = [
    ('is_active', 'INTEGER DEFAULT 1'),
    ('latitude', 'REAL DEFAULT 0.0'),
    ('longitude', 'REAL DEFAULT 0.0'),
    ('last_location_update', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
    ('active_status', "TEXT DEFAULT 'active'")
]

for column_name, column_type in columns_to_add:
    try:
        c.execute(f'ALTER TABLE ambulances ADD COLUMN {column_name} {column_type}')
        conn.commit()
        print(f"✅ Successfully added {column_name} column to ambulances table")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"ℹ️ Column {column_name} already exists")
        else:
            print(f"❌ Error adding {column_name}: {e}")

conn.close()
print("\n✅ Migration complete! You can now run the app.")
