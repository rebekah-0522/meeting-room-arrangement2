from flask import Flask, request, jsonify, send_from_directory, make_response, session
from flask_cors import CORS
import sqlite3
import json
import uuid
import sys
import traceback
import os
import bcrypt
import smtplib
import random
import string
from datetime import datetime, timedelta

try:
    import qrcode
    from io import BytesIO
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print('[WARN] qrcode library not installed, QR code generation disabled')

print('[DEBUG] Starting Flask application...')
print('[DEBUG] Python version:', sys.version)

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root
PROJECT_ROOT = os.path.dirname(BASE_DIR)

print(f'[DEBUG] Project root: {PROJECT_ROOT}')

app = Flask(__name__, 
            static_folder=PROJECT_ROOT, 
            static_url_path='',
            template_folder=PROJECT_ROOT)
app.secret_key = os.environ.get('SECRET_KEY', 'meeting-room-secret-key-2024')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
CORS(app, supports_credentials=True)

DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE = os.path.join(BASE_DIR, 'meeting_room.db')

if DATABASE_URL:
    print('[DEBUG] Using PostgreSQL database (Railway)')
    print(f'[DEBUG] Database URL: {DATABASE_URL[:30]}...')
else:
    print(f'[DEBUG] Using SQLite database: {DATABASE}')

reset_tokens = {}

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

def send_email(to_email, code):
    try:
        smtp_server = 'smtp.foxconn.com'
        smtp_port = 25
        from_email = 'meeting-room-system@foxconn.com'
        
        subject = 'Meeting Room Booking System - Password Reset Verification Code'
        body = f'Your verification code is: {code}\n\nThis code expires in 15 minutes.'
        
        msg = f'Subject: {subject}\n\n{body}'
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(from_email, to_email, msg)
        return True
    except Exception as e:
        print('[ERROR] Failed to send email:', str(e))
        return False

def ph(sql):
    if DATABASE_URL:
        return sql.replace('?', '%s')
    return sql

def get_db():
    if DATABASE_URL:
        import psycopg2
        from psycopg2 import extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = extras.DictCursor
        return conn
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    try:
        print('[DEBUG] Initializing database...')
        conn = get_db()
        c = conn.cursor()
        
        print('[DEBUG] Creating users table...')
        if DATABASE_URL:
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT, 
                          password TEXT, role TEXT DEFAULT 'user', credit INTEGER DEFAULT 0,
                          last_booking_date TEXT, created_at TEXT)''')
        else:
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT, 
                          password TEXT, role TEXT DEFAULT 'user', credit INTEGER DEFAULT 0,
                          last_booking_date TEXT, created_at TEXT)''')
        
        print('[DEBUG] Creating rooms table...')
        c.execute('''CREATE TABLE IF NOT EXISTS rooms
                     (id TEXT PRIMARY KEY, building TEXT, floor TEXT, name TEXT,
                      capacity INTEGER, has_webex INTEGER, has_projector INTEGER,
                      room_type TEXT DEFAULT 'normal')''')
        
        print('[DEBUG] Creating bookings table...')
        c.execute('''CREATE TABLE IF NOT EXISTS bookings
                     (id TEXT PRIMARY KEY, room_id TEXT, user_id TEXT, title TEXT,
                      start_date TEXT, end_date TEXT, start_slot TEXT, end_slot TEXT,
                      note TEXT, status TEXT DEFAULT 'pending', created_at TEXT,
                      approved_at TEXT, cancelled_at TEXT)''')
        
        print('[DEBUG] Adding missing columns to bookings table...')
        try:
            c.execute('ALTER TABLE bookings ADD COLUMN contact_name TEXT')
            print('[DEBUG] Added contact_name column')
        except:
            print('[DEBUG] contact_name column already exists')
        try:
            c.execute('ALTER TABLE bookings ADD COLUMN contact_phone TEXT')
            print('[DEBUG] Added contact_phone column')
        except:
            print('[DEBUG] contact_phone column already exists')
        
        print('[DEBUG] Creating builds table...')
        c.execute('''CREATE TABLE IF NOT EXISTS builds
                     (id TEXT PRIMARY KEY, name TEXT, start_date TEXT, end_date TEXT,
                      is_current INTEGER DEFAULT 0, created_at TEXT)''')
        
        print('[DEBUG] Creating logs table...')
        if DATABASE_URL:
            c.execute('''CREATE TABLE IF NOT EXISTS logs
                         (id SERIAL PRIMARY KEY, action TEXT, detail TEXT,
                          operator TEXT, timestamp TEXT)''')
        else:
            c.execute('''CREATE TABLE IF NOT EXISTS logs
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, detail TEXT,
                          operator TEXT, timestamp TEXT)''')
        
        print('[DEBUG] Creating notifications table...')
        if DATABASE_URL:
            c.execute('''CREATE TABLE IF NOT EXISTS notifications
                         (id SERIAL PRIMARY KEY, user_id TEXT, type TEXT,
                          message TEXT, read INTEGER DEFAULT 0, created_at TEXT)''')
        else:
            c.execute('''CREATE TABLE IF NOT EXISTS notifications
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, type TEXT,
                          message TEXT, read INTEGER DEFAULT 0, created_at TEXT)''')
        
        conn.commit()
        conn.close()
        print('[DEBUG] Database initialized successfully')
        
        init_default_data()
    except Exception as e:
        print('[ERROR] Database initialization failed:', str(e))
        traceback.print_exc()

