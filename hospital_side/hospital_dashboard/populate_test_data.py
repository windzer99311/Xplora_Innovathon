"""
Test Data Population Script
Creates sample hospitals and client requests for testing
"""

import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def populate_test_data():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    
    print("Populating test data...")
    
    # Sample hospitals
    hospitals = [
        {
            'hospital_id': 'HOSP001',
            'name': 'City General Hospital',
            'lat': 28.6139,
            'lng': 77.2090,
            'contact': '+919999999991',
            'address': 'Connaught Place, New Delhi',
            'password': 'password123'
        },
        {
            'hospital_id': 'HOSP002',
            'name': 'Metro Health Center',
            'lat': 28.7041,
            'lng': 77.1025,
            'contact': '+919999999992',
            'address': 'Rohini, New Delhi',
            'password': 'password123'
        },
        {
            'hospital_id': 'HOSP003',
            'name': 'Apollo Medical Center',
            'lat': 28.5355,
            'lng': 77.3910,
            'contact': '+919999999993',
            'address': 'Noida, Uttar Pradesh',
            'password': 'password123'
        }
    ]
    
    # Insert hospitals
    for hospital in hospitals:
        try:
            cursor.execute('''
                INSERT INTO hospitals (hospital_id, name, lat, lng, contact, address, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                hospital['hospital_id'],
                hospital['name'],
                hospital['lat'],
                hospital['lng'],
                hospital['contact'],
                hospital['address'],
                hash_password(hospital['password'])
            ))
            print(f"✅ Added hospital: {hospital['name']}")
        except sqlite3.IntegrityError:
            print(f"⚠️  Hospital {hospital['hospital_id']} already exists")
    
    # Sample bed data
    bed_data = [
        {
            'hospital_id': 'HOSP001',
            'icu_total': 10,
            'icu_available': 5,
            'general_total': 30,
            'general_available': 12,
            'oxygen_total': 15,
            'oxygen_available': 8
        },
        {
            'hospital_id': 'HOSP002',
            'icu_total': 8,
            'icu_available': 0,
            'general_total': 25,
            'general_available': 8,
            'oxygen_total': 10,
            'oxygen_available': 3
        },
        {
            'hospital_id': 'HOSP003',
            'icu_total': 15,
            'icu_available': 7,
            'general_total': 40,
            'general_available': 20,
            'oxygen_total': 20,
            'oxygen_available': 12
        }
    ]
    
    # Insert bed data
    for bed in bed_data:
        try:
            cursor.execute('''
                INSERT INTO bed_management 
                (hospital_id, icu_total, icu_available, general_total, general_available, oxygen_total, oxygen_available)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                bed['hospital_id'],
                bed['icu_total'],
                bed['icu_available'],
                bed['general_total'],
                bed['general_available'],
                bed['oxygen_total'],
                bed['oxygen_available']
            ))
            print(f"✅ Added bed data for: {bed['hospital_id']}")
        except sqlite3.IntegrityError:
            # Update if already exists
            cursor.execute('''
                UPDATE bed_management
                SET icu_total = ?, icu_available = ?,
                    general_total = ?, general_available = ?,
                    oxygen_total = ?, oxygen_available = ?
                WHERE hospital_id = ?
            ''', (
                bed['icu_total'],
                bed['icu_available'],
                bed['general_total'],
                bed['general_available'],
                bed['oxygen_total'],
                bed['oxygen_available'],
                bed['hospital_id']
            ))
            print(f"✅ Updated bed data for: {bed['hospital_id']}")
    
    # Sample client requests
    requests = [
        {
            'hospital_id': 'HOSP001',
            'name': 'Yuvraj Sha',
            'phone': '+91 9523320088',
            'aadhar': '649821812507',
            'address': 'Andra'
        },
        {
            'hospital_id': 'HOSP001',
            'name': 'Priya Sharma',
            'phone': '+91 9876543210',
            'aadhar': '123456789012',
            'address': 'Mumbai, Maharashtra'
        },
        {
            'hospital_id': 'HOSP002',
            'name': 'Rahul Kumar',
            'phone': '+91 9988776655',
            'aadhar': '987654321098',
            'address': 'Delhi'
        }
    ]
    
    # Insert requests
    for req in requests:
        cursor.execute('''
            INSERT INTO client_requests (hospital_id, name, phone, aadhar, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            req['hospital_id'],
            req['name'],
            req['phone'],
            req['aadhar'],
            req['address']
        ))
    print(f"✅ Added {len(requests)} client requests")
    
    conn.commit()
    conn.close()
    
    print("\n" + "="*50)
    print("Test data populated successfully!")
    print("="*50)
    print("\nTest Hospital Credentials:")
    print("-" * 50)
    for hospital in hospitals:
        print(f"Hospital ID: {hospital['hospital_id']}")
        print(f"Name: {hospital['name']}")
        print(f"Password: {hospital['password']}")
        print("-" * 50)
    print("\nYou can now login with any of these credentials!")

if __name__ == '__main__':
    from app import init_db
    
    # Initialize database first
    print("Initializing database...")
    init_db()
    
    # Populate test data
    populate_test_data()
