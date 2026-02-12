from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import hashlib
import random
import requests
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Database paths
AMBULANCE_DB = 'ambulances.db'
USER_DB = 'user.db'
REQUEST_FOLDER = 'Request'

# HTTPSMS API Configuration
HTTPSMS_API_KEY = 'uk_a-jdkCg3AChKrOIBXrvSKHq6CwotAZPWtaiz8Z6pGp0UXlQ7brEGz_SXsKSPI6nR'
HTTPSMS_URL = 'https://api.httpsms.com/v1/messages/send'


# Initialize databases
def init_ambulance_db():
    conn = sqlite3.connect(AMBULANCE_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ambulances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id TEXT UNIQUE NOT NULL,
        driver_name TEXT NOT NULL,
        license_no TEXT NOT NULL,
        vehicle_no TEXT NOT NULL,
        phone TEXT UNIQUE NOT NULL,
        aadhar TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        latitude REAL DEFAULT 0.0,
        longitude REAL DEFAULT 0.0,
        last_location_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active_status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def init_user_db():
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS otp_store (
        number TEXT PRIMARY KEY,
        otp TEXT
    )''')
    conn.commit()
    conn.close()


def init_driver_request_db(driver_id):
    os.makedirs(REQUEST_FOLDER, exist_ok=True)
    db_path = f"{REQUEST_FOLDER}/{driver_id}.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT,
        user_phone TEXT,
        user_lat REAL,
        user_lng REAL,
        user_address TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'driver_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Hash password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))


# Send OTP via HTTPSMS
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
        "x-api-key": "uk_3ADVWA8Fy7iGusnRnzSzpUbKD5ioSG0JVI-P50bbFqgLgjA8W76ZHbZ7Xeg9rK6l",
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


# Send SMS via HTTPSMS
def send_sms(phone, message):
    headers = {
        'x-api-key': HTTPSMS_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {
        'from': '+919661394474',
        'to': phone,
        'content': message
    }
    try:
        response = requests.post(HTTPSMS_URL, json=payload, headers=headers)
        return response.status_code == 200
    except:
        return False


@app.route('/')
def index():
    return redirect(url_for('register'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        driver_name = request.form.get('driver_name')
        driver_id = request.form.get('driver_id')
        license_no = request.form.get('license_no')
        vehicle_no = request.form.get('vehicle_no')
        phone = request.form.get('phone')
        aadhar = request.form.get('aadhar')
        password = request.form.get('password')
        otp_input = request.form.get('otp')

        # Validate inputs
        if not all([driver_name, driver_id, license_no, vehicle_no, phone, aadhar, password]):
            return render_template('register.html', error='All fields are required')

        # Verify OTP
        conn = sqlite3.connect(USER_DB)
        c = conn.cursor()
        c.execute('SELECT otp FROM otp_store WHERE number = ?', (phone,))
        result = c.fetchone()
        conn.close()

        if not result or result[0] != otp_input:
            return render_template('register.html', error='Invalid OTP')

        # Check for duplicates
        conn = sqlite3.connect(AMBULANCE_DB)
        c = conn.cursor()
        c.execute('SELECT * FROM ambulances WHERE driver_id = ? OR phone = ? OR aadhar = ?',
                  (driver_id, phone, aadhar))
        if c.fetchone():
            conn.close()
            return render_template('register.html', error='Driver ID, Phone, or Aadhar already exists')

        # Insert driver
        hashed_password = hash_password(password)
        c.execute('''INSERT INTO ambulances (driver_id, driver_name, license_no, vehicle_no, phone, aadhar, password)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (driver_id, driver_name, license_no, vehicle_no, phone, aadhar, hashed_password))
        conn.commit()
        conn.close()

        # Create personal database
        init_driver_request_db(driver_id)

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/send-otp', methods=['POST'])
def send_otp():
    phone = request.json.get('phone')
    if not phone:
        return jsonify({'success': False, 'message': 'Phone number required'})

    otp = generate_otp()

    # Send OTP using new function
    success = Send_otp(phone, otp)

    return jsonify({'success': success, 'message': 'OTP sent' if success else 'Failed to send OTP'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        driver_id = request.form.get('driver_id')
        password = request.form.get('password')

        if not driver_id or not password:
            return render_template('login.html', error='Driver ID and password required')

        conn = sqlite3.connect(AMBULANCE_DB)
        c = conn.cursor()
        c.execute('SELECT * FROM ambulances WHERE driver_id = ? AND password = ?',
                  (driver_id, hash_password(password)))
        driver = c.fetchone()
        conn.close()

        if driver:
            session['driver_id'] = driver[1]
            session['driver_name'] = driver[2]
            session['vehicle_no'] = driver[4]
            session['phone'] = driver[5]
            session['is_active'] = driver[8] if len(driver) > 8 else 1
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    driver_id = session.get('driver_id')

    # Get current active status from database
    conn = sqlite3.connect(AMBULANCE_DB)
    c = conn.cursor()
    c.execute('SELECT is_active FROM ambulances WHERE driver_id = ?', (driver_id,))
    result = c.fetchone()
    conn.close()

    if result:
        session['is_active'] = result[0] if result[0] is not None else 1

    # Get pending requests and history
    db_path = f"{REQUEST_FOLDER}/{driver_id}.db"
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()

        # Auto-deny requests older than 2 minutes
        c.execute('''UPDATE requests 
                     SET status = "denied" 
                     WHERE status = "pending" 
                     AND (julianday('now') - julianday(created_at)) * 24 * 60 > 2''')
        conn.commit()

        # Get pending requests
        c.execute('SELECT * FROM requests WHERE status = "pending" ORDER BY created_at DESC')
        requests_data = c.fetchall()

        # Get history (accepted and denied requests)
        c.execute('SELECT * FROM requests WHERE status IN ("accepted", "denied") ORDER BY created_at DESC LIMIT 50')
        history_data = c.fetchall()

        conn.close()
    else:
        requests_data = []
        history_data = []

    return render_template('dashboard.html', requests=requests_data, history=history_data)


@app.route('/update-location', methods=['POST'])
@login_required
def update_location():
    lat = request.json.get('lat')
    lng = request.json.get('lng')
    driver_id = session.get('driver_id')

    # Update session
    session['driver_lat'] = lat
    session['driver_lng'] = lng

    # Update database
    conn = sqlite3.connect(AMBULANCE_DB)
    c = conn.cursor()
    c.execute('''UPDATE ambulances 
                 SET latitude = ?, longitude = ?, last_location_update = CURRENT_TIMESTAMP 
                 WHERE driver_id = ?''', (lat, lng, driver_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/accept-request/<int:request_id>')
@login_required
def accept_request(request_id):
    driver_id = session.get('driver_id')
    driver_name = session.get('driver_name')
    vehicle_no = session.get('vehicle_no')
    driver_phone = session.get('phone')
    driver_lat = session.get('driver_lat', 0)
    driver_lng = session.get('driver_lng', 0)

    db_path = f"{REQUEST_FOLDER}/{driver_id}.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Get request details
    c.execute('SELECT * FROM requests WHERE id = ?', (request_id,))
    req = c.fetchone()

    if req:
        # Update status
        c.execute('UPDATE requests SET status = "accepted" WHERE id = ?', (request_id,))
        conn.commit()

        user_phone = req[2]

        # Send SMS to user
        sms_message = f"""Ambulance Confirmed 🚑
Driver: {driver_name}
Vehicle: {vehicle_no}
Phone: {driver_phone}
Current Location: {driver_lat},{driver_lng}
Reaching Soon."""

        send_sms(user_phone, sms_message)

        # Store request details in session for map page
        session['accepted_request_id'] = request_id
        session['user_lat'] = req[3]
        session['user_lng'] = req[4]
        session['user_phone'] = user_phone
        session['user_name'] = req[1]

    conn.close()
    return redirect(url_for('live_map'))


@app.route('/deny-request/<int:request_id>')
@login_required
def deny_request(request_id):
    driver_id = session.get('driver_id')
    db_path = f"{REQUEST_FOLDER}/{driver_id}.db"

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('UPDATE requests SET status = "denied" WHERE id = ?', (request_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/map')
@login_required
def live_map():
    return render_template('map.html')


@app.route('/toggle-status', methods=['POST'])
@login_required
def toggle_status():
    driver_id = session.get('driver_id')

    conn = sqlite3.connect(AMBULANCE_DB)
    c = conn.cursor()

    # Get current status
    c.execute('SELECT is_active, active_status FROM ambulances WHERE driver_id = ?', (driver_id,))
    result = c.fetchone()

    if result:
        current_status = result[0] if result[0] is not None else 1
        new_status = 0 if current_status == 1 else 1
        new_active_status = 'inactive' if current_status == 1 else 'active'

        # Update status
        c.execute('UPDATE ambulances SET is_active = ?, active_status = ? WHERE driver_id = ?',
                  (new_status, new_active_status, driver_id))
        conn.commit()

        # Update session
        session['is_active'] = new_status

    conn.close()
    return jsonify({'success': True, 'is_active': new_status})


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# Test endpoint to add request (for testing purposes)
@app.route('/test-add-request/<driver_id>')
def test_add_request(driver_id):
    db_path = f"{REQUEST_FOLDER}/{driver_id}.db"
    if not os.path.exists(db_path):
        init_driver_request_db(driver_id)

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''INSERT INTO requests (user_name, user_phone, user_lat, user_lng, user_address, status)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              ('John Doe', '+1234567890', 13.0827, 80.2707, 'Chennai, India', 'pending'))
    conn.commit()
    conn.close()

    return 'Test request added'


if __name__ == '__main__':
    init_ambulance_db()
    init_user_db()
    app.run(debug=True, port=5000)