def init_default_data():
    try:
        print('[DEBUG] Initializing default data...')
        conn = get_db()
        c = conn.cursor()
    
        c.execute('SELECT COUNT(*) FROM rooms')
        if c.fetchone()[0] == 0:
            rooms = [
                {'id': 'c01-mickey', 'building': 'C01', 'floor': '4F', 'name': 'Mickey', 'capacity': 102, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-donald', 'building': 'C01', 'floor': '4F', 'name': 'Donald', 'capacity': 80, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-pluto', 'building': 'C01', 'floor': '4F', 'name': 'Pluto', 'capacity': 34, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-dumbo', 'building': 'C01', 'floor': '4F', 'name': 'Dumbo', 'capacity': 20, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-pinocchio', 'building': 'C01', 'floor': '4F', 'name': 'Pinocchio', 'capacity': 20, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-minnie', 'building': 'C01', 'floor': '4F', 'name': 'Minnie', 'capacity': 20, 'has_webex': 0, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-goofy', 'building': 'C01', 'floor': '4F', 'name': 'Goofy', 'capacity': 23, 'has_webex': 0, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-bambi', 'building': 'C01', 'floor': '4F', 'name': 'Bambi', 'capacity': 24, 'has_webex': 0, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c01-elsa', 'building': 'C01', 'floor': '4F', 'name': 'Elsa', 'capacity': 14, 'has_webex': 0, 'has_projector': 0, 'room_type': 'epm'},
                {'id': 'c01-aurora', 'building': 'C01', 'floor': '4F', 'name': 'Aurora', 'capacity': 13, 'has_webex': 0, 'has_projector': 0, 'room_type': 'warroom'},
                {'id': 'c01-ariel', 'building': 'C01', 'floor': '4F', 'name': 'Ariel', 'capacity': 12, 'has_webex': 0, 'has_projector': 0, 'room_type': 'normal'},
                {'id': 'c02-magic', 'building': 'C02', 'floor': '4F', 'name': 'Magic', 'capacity': 102, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c02-cavaliers', 'building': 'C02', 'floor': '4F', 'name': 'Cavaliers', 'capacity': 80, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c02-clippers', 'building': 'C02', 'floor': '4F', 'name': 'Clippers', 'capacity': 17, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c02-celtics', 'building': 'C02', 'floor': '4F', 'name': 'Celtics', 'capacity': 25, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c02-knicks', 'building': 'C02', 'floor': '4F', 'name': 'Knicks', 'capacity': 28, 'has_webex': 1, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c02-lakers', 'building': 'C02', 'floor': '4F', 'name': 'Lakers', 'capacity': 20, 'has_webex': 0, 'has_projector': 1, 'room_type': 'normal'},
                {'id': 'c02-spurs', 'building': 'C02', 'floor': '4F', 'name': 'Spurs', 'capacity': 20, 'has_webex': 0, 'has_projector': 0, 'room_type': 'epm'},
                {'id': 'c02-thunder', 'building': 'C02', 'floor': '4F', 'name': 'Thunder', 'capacity': 13, 'has_webex': 0, 'has_projector': 0, 'room_type': 'warroom'},
                {'id': 'c02-bulls', 'building': 'C02', 'floor': '4F', 'name': 'Bulls', 'capacity': 13, 'has_webex': 0, 'has_projector': 0, 'room_type': 'normal'},
                {'id': 'c02-rockets', 'building': 'C02', 'floor': '4F', 'name': 'Rockets', 'capacity': 14, 'has_webex': 0, 'has_projector': 0, 'room_type': 'normal'}
            ]
            for room in rooms:
                c.execute('''INSERT INTO rooms (id, building, floor, name, capacity, has_webex, has_projector, room_type)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                          (room['id'], room['building'], room['floor'], room['name'], room['capacity'],
                           room['has_webex'], room['has_projector'], room['room_type']))
            print('[DEBUG] Default rooms added')
    
        c.execute(ph('SELECT COUNT(*) FROM users WHERE email = ?'), ('rebekah.xy.he@mail.foxconn.com',))
        if c.fetchone()[0] == 0:
            default_password = '123456'
            hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            c.execute(ph('''INSERT INTO users (id, email, name, password, role, created_at)
                         VALUES (?, ?, ?, ?, ?, ?)'''),
                      (str(uuid.uuid4()), 'rebekah.xy.he@mail.foxconn.com', 'Rebekah', hashed_password, 'epm', datetime.now().isoformat()))
            print('[DEBUG] Default user added')
    
        conn.commit()
        conn.close()
        print('[DEBUG] Default data initialized successfully')
    except Exception as e:
        print('[ERROR] Default data initialization failed:', str(e))
        traceback.print_exc()

@app.errorhandler(Exception)
def handle_exception(e):
    print('[ERROR] Exception:', str(e))
    traceback.print_exc()
    return jsonify({'success': False, 'message': str(e)}), 500

print('[DEBUG] Initializing database v2...')
try:
    init_db()
    print('[DEBUG] Application initialization complete')
except Exception as e:
    print('[ERROR] Application initialization failed:', str(e))
    traceback.print_exc()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('SELECT * FROM users WHERE email = ?'), (email,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    stored_password = user['password']
    
    if stored_password:
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                return jsonify({'success': False, 'message': 'Incorrect password'})
        except Exception:
            if password != stored_password:
                return jsonify({'success': False, 'message': 'Incorrect password'})
    else:
        if password != '123456':
            return jsonify({'success': False, 'message': 'Incorrect password'})
    
    role = user['role']
    if email == 'rebekah.xy.he@mail.foxconn.com':
        role = 'epm'
    
    session['user_id'] = user['id']
    session['user_email'] = user['email']
    session['user_role'] = role
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'name': user['name'] or email.split('@')[0],
            'email': user['email'],
            'role': role,
            'credit': user['credit']
        }
    })

@app.route('/api/current-user', methods=['GET'])
def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('SELECT * FROM users WHERE id = ?'), (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        session.clear()
        return jsonify({'success': False, 'message': 'User not found'})
    
    role = user['role']
    if user['email'] == 'rebekah.xy.he@mail.foxconn.com':
        role = 'epm'
    
    return jsonify({
        'success': True,
        'user': {
            'id': user['id'],
            'name': user['name'] or user['email'].split('@')[0],
            'email': user['email'],
            'role': role,
            'credit': user['credit']
        }
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('SELECT * FROM users WHERE email = ?'), (email,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    code = generate_code()
    reset_tokens[email] = {
        'code': code,
        'expires_at': datetime.now() + timedelta(minutes=15)
    }
    
    if send_email(email, code):
        return jsonify({'success': True, 'message': 'Verification code sent to your email'})
    else:
        return jsonify({'success': False, 'message': 'Failed to send email. Please contact Meeting EPM.'})

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    new_password = data.get('password', '').strip()
    
    if not email or not code or not new_password:
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    if new_password == '123456':
        return jsonify({'success': False, 'message': 'Invalid password'})
    
    token = reset_tokens.get(email)
    if not token:
        return jsonify({'success': False, 'message': 'Verification code not found or expired'})
    
    if datetime.now() > token['expires_at']:
        del reset_tokens[email]
        return jsonify({'success': False, 'message': 'Verification code expired'})
    
    if code != token['code']:
        return jsonify({'success': False, 'message': 'Invalid verification code'})
    
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('UPDATE users SET password = ? WHERE email = ?'), (hashed_password, email))
    conn.commit()
    conn.close()
    
    del reset_tokens[email]
    
    return jsonify({'success': True, 'message': 'Password reset successfully'})

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, email, name, role, credit FROM users')
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    email = data.get('email', '').strip().lower()
    name = data.get('name', '').strip()
    
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'})
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT COUNT(*) FROM users WHERE email = ?'), (email,))
    if c.fetchone()[0] > 0:
        conn.close()
        return jsonify({'success': False, 'message': 'User already exists'})
    
    default_password = '123456'
    hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_id = str(uuid.uuid4())
    c.execute(ph('''INSERT INTO users (id, email, name, password, role, credit, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)'''),
              (user_id, email, name or email.split('@')[0], 
               hashed_password, data.get('role', 'user'), 0,
               datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User created successfully'})

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('SELECT id, email, name, role, credit FROM users WHERE id = ?'), (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    return jsonify({'success': True, 'user': dict(user)})

@app.route('/api/users/<user_id>/password', methods=['PUT'])
def update_password(user_id):
    data = request.json
    new_password = data.get('password', '').strip()
    
    if not new_password or new_password == '123456':
        return jsonify({'success': False, 'message': 'Invalid password'})
    
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('UPDATE users SET password = ? WHERE id = ?'), (hashed_password, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Password updated successfully'})

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    building = request.args.get('building')
    
    conn = get_db()
    c = conn.cursor()
    
    if building:
        c.execute(ph('SELECT * FROM rooms WHERE building = ?'), (building,))
    else:
        c.execute('SELECT * FROM rooms')
    
    rooms = []
    for row in c.fetchall():
        room = dict(row)
        room['hasWebex'] = bool(room.pop('has_webex'))
        room['hasProjector'] = bool(room.pop('has_projector'))
        room['roomType'] = room.pop('room_type')
        rooms.append(room)
    
    conn.close()
    return jsonify(rooms)

@app.route('/api/rooms/<room_id>', methods=['GET'])
def get_room(room_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('SELECT * FROM rooms WHERE id = ?'), (room_id,))
    room = c.fetchone()
    conn.close()
    
    if not room:
        return jsonify({'success': False, 'message': 'Room not found'})
    
    room = dict(room)
    room['hasWebex'] = bool(room.pop('has_webex'))
    room['hasProjector'] = bool(room.pop('has_projector'))
    room['roomType'] = room.pop('room_type')
    
    return jsonify({'success': True, 'room': room})

@app.route('/api/rooms/<room_id>', methods=['PUT'])
def update_room(room_id):
    data = request.json
    
    conn = get_db()
    c = conn.cursor()
    
    updates = []
    params = []
    
    if 'hasWebex' in data:
        updates.append('has_webex = ?')
        params.append(1 if data['hasWebex'] else 0)
    if 'roomType' in data:
        updates.append('room_type = ?')
        params.append(data['roomType'])
    
    if updates:
        params.append(room_id)
        c.execute(ph(f'UPDATE rooms SET {", ".join(updates)} WHERE id = ?'), params)
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True, 'message': 'Room updated successfully'})

def get_date_range(start_date, end_date):
    dates = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    return dates

TIME_SLOTS = [
    '08:00-08:30', '08:30-09:00', '09:00-09:30', '09:30-10:00',
    '10:00-10:30', '10:30-11:00', '11:00-11:30', '11:30-12:00',
    '12:00-12:30', '12:30-13:00', '13:00-13:30', '13:30-14:00',
    '14:00-14:30', '14:30-15:00', '15:00-15:30', '15:30-16:00',
    '16:00-16:30', '16:30-17:00', '17:00-17:30', '17:30-18:00',
    '18:00-18:30', '18:30-19:00', '19:00-19:30', '19:30-20:00',
    '20:00-20:30'
]

TIME_POINTS = [
    '08:00', '08:30', '09:00', '09:30',
    '10:00', '10:30', '11:00', '11:30',
    '12:00', '12:30', '13:00', '13:30',
    '14:00', '14:30', '15:00', '15:30',
    '16:00', '16:30', '17:00', '17:30',
    '18:00', '18:30', '19:00', '19:30',
    '20:00', '20:30'
]

def parse_time_to_minutes(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

def slot_index(slot):
    if not slot:
        return -1
    time_str = slot
    if '-' in slot:
        time_str = slot.split('-')[0]
    try:
        minutes = parse_time_to_minutes(time_str)
        return (minutes - 480) // 30
    except:
        return -1

def slots_between(start_slot, end_slot):
    if not start_slot or not end_slot:
        return []
    
    start_str = start_slot
    end_str = end_slot
    
    if '-' in start_slot:
        start_str = start_slot.split('-')[0]
    if '-' in end_slot:
        end_str = end_slot.split('-')[1]
    
    try:
        start_minutes = parse_time_to_minutes(start_str)
        end_minutes = parse_time_to_minutes(end_str)
    except:
        return []
    
    slots = []
    for m in range(start_minutes, end_minutes, 30):
        h = m // 60
        min = m % 60
        slots.append(f'{h:02d}:{min:02d}')
    return slots

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    user_id = request.args.get('userId')
    room_id = request.args.get('roomId')
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    status = request.args.get('status')
    
    conn = get_db()
    c = conn.cursor()
    
    query = 'SELECT b.*, u.name as booker_name FROM bookings b LEFT JOIN users u ON b.user_id = u.id WHERE 1=1'
    params = []
    
    if user_id:
        query += ' AND b.user_id = ?'
        params.append(user_id)
    if room_id:
        query += ' AND b.room_id = ?'
        params.append(room_id)
    if start_date:
        query += ' AND b.start_date <= ?'
        params.append(end_date or start_date)
    if end_date:
        query += ' AND b.end_date >= ?'
        params.append(start_date or end_date)
    if status:
        query += ' AND b.status = ?'
        params.append(status)
    
    query += ' ORDER BY b.start_date, b.start_slot'
    
    c.execute(ph(query), params)
    bookings = []
    for row in c.fetchall():
        row_dict = dict(row)
        booking = {
            'id': row_dict['id'],
            'roomId': row_dict['room_id'],
            'userId': row_dict['user_id'],
            'title': row_dict['title'],
            'bookerName': row_dict.get('booker_name', '') or row_dict.get('bookerName', ''),
            'bookerEmail': '',
            'contactName': row_dict.get('contact_name', '') or row_dict.get('contactName', ''),
            'contactPhone': row_dict.get('contact_phone', '') or row_dict.get('contactPhone', ''),
            'startDate': row_dict['start_date'],
            'endDate': row_dict['end_date'],
            'startSlot': row_dict['start_slot'],
            'endSlot': row_dict['end_slot'],
            'slots': [],
            'note': row_dict.get('note', '') or '',
            'buildId': row_dict.get('build_id') or None,
            'status': row_dict['status'],
            'createdAt': row_dict.get('created_at') or '',
            'approvedBy': row_dict.get('approved_by') or None,
            'approvedAt': row_dict.get('approved_at') or None,
            'cancelledAt': row_dict.get('cancelled_at') or None,
            'cancelReason': row_dict.get('cancel_reason') or ''
        }
        bookings.append(booking)
    
    conn.close()
    return jsonify({'success': True, 'data': bookings})

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(ph('SELECT b.*, u.name as booker_name FROM bookings b LEFT JOIN users u ON b.user_id = u.id WHERE b.id = ?'), (booking_id,))
    booking = c.fetchone()
    conn.close()
    
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    return jsonify({'success': True, 'booking': dict(booking)})

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.json
    
    room_id = data.get('roomId')
    user_id = data.get('userId')
    title = data.get('title', '').strip()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    start_slot = data.get('startSlot')
    end_slot = data.get('endSlot')
    note = data.get('note', '').strip()
    contact_name = data.get('contactName', '').strip()
    contact_phone = data.get('contactPhone', '').strip()
    booker_name = data.get('bookerName', '').strip()
    
    if not room_id or not user_id or not title or not start_date or not end_date:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    if end_date < start_date:
        return jsonify({'success': False, 'message': 'End date cannot be earlier than start date'})
    
    if slot_index(end_slot) < slot_index(start_slot):
        return jsonify({'success': False, 'message': 'End time cannot be earlier than start time'})
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT * FROM rooms WHERE id = ?'), (room_id,))
    room = c.fetchone()
    if not room:
        conn.close()
        return jsonify({'success': False, 'message': 'Room not found'})
    
    c.execute(ph('SELECT * FROM users WHERE id = ?'), (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
    dates = get_date_range(start_date, end_date)
    slots = slots_between(start_slot, end_slot)
    
    conflicts = []
    for date in dates:
        c.execute(ph('''SELECT b.id, u.name as booker_name, b.start_slot, b.end_slot 
                     FROM bookings b LEFT JOIN users u ON b.user_id = u.id
                     WHERE b.room_id = ? AND b.start_date <= ? AND b.end_date >= ?
                     AND b.status IN ('pending', 'approved')'''),
                  (room_id, date, date))
        
        existing_bookings = c.fetchall()
        for eb in existing_bookings:
            eb_slots = slots_between(eb['start_slot'], eb['end_slot'])
            overlapping = set(slots) & set(eb_slots)
            if overlapping:
                conflicts.append({
                    'date': date,
                    'booker': eb['booker_name'],
                    'slots': list(overlapping)
                })
    
    if conflicts:
        conn.close()
        return jsonify({
            'success': False,
            'conflicts': conflicts
        })
    
    booking_id = str(uuid.uuid4())
    
    days = len(dates)
    needs_approval = user['role'] != 'epm' and days > 3
    
    c.execute(ph('''INSERT INTO bookings (id, room_id, user_id, title, start_date, end_date, 
                 start_slot, end_slot, note, status, created_at, contact_name, contact_phone)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''),
              (booking_id, room_id, user_id, title, start_date, end_date,
               start_slot, end_slot, note, 'pending' if needs_approval else 'approved',
               datetime.now().isoformat(), contact_name, contact_phone))
    
    c.execute(ph('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)'''),
              ('Create Booking', f'{title} - {room_id}', user['name'], datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'booking': {
            'id': booking_id,
            'roomId': room_id,
            'userId': user_id,
            'title': title,
            'bookerName': booker_name or user['name'],
            'bookerEmail': user['email'],
            'contactName': contact_name,
            'contactPhone': contact_phone,
            'startDate': start_date,
            'endDate': end_date,
            'startSlot': start_slot,
            'endSlot': end_slot,
            'note': note,
            'status': 'pending' if needs_approval else 'approved'
        },
        'needsApproval': needs_approval,
        'warnings': []
    })

