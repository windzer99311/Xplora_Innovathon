#!/usr/bin/env python3
"""
Database Migration Script
Adds new columns for standalone ambulance bookings:
- ambulance_driver (TEXT)
- ambulance_phone (TEXT)
- ambulance_lat (REAL)
- ambulance_lng (REAL)
"""

import sqlite3
import os

def migrate_database():
    db_path = 'clients.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. No migration needed.")
        return
    
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(bookings)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = {
        'ambulance_driver': 'TEXT',
        'ambulance_phone': 'TEXT',
        'ambulance_lat': 'REAL',
        'ambulance_lng': 'REAL'
    }
    
    added_columns = []
    
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f'ALTER TABLE bookings ADD COLUMN {col_name} {col_type}')
                added_columns.append(col_name)
                print(f"✓ Added column: {col_name} ({col_type})")
            except sqlite3.OperationalError as e:
                print(f"✗ Error adding column {col_name}: {e}")
        else:
            print(f"  Column {col_name} already exists, skipping")
    
    conn.commit()
    conn.close()
    
    if added_columns:
        print(f"\n✅ Migration completed! Added {len(added_columns)} new column(s).")
    else:
        print("\n✅ Database is already up to date. No migration needed.")
    
    print("\nYou can now use the standalone ambulance booking feature!")

if __name__ == '__main__':
    migrate_database()
