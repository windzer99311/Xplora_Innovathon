from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import requests
import random
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'


# ========================
# OTP FUNCTIONS (MANDATORY)
# ========================

def generate_otp():
    return random.randint(100000, 999999)


def Send_otp(phone_number, otp):
    # Ensure table exists and store OTP
    print(otp)
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS otp_store (number TEXT PRIMARY KEY, otp TEXT)'
    )
    cursor.execute(
        'INSERT OR REPLACE INTO otp_store (number, otp) VALUES (?, ?)',
        (phone_number, str(otp))
    )
    conn.commit()
    conn.close()

    url = "https://api.httpsms.com/v1/messages/send"
    headers = {
        "x-api-key": "uk_a-jdkCg3AChKrOIBXrvSKHq6CwotAZPWtaiz8Z6pGp0UXlQ7brEGz_SXsKSPI6nR",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "+919661394474",
        "to": phone_number,
        "content": f"Your OTP is {otp}. Do not share this."
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        return response.status_code == 200
    except:
        return False


def verify_otp(phone_number, otp):
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('SELECT otp FROM otp_store WHERE number = ?', (phone_number,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == str(otp):
        return True
    return False


# ========================
# DATABASE INITIALIZATION
# ========================

def init_db():
    # Initialize clients.db
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            aadhar TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create bookings table for bed and ambulance bookings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            booking_type TEXT NOT NULL,
            hospital_id INTEGER,
            hospital_name TEXT,
            hospital_contact TEXT,
            bed_type TEXT,
            ambulance_number TEXT,
            ambulance_id INTEGER,
            ambulance_driver TEXT,
            ambulance_phone TEXT,
            ambulance_lat REAL,
            ambulance_lng REAL,
            status TEXT DEFAULT 'confirmed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_phone) REFERENCES users(phone)
        )
    ''')
    conn.commit()
    conn.close()

    # Initialize user.db for OTP
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


# ========================
# LOGIN REQUIRED DECORATOR
# ========================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_phone' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# ========================
# AUTHENTICATION ROUTES
# ========================

@app.route('/')
def index():
    if 'user_phone' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')

        if action == 'send_otp':
            name = data.get('name')
            phone = data.get('phone')
            aadhar = data.get('aadhar')

            # Validate Aadhar (12 digits)
            if not aadhar or len(aadhar) != 12 or not aadhar.isdigit():
                return jsonify({'success': False, 'message': 'Invalid Aadhar number'})

            # Check if phone already exists
            conn = sqlite3.connect('clients.db')
            cursor = conn.cursor()
            cursor.execute('SELECT phone FROM users WHERE phone = ?', (phone,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Phone number already registered'})

            # Check if aadhar already exists
            cursor.execute('SELECT aadhar FROM users WHERE aadhar = ?', (aadhar,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Aadhar number already registered'})
            conn.close()

            # Generate and send OTP
            otp = generate_otp()
            if Send_otp(phone, otp):
                return jsonify({'success': True, 'message': 'OTP sent successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP'})

        elif action == 'verify_otp':
            name = data.get('name')
            phone = data.get('phone')
            aadhar = data.get('aadhar')
            otp = data.get('otp')

            # Verify OTP
            if verify_otp(phone, otp):
                # Register user
                conn = sqlite3.connect('clients.db')
                cursor = conn.cursor()
                try:
                    cursor.execute('INSERT INTO users (name, phone, aadhar) VALUES (?, ?, ?)',
                                   (name, phone, aadhar))
                    conn.commit()
                    conn.close()

                    # Log user in
                    session['user_phone'] = phone
                    session['user_name'] = name
                    session['user_aadhar'] = aadhar

                    return jsonify({'success': True, 'message': 'Registration successful'})
                except sqlite3.IntegrityError:
                    conn.close()
                    return jsonify({'success': False, 'message': 'Phone or Aadhar already exists'})
            else:
                return jsonify({'success': False, 'message': 'Invalid OTP'})

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')

        if action == 'send_otp':
            phone = data.get('phone')

            # Check if user exists
            conn = sqlite3.connect('clients.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM users WHERE phone = ?', (phone,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                return jsonify({'success': False, 'message': 'Phone number not registered'})

            # Generate and send OTP
            otp = generate_otp()
            if Send_otp(phone, otp):
                return jsonify({'success': True, 'message': 'OTP sent successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send OTP'})

        elif action == 'verify_otp':
            phone = data.get('phone')
            otp = data.get('otp')

            # Verify OTP
            if verify_otp(phone, otp):
                # Get user details
                conn = sqlite3.connect('clients.db')
                cursor = conn.cursor()
                cursor.execute('SELECT name, aadhar FROM users WHERE phone = ?', (phone,))
                user = cursor.fetchone()
                conn.close()

                if user:
                    session['user_phone'] = phone
                    session['user_name'] = user[0]
                    session['user_aadhar'] = user[1]
                    return jsonify({'success': True, 'message': 'Login successful'})

            return jsonify({'success': False, 'message': 'Invalid OTP'})

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ========================
# DASHBOARD
# ========================

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user_name=session.get('user_name'))


@app.route('/booking')
@login_required
def booking():
    return render_template('booking.html', user_name=session.get('user_name'))


# ========================
# API ENDPOINTS
# ========================
HOSPITAL_DB_PATH = r"C:\Users\Karan Kumar\PycharmProjects\Hospitle_emergency_system\Claude\hospital_side\hospital_dashboard\hospital.db"  # change if needed


def get_all_hospitals():
    conn = sqlite3.connect(HOSPITAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT 
            h.id,
            h.hospital_id,
            h.name,
            h.lat,
            h.lng,
            h.contact,
            h.address,
            bm.icu_available,
            bm.general_available,
            bm.oxygen_available
        FROM hospitals h
        LEFT JOIN bed_management bm
        ON h.hospital_id = bm.hospital_id
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    hospitals = []

    for row in rows:
        hospitals.append({
            "id": row["id"],  # internal DB id
            "hospital_id": row["hospital_id"],  # public hospital key
            "name": row["name"],
            "lat": row["lat"],
            "lng": row["lng"],
            "beds": {
                "icu": row["icu_available"] or 0,
                "general": row["general_available"] or 0,
                "oxygen": row["oxygen_available"] or 0
            },
            "contact": row["contact"],
            "address": row["address"]
        })

    return hospitals


@app.route('/api/hospitals')
@login_required
def get_hospitals():
    try:
        hospitals = get_all_hospitals()
        return jsonify(hospitals)
    except Exception as e:
        print("[ERROR] Failed to load hospitals:", e)
        return jsonify({
            "success": False,
            "message": "Unable to load hospital data"
        }), 500


# Add this to hospital_tracker_client/app.py

# Path to ambulance database
AMBULANCE_DB = r'C:\Users\Karan Kumar\PycharmProjects\Hospitle_emergency_system\Claude\ambulance_side\ambulances.db'


@app.route('/api/ambulances')
@login_required
def get_ambulances():
    """Fetch real ambulance data from ambulance_side database"""
    ambulances = []

    try:
        conn = sqlite3.connect(AMBULANCE_DB)
        cursor = conn.cursor()

        # Get all active ambulances with their details and location
        cursor.execute('''
            SELECT id, driver_name, vehicle_no, phone, is_active, latitude, longitude ,driver_id
            FROM ambulances 
            WHERE is_active = 1 AND active_status = 'active'
        ''')

        rows = cursor.fetchall()
        conn.close()

        # Transform to required format
        for row in rows:
            ambulances.append({
                'id': row[0],
                'driver': row[1],
                'number': row[2],
                'phone': row[3],
                'status': 'available',
                'lat': row[5] if row[5] != 0.0 else 28.6139,  # Use stored lat or default
                'lng': row[6] if row[6] != 0.0 else 77.2090,  # Use stored lng or default
                'driver_id': row[7]
            })

    except Exception as e:
        print(f"Error fetching ambulances: {e}")
        return jsonify([])

    return jsonify(ambulances)


# Alternative: If you want to fetch live location from driver sessions
@app.route('/api/ambulances_with_location')
@login_required
def get_ambulances_with_location():
    """Fetch ambulances with live location from driver database"""
    ambulances = []

    try:
        # Connect to ambulance database
        conn = sqlite3.connect(AMBULANCE_DB)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, driver_id, driver_name, vehicle_no, phone, is_active
            FROM ambulances
            WHERE active_status = 'active'
        ''')

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            driver_id = row[1]
            is_active = row[5]

            # Default location
            lat, lng = 28.6139, 77.2090

            # Try to get live location from driver's personal database
            driver_db_path = fr'C:\Users\Karan Kumar\PycharmProjects\Hospitle_emergency_system\Claude\ambulance_side\Request\{driver_id}.db'

            # Get status based on is_active toggle
            if is_active == 1:
                status = 'available'
            else:
                status = 'busy'

            ambulances.append({
                'id': row[0],
                'driver': row[2],
                'number': row[3],
                'phone': row[4],
                'status': status,
                'lat': lat,
                'lng': lng
            })

    except Exception as e:
        print(f"Error fetching ambulances: {e}")

    return jsonify(ambulances)


@app.route('/api/request_ambulance', methods=['POST'])
@login_required
def request_ambulance():
    data = request.json
    hospital_id = data.get('hospital_id')
    user_phone = session.get('user_phone')

    # In a real app, this would dispatch an ambulance
    # For demo, just return success
    return jsonify({
        'success': True,
        'message': f'Ambulance requested! You will receive a call shortly at {user_phone}',
        'estimated_time': '8-12 minutes'
    })


@app.route('/api/book_ambulance', methods=['POST'])
@login_required
def book_ambulance():
    """Standalone ambulance booking (not through hospital)"""
    import os

    data = request.json
    ambulance_id = data.get('ambulance_id')
    ambulance_number = data.get('ambulance_number')
    driver = data.get('driver')
    phone = data.get('phone')
    lat = data.get('lat')
    lng = data.get('lng')
    driver_id = data.get('driver_id')  # Get driver_id from request
    user_lat = data.get('user_lat')  # User's current location
    user_lng = data.get('user_lng')  # User's current location
    user_address = data.get('user_address', 'Unknown location')  # User's address

    user_phone = session.get('user_phone')
    user_name = session.get('user_name')

    # Extra validation: Ensure user_phone is set in session
    if not user_phone:
        return jsonify({
            'success': False,
            'message': 'Session expired. Please login again.'
        }), 401

    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()

    # Verify user exists in database
    cursor.execute('SELECT phone FROM users WHERE phone = ?', (user_phone,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Invalid user session. Please login again.'
        }), 401

    # Save standalone ambulance booking - ONLY for the logged-in user
    cursor.execute('''
        INSERT INTO bookings (user_phone, booking_type, ambulance_id, ambulance_number,
                            ambulance_driver, ambulance_phone, ambulance_lat, ambulance_lng, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_phone, 'ambulance', ambulance_id, ambulance_number,
          driver, phone, lat, lng, 'confirmed'))

    # Debug logging
    print(f"[AMBULANCE BOOKING] User {user_phone} booked ambulance {ambulance_number} (ID: {ambulance_id})")
    print(f"[AMBULANCE BOOKING] Driver: {driver}, Phone: {phone}")

    conn.commit()
    conn.close()

    # Save request to driver's Request database using driver_id
    if not driver_id:
        print(f"[ERROR] driver_id not provided in request")
        return jsonify({
            'success': True,
            'message': f'✅ Ambulance {ambulance_number} has been booked!\n\nDriver: {driver}\nPhone: {phone}\nEstimated arrival: 8-12 minutes'
        })

    driver_request_db = fr"C:\Users\Karan Kumar\PycharmProjects\Hospitle_emergency_system\Claude\ambulance_side\Request\{driver_id}.db"

    # Debug logging
    print(f"[DEBUG] driver_id: {driver_id}")
    print(f"[DEBUG] user_lat: {user_lat}, user_lng: {user_lng}, user_address: {user_address}")
    print(f"[DEBUG] driver_request_db path: {driver_request_db}")

    # Validate user location data
    if user_lat is None or user_lng is None:
        print(f"[WARNING] User location not provided. Skipping driver request database update.")
    else:
        try:
            # Create Request directory if it doesn't exist
            os.makedirs(os.path.dirname(driver_request_db), exist_ok=True)

            # Connect to driver's request database
            request_conn = sqlite3.connect(driver_request_db)
            request_cursor = request_conn.cursor()

            # Create table if it doesn't exist
            request_cursor.execute('''CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT,
                user_phone TEXT,
                user_lat REAL,
                user_lng REAL,
                user_address TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')

            # Insert request
            request_cursor.execute('''
                INSERT INTO requests (user_name, user_phone, user_lat, user_lng, user_address, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            ''', (user_name, user_phone, user_lat, user_lng, user_address))

            request_conn.commit()
            request_conn.close()

            print(f"[DRIVER REQUEST] ✅ Request saved to {driver_request_db}")
            print(f"[DRIVER REQUEST] User: {user_name}, Phone: {user_phone}, Location: ({user_lat}, {user_lng})")
        except Exception as e:
            print(f"[DRIVER REQUEST ERROR] ❌ Failed to save to driver database: {e}")
            import traceback
            traceback.print_exc()

    return jsonify({
        'success': True,
        'message': f'✅ Ambulance {ambulance_number} has been booked!\n\nDriver: {driver}\nPhone: {phone}\nEstimated arrival: 8-12 minutes'
    })


@app.route('/api/book_hospital', methods=['POST'])
@login_required
def book_hospital():
    import os

    data = request.json
    hospital_id = data.get('hospital_id')
    hospital_name = data.get('hospital_name')
    hospital_contact = data.get('hospital_contact')
    bed_type = data.get('bed_type')
    services = data.get('services', [])
    location = data.get('location', 'unknown')
    ambulance = data.get('ambulance', False)

    user_phone = session.get('user_phone')
    user_name = session.get('user_name')
    user_aadhar = session.get('user_aadhar')

    # Extra validation: Ensure user_phone is set in session
    if not user_phone:
        return jsonify({
            'success': False,
            'message': 'Session expired. Please login again.'
        }), 401

    # Debug logging
    print(f"[HOSPITAL BOOKING] User {user_phone} booking at {hospital_name}")

    # Save to clients.db (original functionality)
    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()

    # Verify user exists in database
    cursor.execute('SELECT phone FROM users WHERE phone = ?', (user_phone,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Invalid user session. Please login again.'
        }), 401

    # Save bed booking - ONLY for the logged-in user
    if 'bed_booking' in services:
        cursor.execute('''
            INSERT INTO bookings (user_phone, booking_type, hospital_id, hospital_name, 
                                hospital_contact, bed_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_phone, 'bed', hospital_id, hospital_name, hospital_contact, bed_type, 'confirmed'))
        print(f"[HOSPITAL BOOKING] Bed booking saved for {user_phone}")

    # Save ambulance booking - ONLY for the logged-in user
    if 'ambulance' in services:
        cursor.execute('''
            INSERT INTO bookings (user_phone, booking_type, hospital_id, hospital_name, 
                                hospital_contact, ambulance_number, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_phone, 'ambulance', hospital_id, hospital_name, hospital_contact,
              'Ambulance dispatched', 'en-route'))
        print(f"[HOSPITAL BOOKING] Ambulance booking saved for {user_phone}")

    conn.commit()
    conn.close()

    # Save to hospital database
    hospital_db_path = fr"C:\Users\Karan Kumar\PycharmProjects\Hospitle_emergency_system\Claude\hospital_side\hospital_dashboard\client_database\{hospital_id}.db"

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(hospital_db_path), exist_ok=True)

        # Connect to hospital database
        hospital_conn = sqlite3.connect(hospital_db_path)
        hospital_cursor = hospital_conn.cursor()

        # Create table if it doesn't exist
        hospital_cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone_no TEXT NOT NULL,
                aadhar_no TEXT NOT NULL,
                ambulance BOOLEAN NOT NULL,
                location TEXT NOT NULL,
                bed_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert booking data
        hospital_cursor.execute('''
            INSERT INTO patient_bookings (name, phone_no, aadhar_no, ambulance, location, bed_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_name, user_phone, user_aadhar, ambulance, location, bed_type))

        hospital_conn.commit()
        hospital_conn.close()

        print(f"[HOSPITAL DB] Data saved to {hospital_db_path}")
    except Exception as e:
        print(f"[HOSPITAL DB ERROR] Failed to save to hospital database: {e}")

    # Build confirmation message
    services_text = []
    if 'bed_booking' in services:
        services_text.append(f'{bed_type.upper()} bed reserved')
    if 'ambulance' in services:
        services_text.append('Ambulance dispatched')

    message = f'Booking confirmed for {user_name}!\n'
    message += '\n'.join(services_text)
    message += f'\n\nContact: {user_phone}'

    if 'ambulance' in services:
        message += '\nEstimated arrival: 8-12 minutes'

    return jsonify({
        'success': True,
        'message': message
    })


@app.route('/api/user_info')
@login_required
def get_user_info():
    user_phone = session.get('user_phone')

    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, phone, aadhar, created_at FROM users WHERE phone = ?', (user_phone,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            'success': True,
            'data': {
                'name': user[0],
                'phone': user[1],
                'aadhar': user[2],
                'registered_on': user[3]
            }
        })
    return jsonify({'success': False, 'message': 'User not found'})


@app.route('/api/booking_history')
@login_required
def get_booking_history():
    user_phone = session.get('user_phone')

    # Debug: Log who is requesting history
    print(f"[BOOKING HISTORY] Request from user: {user_phone}")

    if not user_phone:
        return jsonify({
            'success': False,
            'message': 'Session expired. Please login again.'
        }), 401

    conn = sqlite3.connect('clients.db')
    cursor = conn.cursor()

    # Get all bookings for THIS SPECIFIC USER ONLY
    cursor.execute('''
        SELECT id, booking_type, hospital_name, hospital_contact, bed_type, 
               ambulance_number, ambulance_id, status, created_at,
               ambulance_driver, ambulance_phone, ambulance_lat, ambulance_lng, user_phone
        FROM bookings 
        WHERE user_phone = ?
        ORDER BY created_at DESC
    ''', (user_phone,))

    bookings = cursor.fetchall()

    # Debug: Log how many bookings found
    print(f"[BOOKING HISTORY] Found {len(bookings)} bookings for {user_phone}")

    conn.close()

    bed_bookings = []
    ambulance_bookings = []

    for booking in bookings:
        # Extra safety check: verify booking belongs to requesting user
        if booking[13] != user_phone:
            print(f"[WARNING] Skipping booking {booking[0]} - belongs to {booking[13]}, not {user_phone}")
            continue

        booking_data = {
            'id': booking[0],
            'hospital_name': booking[2],
            'hospital_contact': booking[3],
            'status': booking[7],
            'booked_on': booking[8]
        }

        if booking[1] == 'bed':
            booking_data['bed_type'] = booking[4]
            bed_bookings.append(booking_data)
        elif booking[1] == 'ambulance':
            booking_data['ambulance_number'] = booking[5]
            booking_data['ambulance_id'] = booking[6]
            # Add standalone ambulance fields if present
            if booking[9]:  # ambulance_driver
                booking_data['ambulance_driver'] = booking[9]
                booking_data['ambulance_phone'] = booking[10]
                booking_data['ambulance_lat'] = booking[11]
                booking_data['ambulance_lng'] = booking[12]

                # Fetch status from driver's request database
                ambulance_id = booking[6]
                if ambulance_id:
                    try:
                        # Get driver_id from ambulance database
                        import os
                        amb_conn = sqlite3.connect(AMBULANCE_DB)
                        amb_cursor = amb_conn.cursor()
                        amb_cursor.execute('SELECT driver_id FROM ambulances WHERE id = ?', (ambulance_id,))
                        result = amb_cursor.fetchone()
                        amb_conn.close()

                        if result:
                            driver_id = result[0]
                            driver_request_db = fr"C:\Users\Karan Kumar\PycharmProjects\Hospitle_emergency_system\Claude\ambulance_side\Request\{driver_id}.db"

                            if os.path.exists(driver_request_db):
                                driver_conn = sqlite3.connect(driver_request_db)
                                driver_cursor = driver_conn.cursor()

                                # Get status for this specific booking by matching user_phone and created_at timestamp
                                # We look for requests created within 5 seconds of the booking time
                                booking_time = booking[8]  # created_at from bookings table
                                driver_cursor.execute('''
                                    SELECT status FROM requests 
                                    WHERE user_phone = ?
                                    AND ABS(JULIANDAY(created_at) - JULIANDAY(?)) * 86400 <= 5
                                    ORDER BY ABS(JULIANDAY(created_at) - JULIANDAY(?))
                                    LIMIT 1
                                ''', (user_phone, booking_time, booking_time))

                                status_result = driver_cursor.fetchone()
                                driver_conn.close()

                                if status_result:
                                    booking_data['status'] = status_result[0]
                    except Exception as e:
                        print(f"[ERROR] Failed to fetch status from driver DB: {e}")

            ambulance_bookings.append(booking_data)

    print(
        f"[BOOKING HISTORY] Returning {len(bed_bookings)} bed bookings and {len(ambulance_bookings)} ambulance bookings")

    return jsonify({
        'success': True,
        'data': {
            'beds': bed_bookings,
            'ambulances': ambulance_bookings
        }
    })


# ========================
# RUN APP
# ========================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=8000)