import time

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import hashlib
import random
import requests
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'


# Database initialization
def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    # Hospitals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            lat REAL,
            lng REAL,
            contact TEXT NOT NULL,
            address TEXT,
            password TEXT NOT NULL
        )
    ''')

    # Bed management table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bed_management (
            hospital_id TEXT PRIMARY KEY,
            icu_total INTEGER DEFAULT 0,
            icu_available INTEGER DEFAULT 0,
            general_total INTEGER DEFAULT 0,
            general_available INTEGER DEFAULT 0,
            oxygen_total INTEGER DEFAULT 0,
            oxygen_available INTEGER DEFAULT 0,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
        )
    ''')

    # Client requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS client_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            aadhar TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id)
        )
    ''')

    conn.commit()
    conn.close()

    # OTP database
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


# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# OTP generation and sending
def send_otp(phone_number):
    otp = random.randint(100000, 999999)
    print(otp)

    # Store OTP in database
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT OR REPLACE INTO otp_store (number, otp) VALUES (?, ?)',
        (phone_number, str(otp))
    )
    conn.commit()
    conn.close()

    # Send OTP via HTTPSMS
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


# Verify OTP
def verify_otp(phone_number, entered_otp):
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('SELECT otp FROM otp_store WHERE number = ?', (phone_number,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == entered_otp:
        # Delete OTP after successful verification
        conn = sqlite3.connect('user.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM otp_store WHERE number = ?', (phone_number,))
        conn.commit()
        conn.close()
        return True
    return False


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'hospital_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/hospital/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'send_otp':
            # Step 1: Send OTP
            hospital_name = request.form.get('hospital_name')
            contact = request.form.get('contact')
            hospital_id = request.form.get('hospital_id')
            password = request.form.get('password')
            address = request.form.get('address')
            lat = request.form.get('lat', 0.0)
            lng = request.form.get('lng', 0.0)

            # Store in session temporarily
            session['temp_registration'] = {
                'hospital_name': hospital_name,
                'contact': contact,
                'hospital_id': hospital_id,
                'password': password,
                'address': address,
                'lat': lat,
                'lng': lng
            }

            if send_otp(contact):
                flash('OTP sent successfully to ' + contact, 'success')
                return render_template('register.html', otp_sent=True)
            else:
                flash('Failed to send OTP. Please try again.', 'error')
                return render_template('register.html')

        elif action == 'verify_otp':
            # Step 2: Verify OTP and complete registration
            entered_otp = request.form.get('otp')
            temp_data = session.get('temp_registration')

            if not temp_data:
                flash('Registration session expired. Please start again.', 'error')
                return redirect(url_for('register'))

            if verify_otp(temp_data['contact'], entered_otp):
                # Register hospital
                conn = sqlite3.connect('hospital.db')
                cursor = conn.cursor()

                try:
                    cursor.execute('''
                        INSERT INTO hospitals (hospital_id, name, lat, lng, contact, address, password)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        temp_data['hospital_id'],
                        temp_data['hospital_name'],
                        float(temp_data['lat']) if temp_data['lat'] else 0.0,
                        float(temp_data['lng']) if temp_data['lng'] else 0.0,
                        temp_data['contact'],
                        temp_data['address'],
                        hash_password(temp_data['password'])
                    ))

                    # Initialize bed management
                    cursor.execute('''
                        INSERT INTO bed_management (hospital_id)
                        VALUES (?)
                    ''', (temp_data['hospital_id'],))

                    conn.commit()
                    import os
                    os.makedirs("client_database", exist_ok=True)

                    # Initialize client database with patient_bookings table
                    client_db_path = f"client_database/{temp_data['hospital_id']}.db"
                    client_conn = sqlite3.connect(client_db_path)
                    client_cursor = client_conn.cursor()
                    client_cursor.execute('''
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
                    client_conn.commit()
                    client_conn.close()

                    session.pop('temp_registration', None)
                    flash('Registration successful! Please login.', 'success')
                    return redirect(url_for('login'))

                except sqlite3.IntegrityError:
                    flash('Hospital ID already exists. Please choose another.', 'error')
                    return render_template('register.html')
                finally:
                    conn.close()
            else:
                flash('Invalid OTP. Please try again.', 'error')
                return render_template('register.html', otp_sent=True)

    return render_template('register.html')


@app.route('/hospital/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        hospital_id = request.form.get('hospital_id')
        password = request.form.get('password')

        conn = sqlite3.connect('hospital.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password, name FROM hospitals WHERE hospital_id = ?', (hospital_id,))
        result = cursor.fetchone()
        conn.close()

        if result and result[0] == hash_password(password):
            session['hospital_id'] = hospital_id
            session['hospital_name'] = result[1]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard_beds'))
        else:
            flash('Invalid Hospital ID or Password', 'error')

    return render_template('login.html')


@app.route('/hospital/dashboard/beds', methods=['GET', 'POST'])
@login_required
def dashboard_beds():
    hospital_id = session['hospital_id']

    if request.method == 'POST':
        # Update bed data
        conn = sqlite3.connect('hospital.db')
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE bed_management
            SET icu_total = ?, icu_available = ?,
                general_total = ?, general_available = ?,
                oxygen_total = ?, oxygen_available = ?
            WHERE hospital_id = ?
        ''', (
            int(request.form.get('icu_total')),
            int(request.form.get('icu_available')),
            int(request.form.get('general_total')),
            int(request.form.get('general_available')),
            int(request.form.get('oxygen_total')),
            int(request.form.get('oxygen_available')),
            hospital_id
        ))

        conn.commit()
        conn.close()

        flash('Bed data updated successfully', 'success')
        return redirect(url_for('dashboard_beds'))

    # Get current bed data
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bed_management WHERE hospital_id = ?', (hospital_id,))
    bed_data = cursor.fetchone()
    conn.close()

    if bed_data:
        beds = {
            'icu_total': bed_data[1],
            'icu_available': bed_data[2],
            'general_total': bed_data[3],
            'general_available': bed_data[4],
            'oxygen_total': bed_data[5],
            'oxygen_available': bed_data[6]
        }
    else:
        beds = {
            'icu_total': 0,
            'icu_available': 0,
            'general_total': 0,
            'general_available': 0,
            'oxygen_total': 0,
            'oxygen_available': 0
        }

    return render_template('dashboard_beds.html', beds=beds)