@app.route('/api/bookings/<booking_id>/approve', methods=['PUT'])
def approve_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT * FROM bookings WHERE id = ?'), (booking_id,))
    booking = c.fetchone()
    
    if not booking:
        conn.close()
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    if booking['status'] != 'pending':
        conn.close()
        return jsonify({'success': False, 'message': 'Booking is not pending'})
    
    c.execute(ph('UPDATE bookings SET status = ?, approved_at = ? WHERE id = ?'),
              ('approved', datetime.now().isoformat(), booking_id))
    
    c.execute(ph('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)'''),
              ('Approve Booking', booking['title'], 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Booking approved successfully'})

@app.route('/api/bookings/<booking_id>/reject', methods=['PUT'])
def reject_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT * FROM bookings WHERE id = ?'), (booking_id,))
    booking = c.fetchone()
    
    if not booking:
        conn.close()
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    if booking['status'] != 'pending':
        conn.close()
        return jsonify({'success': False, 'message': 'Booking is not pending'})
    
    c.execute(ph('UPDATE bookings SET status = ?, approved_at = ? WHERE id = ?'),
              ('rejected', datetime.now().isoformat(), booking_id))
    
    c.execute(ph('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)'''),
              ('Reject Booking', booking['title'], 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Booking rejected successfully'})

@app.route('/api/bookings/<booking_id>/cancel', methods=['PUT'])
def cancel_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT * FROM bookings WHERE id = ?'), (booking_id,))
    booking = c.fetchone()
    
    if not booking:
        conn.close()
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    if booking['status'] in ('cancelled', 'rejected'):
        conn.close()
        return jsonify({'success': False, 'message': 'Booking is already cancelled or rejected'})
    
    c.execute(ph('UPDATE bookings SET status = ?, cancelled_at = ? WHERE id = ?'),
              ('cancelled', datetime.now().isoformat(), booking_id))
    
    c.execute(ph('SELECT name FROM users WHERE id = ?'), (booking['user_id'],))
    user = c.fetchone()
    
    c.execute(ph('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)'''),
              ('Cancel Booking', booking['title'], user['name'] if user else 'Unknown', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Booking cancelled successfully'})

@app.route('/api/builds', methods=['GET'])
def get_builds():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM builds ORDER BY created_at DESC')
    builds = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(builds)

@app.route('/api/builds/current', methods=['GET'])
def get_current_build():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM builds WHERE is_current = 1 LIMIT 1')
    build = c.fetchone()
    conn.close()
    
    if not build:
        return jsonify({'success': False, 'message': 'No current build'})
    
    return jsonify({'success': True, 'build': dict(build)})

@app.route('/api/builds', methods=['POST'])
def create_build():
    data = request.json
    name = data.get('name', '').strip()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    
    if not name or not start_date or not end_date:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('UPDATE builds SET is_current = 0 WHERE is_current = 1')
    
    build_id = str(uuid.uuid4())
    c.execute('''INSERT INTO builds (id, name, start_date, end_date, is_current, created_at)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (build_id, name, start_date, end_date, 1, datetime.now().isoformat()))
    
    c.execute('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)''',
              ('Add Build', name, 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Build created successfully', 'buildId': build_id})

@app.route('/api/builds/<build_id>/set-current', methods=['PUT'])
def set_current_build(build_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT * FROM builds WHERE id = ?'), (build_id,))
    build = c.fetchone()
    
    if not build:
        conn.close()
        return jsonify({'success': False, 'message': 'Build not found'})
    
    c.execute('UPDATE builds SET is_current = 0 WHERE is_current = 1')
    c.execute(ph('UPDATE builds SET is_current = 1 WHERE id = ?'), (build_id,))
    
    c.execute(ph('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)'''),
              ('Switch Build', build['name'], 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Build set as current successfully'})

@app.route('/api/builds/<build_id>', methods=['DELETE'])
def delete_build(build_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT * FROM builds WHERE id = ?'), (build_id,))
    build = c.fetchone()
    
    if not build:
        conn.close()
        return jsonify({'success': False, 'message': 'Build not found'})
    
    c.execute(ph('DELETE FROM builds WHERE id = ?'), (build_id,))
    
    c.execute(ph('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)'''),
              ('Delete Build', build['name'], 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Build deleted successfully'})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100')
    logs = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(logs)

@app.route('/api/stats/bookings', methods=['GET'])
def get_booking_stats():
    conn = get_db()
    c = conn.cursor()
    
    c.execute(ph('SELECT COUNT(*) FROM bookings WHERE status = ?'), ('approved',))
    approved = c.fetchone()[0]
    
    c.execute(ph('SELECT COUNT(*) FROM bookings WHERE status = ?'), ('pending',))
    pending = c.fetchone()[0]
    
    c.execute(ph('SELECT COUNT(*) FROM bookings WHERE status = ?'), ('rejected',))
    rejected = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'approved': approved,
        'pending': pending,
        'rejected': rejected,
        'total': approved + pending + rejected
    })

@app.route('/api/buildings', methods=['GET'])
def get_buildings():
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT DISTINCT building FROM rooms ORDER BY building')
    buildings = [row['building'] for row in c.fetchall()]
    conn.close()
    return jsonify(buildings)

@app.route('/')
def index():
    index_path = os.path.join(PROJECT_ROOT, 'index.html')
    print(f'[DEBUG] Looking for index.html at: {index_path}')
    print(f'[DEBUG] Exists: {os.path.exists(index_path)}')
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
        print(f'[DEBUG] index.html loaded, size: {len(content)} bytes')
        return content

@app.route('/<path:path>')
def static_files(path):
    file_path = os.path.join(PROJECT_ROOT, path)
    if os.path.exists(file_path):
        return send_from_directory(PROJECT_ROOT, path)
    return jsonify({'error': 'File not found'}), 404

@app.route('/api/bookings/clear', methods=['DELETE'])
def clear_bookings():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM bookings')
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'All bookings cleared successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

SAMPLE_USERS = [
    {'email': 'bay@example.com', 'name': 'Bay', 'phone': '13822443966'},
    {'email': 'ray@example.com', 'name': 'Ray', 'phone': '506828715'},
    {'email': 'kitsa@example.com', 'name': 'Kitsa', 'phone': '13165713179'},
    {'email': 'chester@example.com', 'name': 'Chester', 'phone': '13538007047'},
    {'email': 'fanxie@example.com', 'name': 'Fan Xie', 'phone': '13549847690'},
    {'email': 'brynn@example.com', 'name': 'Brynn', 'phone': '777896'},
    {'email': 'amber@example.com', 'name': 'Amber', 'phone': '29951'},
    {'email': 'gary@example.com', 'name': 'Gary', 'phone': ''},
    {'email': 'ella@example.com', 'name': 'Ella', 'phone': '89889'},
    {'email': 'govinda@example.com', 'name': 'Govinda', 'phone': '568-86500'},
    {'email': 'rose@example.com', 'name': 'Rose Wang', 'phone': '15807557488'},
    {'email': 'funnycheng@example.com', 'name': 'Funny Cheng', 'phone': '13640901702'},
    {'email': 'melody@example.com', 'name': 'Melody Wei', 'phone': '76972'},
    {'email': 'patty@example.com', 'name': 'Patty', 'phone': '24639'},
    {'email': 'zac@example.com', 'name': 'Zac', 'phone': '13143656064'},
    {'email': 'rachel@example.com', 'name': 'Rachel', 'phone': ''},
    {'email': 'ee_user@example.com', 'name': 'EE User', 'phone': '18576733879'},
]

SAMPLE_BOOKINGS = [
    {'room': 'C01-4F Dumbo', 'title': 'SQE QA Morning Sync w/PQM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Bay'},
    {'room': 'C01-4F Minnie', 'title': 'Others Tritium-B daily sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Ray'},
    {'room': 'C01-4F Bambi', 'title': 'Others RIM DVT & OVB sync up', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Kitsa'},
    {'room': 'C01-4F Elsa', 'title': 'EPM Others Daily Input Outline', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Chester'},
    {'room': 'C01-4F Aurora', 'title': 'KPD Tritium-A Morning Sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Fan Xie'},
    {'room': 'C01-4F Ariel', 'title': 'Others F1 Arc daily Sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Kitsa'},
    {'room': 'C02-4F Clippers', 'title': 'AAE Morning sync up', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Brynn'},
    {'room': 'C02-4F Lakers', 'title': 'EE Daily Sync meeting', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '10:30', 'booker': 'EE User'},
    {'room': 'C02-4F Bulls', 'title': 'KPD Camera pre-Sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Funny Cheng'},
    {'room': 'C02-4F Rockets', 'title': 'KPD FCAM internal Sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:00', 'end_slot': '09:30', 'booker': 'Melody Wei'},
    {'room': 'C01-4F Mickey', 'title': 'RF Daily Morning Sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:30', 'end_slot': '10:00', 'booker': 'Amber'},
    {'room': 'C01-4F Pinocchio', 'title': 'KPD Acoustic Sync daily', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:30', 'end_slot': '10:00', 'booker': 'Gary'},
    {'room': 'C01-4F Goofy', 'title': 'Others RIM FA IT meeting', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:30', 'end_slot': '10:00', 'booker': 'Brynn'},
    {'room': 'C02-4F Cavaliers', 'title': 'Mistral FATP EPM Sync up', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:30', 'end_slot': '10:00', 'booker': 'Rachel'},
    {'room': 'C02-4F Lakers', 'title': 'PD Flex Bending Daily', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:30', 'end_slot': '10:00', 'booker': 'Patty'},
    {'room': 'C02-4F Thunder', 'title': 'Others RIM Daily Sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '09:30', 'end_slot': '10:00', 'booker': 'Kitsa'},
    {'room': 'C01-4F Dumbo', 'title': 'IT DOE Daily meeting', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '10:00', 'end_slot': '10:30', 'booker': 'Ella'},
    {'room': 'C01-4F Minnie', 'title': 'Others RIM FA Meeting', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '10:00', 'end_slot': '10:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Bambi', 'title': 'EERF Sync Meeting', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '10:00', 'end_slot': '10:30', 'booker': 'Amber'},
    {'room': 'C01-4F Aurora', 'title': 'AAE Zac with VM8', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '10:00', 'end_slot': '10:30', 'booker': 'Zac'},
    {'room': 'C02-4F Clippers', 'title': 'EPM Rachel Input Online', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '10:00', 'end_slot': '10:30', 'booker': 'Rachel'},
    {'room': 'C01-4F Goofy', 'title': 'AAE JMP boxplot Meeting', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '11:00', 'end_slot': '11:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Pluto', 'title': 'Others Mistral DFM Sync', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Govinda'},
    {'room': 'C01-4F Minnie', 'title': 'AAE ZAC/ASF cross function', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Elsa', 'title': 'HWTE War Room', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Rose Wang'},
    {'room': 'C01-4F Aurora', 'title': 'AAE Zac with VM8 DFM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Zac'},
    {'room': 'C02-4F Magic', 'title': 'Mistral FATP EPM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Clippers', 'title': 'DOE Meeting Tue & Friday', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Ella'},
    {'room': 'C02-4F Lakers', 'title': 'PCC System Sync up', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Patty'},
    {'room': 'C02-4F Thunder', 'title': 'EPM War Room', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '13:00', 'end_slot': '13:30', 'booker': 'Rachel'},
    {'room': 'C01-4F Mickey', 'title': 'RF Daily FA', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '14:00', 'end_slot': '14:30', 'booker': 'Amber'},
    {'room': 'C01-4F Donald', 'title': 'Mistral MLB EPM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '14:00', 'end_slot': '14:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Clippers', 'title': 'EPM War Room', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '14:00', 'end_slot': '14:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Celtics', 'title': 'EPM War Room', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '14:00', 'end_slot': '14:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Knicks', 'title': 'AAE War Room', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '14:00', 'end_slot': '14:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Pluto', 'title': 'SQE QA pre Sync w/PQM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '16:30', 'end_slot': '17:00', 'booker': 'Bay'},
    {'room': 'C01-4F Goofy', 'title': 'EERF Sync Meeting', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '16:30', 'end_slot': '17:00', 'booker': 'Amber'},
    {'room': 'C01-4F Aurora', 'title': 'Others Tritium-A Wrap up', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '16:30', 'end_slot': '17:00', 'booker': 'Kitsa'},
    {'room': 'C02-4F Clippers', 'title': 'Mistral FATP EPM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '16:30', 'end_slot': '17:00', 'booker': 'Rachel'},
    {'room': 'C02-4F Lakers', 'title': 'AAE Morning Wrap up', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '16:30', 'end_slot': '17:00', 'booker': 'Brynn'},
    {'room': 'C02-4F Rockets', 'title': 'SQE QA pre Sync w/PQM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '16:30', 'end_slot': '17:00', 'booker': 'Bay'},
    {'room': 'C02-4F Clippers', 'title': 'Mistral FATP EPM Wrap up', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '17:00', 'end_slot': '17:30', 'booker': 'Rachel'},
    {'room': 'C01-4F Mickey', 'title': 'Others RIM DVT & OVB', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '17:30', 'end_slot': '18:00', 'booker': 'Kitsa'},
    {'room': 'C02-4F Clippers', 'title': 'Mistral FATP EPM', 'start_date': '7/14', 'end_date': '7/20', 'start_slot': '19:00', 'end_slot': '19:30', 'booker': 'Rachel'},
]

ROOM_MAP = {
    'C01-4F Mickey': 'c01-mickey',
    'C01-4F Donald': 'c01-donald',
    'C01-4F Pluto': 'c01-pluto',
    'C01-4F Dumbo': 'c01-dumbo',
    'C01-4F Pinocchio': 'c01-pinocchio',
    'C01-4F Minnie': 'c01-minnie',
    'C01-4F Goofy': 'c01-goofy',
    'C01-4F Bambi': 'c01-bambi',
    'C01-4F Elsa': 'c01-elsa',
    'C01-4F Aurora': 'c01-aurora',
    'C01-4F Ariel': 'c01-ariel',
    'C02-4F Magic': 'c02-magic',
    'C02-4F Cavaliers': 'c02-cavaliers',
    'C02-4F Clippers': 'c02-clippers',
    'C02-4F Celtics': 'c02-celtics',
    'C02-4F Knicks': 'c02-knicks',
    'C02-4F Lakers': 'c02-lakers',
    'C02-4F Spurs': 'c02-spurs',
    'C02-4F Thunder': 'c02-thunder',
    'C02-4F Bulls': 'c02-bulls',
    'C02-4F Rockets': 'c02-rockets',
}

def parse_date(date_str):
    parts = date_str.split('/')
    if len(parts) == 2:
        return f'{datetime.now().year}-{int(parts[0]):02d}-{int(parts[1]):02d}'
    elif len(parts) == 3:
        return f'{parts[2]}-{int(parts[0]):02d}-{int(parts[1]):02d}'
    return None

@app.route('/api/bookings/import/sample', methods=['POST'])
def import_sample_data():
    try:
        conn = get_db()
        c = conn.cursor()

        user_map = {}
        for user in SAMPLE_USERS:
            c.execute(ph('SELECT id FROM users WHERE email = ?'), (user['email'],))
            existing = c.fetchone()
            if existing:
                user_map[user['name']] = existing['id'] if isinstance(existing, dict) else existing[0]
                continue
            
            user_id = str(uuid.uuid4())
            c.execute(ph('''INSERT INTO users (id, email, name, password, role, created_at)
                         VALUES (?, ?, ?, ?, ?, ?)'''),
                      (user_id, user['email'], user['name'], '123456', 'user', datetime.now().isoformat()))
            user_map[user['name']] = user_id

        conn.commit()

        count = 0
        for booking in SAMPLE_BOOKINGS:
            room_id = ROOM_MAP.get(booking['room'])
            user_id = user_map.get(booking['booker'])
            start_date = parse_date(booking['start_date'])
            end_date = parse_date(booking['end_date'])
            start_slot = booking['start_slot']
            end_slot = booking['end_slot']
            
            if not room_id:
                continue
            if not user_id:
                continue
            if not start_date or not end_date:
                continue

            booking_id = str(uuid.uuid4())
            c.execute(ph('''INSERT INTO bookings (id, room_id, user_id, title, start_date, end_date, 
                         start_slot, end_slot, note, status, created_at, contact_name, contact_phone)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''),
                      (booking_id, room_id, user_id, booking['title'], start_date, end_date,
                       start_slot, end_slot, '', 'approved', datetime.now().isoformat(),
                       user['name'] if user else '', user.get('phone', '') if user else ''))
            count += 1

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'Successfully imported {count} sample bookings'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/bookings/import/undo', methods=['POST'])
def undo_import():
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM bookings WHERE created_at LIKE '2026-07-08%'")
        deleted = c.rowcount
        c.execute("DELETE FROM users WHERE email LIKE '%@example.com'")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Undo completed. Deleted {deleted} bookings.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/qrcode')
def generate_qrcode():
    if not QRCODE_AVAILABLE:
        return jsonify({'success': False, 'message': 'QR code library not installed'}), 500
    
    custom_url = request.args.get('url')
    
    if custom_url:
        qr_url = custom_url
    else:
        scheme = request.headers.get('X-Forwarded-Proto', 'http')
        host = request.headers.get('X-Forwarded-Host', request.host)
        qr_url = f'{scheme}://{host}'
    
    print(f'[DEBUG] Generating QR code for: {qr_url}')
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color='black', back_color='white')
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    response = make_response(img_bytes.read())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = f'inline; filename=qrcode.png'
    
    return response

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 5000))
        print('[DEBUG] Starting Flask server...')
        print(f'[DEBUG] Host: 0.0.0.0')
        print(f'[DEBUG] Port: {port}')
        print('[DEBUG] Debug: False')
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print('[ERROR] Flask server failed to start:', str(e))
        traceback.print_exc()
        sys.exit(1)