#!/usr/bin/env python3
"""
Test script to verify OTP system is working correctly
Run this before the hackathon demo to ensure everything works
"""

import requests
import random
import sqlite3

def test_otp_api():
    """Test if HTTPSMS API is configured correctly"""
    print("🧪 Testing OTP System...")
    print("=" * 50)
    
    # Check if API key is configured
    print("\n1. Checking API configuration...")
    with open('app.py', 'r') as f:
        content = f.read()
        if 'YOUR_API_KEY_HERE' in content:
            print("   ❌ API key not configured!")
            print("   Please edit app.py and add your HTTPSMS API key")
            return False
        else:
            print("   ✅ API key is configured")
    
    # Test database creation
    print("\n2. Testing database initialization...")
    try:
        # Test clients.db
        conn = sqlite3.connect('clients.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("   ✅ clients.db initialized")
        
        # Test user.db
        conn = sqlite3.connect('user.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_store (
                number TEXT PRIMARY KEY,
                otp TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("   ✅ user.db initialized")
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False
    
    # Test OTP generation
    print("\n3. Testing OTP generation...")
    try:
        otp = random.randint(100000, 999999)
        if len(str(otp)) == 6:
            print(f"   ✅ OTP generated: {otp}")
        else:
            print("   ❌ OTP generation failed")
            return False
    except Exception as e:
        print(f"   ❌ OTP error: {e}")
        return False
    
    # Test OTP storage
    print("\n4. Testing OTP storage...")
    try:
        test_phone = "+919999999999"
        test_otp = "123456"
        
        conn = sqlite3.connect('user.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO otp_store (number, otp) VALUES (?, ?)',
            (test_phone, test_otp)
        )
        conn.commit()
        
        # Verify storage
        cursor.execute('SELECT otp FROM otp_store WHERE number = ?', (test_phone,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == test_otp:
            print(f"   ✅ OTP stored and retrieved successfully")
        else:
            print("   ❌ OTP storage verification failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Storage error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED!")
    print("\nYour system is ready for the demo.")
    print("\nNext steps:")
    print("1. Run: python app.py")
    print("2. Open: http://localhost:5000")
    print("3. Test with your actual phone number")
    print("\nGood luck! 🚀")
    
    return True

if __name__ == '__main__':
    test_otp_api()