@app.route('/hospital/dashboard/requests')
@login_required
def dashboard_requests():
    hospital_id = session['hospital_id']

    # Get client requests from the hospital-specific client database
    import os
    db_path = f'client_database/{hospital_id}.db'

    requests_list = []

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, phone_no, aadhar_no, location, bed_type, ambulance, created_at
            FROM patient_bookings
            ORDER BY created_at DESC
        ''')

        requests_data = cursor.fetchall()
        conn.close()

        for req in requests_data:
            requests_list.append({
                'id': req[0],
                'name': req[1],
                'phone': req[2],
                'aadhar': req[3],
                'address': req[4] if req[4] else 'N/A',
                'bed_type': req[5] if req[5] else 'N/A',
                'ambulance': req[6],
                'created_at': req[7]
            })

    return render_template('dashboard_requests.html', requests=requests_list)


@app.route('/hospital/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


# API endpoint for client-side web to fetch hospital data
@app.route('/api/hospitals', methods=['GET'])
def get_hospitals():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT h.id, h.hospital_id, h.name, h.lat, h.lng, h.contact, h.address,
               b.icu_available, b.general_available, b.oxygen_available
        FROM hospitals h
        LEFT JOIN bed_management b ON h.hospital_id = b.hospital_id
    ''')

    hospitals = []
    for row in cursor.fetchall():
        hospitals.append({
            'id': row['id'],
            'hospital_id': row['hospital_id'],
            'name': row['name'],
            'lat': row['lat'],
            'lng': row['lng'],
            'beds': {
                'icu': row['icu_available'] if row['icu_available'] else 0,
                'general': row['general_available'] if row['general_available'] else 0,
                'oxygen': row['oxygen_available'] if row['oxygen_available'] else 0
            },
            'user_phone': row['contact'],
            'address': row['address']
        })

    conn.close()
    return jsonify(hospitals)


# API endpoint for client to submit requests
@app.route('/api/request', methods=['POST'])
def submit_request():
    data = request.json

    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO client_requests (hospital_id, name, phone, aadhar, address)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        data.get('hospital_id'),
        data.get('name'),
        data.get('phone'),
        data.get('aadhar'),
        data.get('address', None)
    ))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Request submitted successfully'})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)