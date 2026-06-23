from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
import sqlite3
import json
import uuid
import sys
import traceback
import os
from datetime import datetime

print('[DEBUG] Starting Flask application...')
print('[DEBUG] Python version:', sys.version)

# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root
PROJECT_ROOT = os.path.dirname(BASE_DIR)

print(f'[DEBUG] Project root: {PROJECT_ROOT}')

app = Flask(__name__, static_folder=PROJECT_ROOT, static_url_path='')
CORS(app)

DATABASE = os.path.join(BASE_DIR, 'meeting_room.db')
print(f'[DEBUG] Database path: {DATABASE}')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        print('[DEBUG] Initializing database...')
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        print('[DEBUG] Creating users table...')
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
        
        print('[DEBUG] Creating builds table...')
        c.execute('''CREATE TABLE IF NOT EXISTS builds
                     (id TEXT PRIMARY KEY, name TEXT, start_date TEXT, end_date TEXT,
                      is_current INTEGER DEFAULT 0, created_at TEXT)''')
        
        print('[DEBUG] Creating logs table...')
        c.execute('''CREATE TABLE IF NOT EXISTS logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, detail TEXT,
                      operator TEXT, timestamp TEXT)''')
        
        print('[DEBUG] Creating notifications table...')
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
    
        c.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('rebekah.xy.he@mail.foxconn.com',))
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO users (id, email, name, password, role, created_at)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (str(uuid.uuid4()), 'rebekah.xy.he@mail.foxconn.com', 'Rebekah', '123456', 'epm', datetime.now().isoformat()))
            print('[DEBUG] Default user added')
    
        conn.commit()
        conn.close()
        print('[DEBUG] Default data initialized successfully')
    except Exception as e:
        print('[ERROR] Default data initialization failed:', str(e))
        traceback.print_exc()

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
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})
    
    stored_password = user['password'] or '123456'
    
    if password != stored_password:
        return jsonify({'success': False, 'message': 'Incorrect password'})
    
    role = user['role']
    if email == 'rebekah.xy.he@mail.foxconn.com':
        role = 'epm'
    
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
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM users WHERE email = ?', (email,))
    if c.fetchone()[0] > 0:
        conn.close()
        return jsonify({'success': False, 'message': 'User already exists'})
    
    user_id = str(uuid.uuid4())
    c.execute('''INSERT INTO users (id, email, name, password, role, credit, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (user_id, email, data.get('name', email.split('@')[0]), 
               data.get('password', '123456'), data.get('role', 'user'), 0,
               datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'User created successfully'})

@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, email, name, role, credit FROM users WHERE id = ?', (user_id,))
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
    
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE id = ?', (new_password, user_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Password updated successfully'})

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    building = request.args.get('building')
    
    conn = get_db()
    c = conn.cursor()
    
    if building:
        c.execute('SELECT * FROM rooms WHERE building = ?', (building,))
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
    c.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
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
        c.execute(f'UPDATE rooms SET {", ".join(updates)} WHERE id = ?', params)
        conn.commit()
    
    conn.close()
    
    return jsonify({'success': True, 'message': 'Room updated successfully'})

def get_date_range(start_date, end_date):
    dates = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current = current.replace(day=current.day + 1)
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

def slot_index(slot):
    return TIME_SLOTS.index(slot)

def slots_between(start_slot, end_slot):
    start = slot_index(start_slot)
    end = slot_index(end_slot)
    if start == -1 or end == -1 or end < start:
        return []
    return TIME_SLOTS[start:end+1]

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
    
    c.execute(query, params)
    bookings = []
    for row in c.fetchall():
        booking = dict(row)
        bookings.append(booking)
    
    conn.close()
    return jsonify(bookings)

@app.route('/api/bookings/<booking_id>', methods=['GET'])
def get_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT b.*, u.name as booker_name FROM bookings b LEFT JOIN users u ON b.user_id = u.id WHERE b.id = ?', (booking_id,))
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
    
    if not room_id or not user_id or not title or not start_date or not end_date:
        return jsonify({'success': False, 'message': 'Missing required fields'})
    
    if end_date < start_date:
        return jsonify({'success': False, 'message': 'End date cannot be earlier than start date'})
    
    if slot_index(end_slot) < slot_index(start_slot):
        return jsonify({'success': False, 'message': 'End time cannot be earlier than start time'})
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
    room = c.fetchone()
    if not room:
        conn.close()
        return jsonify({'success': False, 'message': 'Room not found'})
    
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'})
    
    dates = get_date_range(start_date, end_date)
    slots = slots_between(start_slot, end_slot)
    
    conflicts = []
    for date in dates:
        c.execute('''SELECT b.id, u.name as booker_name, b.start_slot, b.end_slot 
                     FROM bookings b LEFT JOIN users u ON b.user_id = u.id
                     WHERE b.room_id = ? AND b.start_date <= ? AND b.end_date >= ?
                     AND b.status IN ('pending', 'approved')''',
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
    needs_approval = user['role'] != 'epm'
    
    c.execute('''INSERT INTO bookings (id, room_id, user_id, title, start_date, end_date, 
                 start_slot, end_slot, note, status, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (booking_id, room_id, user_id, title, start_date, end_date,
               start_slot, end_slot, note, 'pending' if needs_approval else 'approved',
               datetime.now().isoformat()))
    
    c.execute('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)''',
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
            'startDate': start_date,
            'endDate': end_date,
            'startSlot': start_slot,
            'endSlot': end_slot,
            'note': note,
            'status': 'pending' if needs_approval else 'approved',
            'booker': user['name']
        },
        'needsApproval': needs_approval,
        'warnings': []
    })

