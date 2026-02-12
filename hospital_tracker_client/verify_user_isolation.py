#!/usr/bin/env python3
"""
Verification script to check if ambulance bookings are properly isolated by user
"""
import sqlite3
from datetime import datetime

def verify_booking_isolation():
    """Check if bookings are properly isolated per user"""
    
    print("=" * 70)
    print("BOOKING ISOLATION VERIFICATION")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect('clients.db')
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute('SELECT phone, name FROM users ORDER BY created_at')
        users = cursor.fetchall()
        
        if not users:
            print("\n⚠️  No users found in database")
            print("   Please register at least 2 users to test isolation")
            conn.close()
            return
        
        print(f"\n📊 Found {len(users)} registered users:")
        for phone, name in users:
            print(f"   • {name} ({phone})")
        
        print("\n" + "=" * 70)
        print("BOOKING DETAILS BY USER")
        print("=" * 70)
        
        total_bookings = 0
        
        for phone, name in users:
            # Get bookings for this specific user
            cursor.execute('''
                SELECT id, booking_type, hospital_name, ambulance_number, 
                       ambulance_driver, status, created_at
                FROM bookings
                WHERE user_phone = ?
                ORDER BY created_at DESC
            ''', (phone,))
            
            user_bookings = cursor.fetchall()
            total_bookings += len(user_bookings)
            
            print(f"\n👤 {name} ({phone})")
            print(f"   Total bookings: {len(user_bookings)}")
            
            if user_bookings:
                for booking in user_bookings:
                    booking_id, booking_type, hospital, ambulance_num, driver, status, created = booking
                    
                    if booking_type == 'bed':
                        print(f"   • [BED #{booking_id}] {hospital} - {status}")
                    elif booking_type == 'ambulance':
                        if driver:  # Standalone ambulance
                            print(f"   • [AMBULANCE #{booking_id}] {ambulance_num} - Driver: {driver} - {status}")
                        else:  # Hospital ambulance
                            print(f"   • [AMBULANCE #{booking_id}] {hospital} - {status}")
            else:
                print("   No bookings")
        
        # Verify data integrity
        print("\n" + "=" * 70)
        print("DATA INTEGRITY CHECKS")
        print("=" * 70)
        
        # Check for any bookings with NULL user_phone (should never happen)
        cursor.execute('SELECT COUNT(*) FROM bookings WHERE user_phone IS NULL')
        orphan_count = cursor.fetchone()[0]
        
        if orphan_count > 0:
            print(f"\n❌ ERROR: Found {orphan_count} bookings with NULL user_phone!")
        else:
            print(f"\n✅ All bookings have valid user_phone")
        
        # Check for any bookings with user_phone not in users table
        cursor.execute('''
            SELECT COUNT(*) FROM bookings 
            WHERE user_phone NOT IN (SELECT phone FROM users)
        ''')
        invalid_users = cursor.fetchone()[0]
        
        if invalid_users > 0:
            print(f"❌ ERROR: Found {invalid_users} bookings with invalid user_phone!")
        else:
            print(f"✅ All bookings belong to valid users")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total users: {len(users)}")
        print(f"Total bookings: {total_bookings}")
        print(f"Average bookings per user: {total_bookings / len(users) if users else 0:.1f}")
        
        # Check if isolation is working
        print("\n" + "=" * 70)
        print("ISOLATION TEST RESULT")
        print("=" * 70)
        
        if len(users) >= 2:
            # Get booking counts per user
            booking_counts = []
            for phone, name in users:
                cursor.execute('SELECT COUNT(*) FROM bookings WHERE user_phone = ?', (phone,))
                count = cursor.fetchone()[0]
                booking_counts.append(count)
            
            # Check if all users have the same bookings (would indicate a bug)
            if len(set(booking_counts)) == 1 and booking_counts[0] > 0:
                print("\n⚠️  WARNING: All users have the SAME number of bookings!")
                print("   This might indicate a booking isolation issue.")
                print("   Please verify that different users are making different bookings.")
            else:
                print("\n✅ Users have different booking counts - isolation appears to be working")
        else:
            print("\n⚠️  Need at least 2 users to test isolation")
            print("   Please register another user and try booking with each account separately")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("TESTING INSTRUCTIONS")
        print("=" * 70)
        print("""
To properly test booking isolation:

1. Register two different users with different phone numbers:
   User A: +91-9876543210
   User B: +91-9876543211

2. Login as User A and book an ambulance (e.g., DL-01-AB-1234)

3. Logout and login as User B and book a DIFFERENT ambulance (e.g., DL-02-CD-5678)

4. Run this script again to verify:
   - User A should only see their booking (DL-01-AB-1234)
   - User B should only see their booking (DL-02-CD-5678)

5. Check the terminal output when running the Flask app - you should see:
   [AMBULANCE BOOKING] User +91-9876543210 booked ambulance DL-01-AB-1234
   [AMBULANCE BOOKING] User +91-9876543211 booked ambulance DL-02-CD-5678
        """)
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == '__main__':
    verify_booking_isolation()