@app.route('/api/bookings/<booking_id>/approve', methods=['PUT'])
def approve_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    booking = c.fetchone()
    
    if not booking:
        conn.close()
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    if booking['status'] != 'pending':
        conn.close()
        return jsonify({'success': False, 'message': 'Booking is not pending'})
    
    c.execute('UPDATE bookings SET status = ?, approved_at = ? WHERE id = ?',
              ('approved', datetime.now().isoformat(), booking_id))
    
    c.execute('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)''',
              ('Approve Booking', booking['title'], 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Booking approved successfully'})

@app.route('/api/bookings/<booking_id>/reject', methods=['PUT'])
def reject_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    booking = c.fetchone()
    
    if not booking:
        conn.close()
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    if booking['status'] != 'pending':
        conn.close()
        return jsonify({'success': False, 'message': 'Booking is not pending'})
    
    c.execute('UPDATE bookings SET status = ?, approved_at = ? WHERE id = ?',
              ('rejected', datetime.now().isoformat(), booking_id))
    
    c.execute('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)''',
              ('Reject Booking', booking['title'], 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Booking rejected successfully'})

@app.route('/api/bookings/<booking_id>/cancel', methods=['PUT'])
def cancel_booking(booking_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    booking = c.fetchone()
    
    if not booking:
        conn.close()
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    if booking['status'] in ('cancelled', 'rejected'):
        conn.close()
        return jsonify({'success': False, 'message': 'Booking is already cancelled or rejected'})
    
    c.execute('UPDATE bookings SET status = ?, cancelled_at = ? WHERE id = ?',
              ('cancelled', datetime.now().isoformat(), booking_id))
    
    c.execute('SELECT name FROM users WHERE id = ?', (booking['user_id'],))
    user = c.fetchone()
    
    c.execute('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)''',
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
    
    c.execute('SELECT * FROM builds WHERE id = ?', (build_id,))
    build = c.fetchone()
    
    if not build:
        conn.close()
        return jsonify({'success': False, 'message': 'Build not found'})
    
    c.execute('UPDATE builds SET is_current = 0 WHERE is_current = 1')
    c.execute('UPDATE builds SET is_current = 1 WHERE id = ?', (build_id,))
    
    c.execute('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)''',
              ('Switch Build', build['name'], 'EPM', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Build set as current successfully'})

@app.route('/api/builds/<build_id>', methods=['DELETE'])
def delete_build(build_id):
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM builds WHERE id = ?', (build_id,))
    build = c.fetchone()
    
    if not build:
        conn.close()
        return jsonify({'success': False, 'message': 'Build not found'})
    
    c.execute('DELETE FROM builds WHERE id = ?', (build_id,))
    
    c.execute('''INSERT INTO logs (action, detail, operator, timestamp)
                 VALUES (?, ?, ?, ?)''',
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
    
    c.execute('SELECT COUNT(*) FROM bookings WHERE status = ?', ('approved',))
    approved = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM bookings WHERE status = ?', ('pending',))
    pending = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM bookings WHERE status = ?', ('rejected',))
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

if __name__ == '__main__':
    try:
        print('[DEBUG] Starting Flask server...')
        print('[DEBUG] Host: 0.0.0.0')
        print('[DEBUG] Port: 5000')
        print('[DEBUG] Debug: False')
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print('[ERROR] Flask server failed to start:', str(e))
        traceback.print_exc()
        input('Press Enter to exit...')