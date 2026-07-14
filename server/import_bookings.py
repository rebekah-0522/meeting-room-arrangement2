import sqlite3
import uuid
from datetime import datetime

DATABASE = 'meeting_room.db'

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

def parse_date(date_str):
    parts = date_str.split('/')
    if len(parts) == 2:
        return f'2026-{int(parts[0]):02d}-{int(parts[1]):02d}'
    elif len(parts) == 3:
        return f'{parts[2]}-{int(parts[0]):02d}-{int(parts[1]):02d}'
    return None

def parse_time_to_minutes(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes

def get_slot(time_str):
    time_str = time_str.strip().replace('–', '-')
    for slot in TIME_POINTS:
        if slot == time_str or time_str.startswith(slot):
            return slot
    for slot in TIME_SLOTS:
        if slot == time_str or time_str.startswith(slot):
            return slot
    if '-' in time_str:
        parts = time_str.split('-')
        if len(parts) == 2:
            try:
                start_minutes = parse_time_to_minutes(parts[0].strip())
                end_minutes = parse_time_to_minutes(parts[1].strip())
                h = start_minutes // 60
                min = start_minutes % 60
                return f'{h:02d}:{min:02d}'
            except:
                pass
    return None

users_data = [
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

bookings_data = [
    {'room': 'C01-4F Dumbo', 'title': 'SQE QA Morning Sync w/PQM', 'start_date': '6/25', 'end_date': '8/1', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Bay'},
    {'room': 'C01-4F Minnie', 'title': 'Others Tritium-B daily sync up with F1', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Ray'},
    {'room': 'C01-4F Bambi', 'title': 'Others RIM DVT & OVB sync up', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Kitsa'},
    {'room': 'C01-4F Elsa', 'title': 'EPM Others Daily Input Outline Meeting', 'start_date': '7/6', 'end_date': '8/1', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Chester'},
    {'room': 'C01-4F Aurora', 'title': 'KPD Tritium-A Morning Sync with CPT', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Fan Xie'},
    {'room': 'C01-4F Ariel', 'title': 'Others F1 Arc daily Sync with CPT', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Kitsa'},
    {'room': 'C02-4F Clippers', 'title': 'AAE Morning sync up', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Brynn'},
    {'room': 'C02-4F Lakers', 'title': 'EE Daily Sync meeting', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:00-09:30', 'end_slot': '10:00-10:30', 'booker': 'EE User'},
    {'room': 'C02-4F Bulls', 'title': 'KPD Camera pre-Sync with F1', 'start_date': '6/20', 'end_date': '8/19', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Funny Cheng'},
    {'room': 'C02-4F Rockets', 'title': 'KPD FCAM internal Sync meeting', 'start_date': '7/6', 'end_date': '8/7', 'start_slot': '09:00-09:30', 'end_slot': '09:00-09:30', 'booker': 'Melody Wei'},
    {'room': 'C01-4F Mickey', 'title': 'RF Daily Morning Sync', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:30-10:00', 'end_slot': '09:30-10:00', 'booker': 'Amber'},
    {'room': 'C01-4F Pinocchio', 'title': 'KPD Acoustic Sync daily Meeting with CPTN', 'start_date': '6/8', 'end_date': '8/30', 'start_slot': '09:30-10:00', 'end_slot': '09:30-10:00', 'booker': 'Gary'},
    {'room': 'C01-4F Goofy', 'title': 'Others RIM FA IT cross function meeting', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:30-10:00', 'end_slot': '09:30-10:00', 'booker': 'Brynn'},
    {'room': 'C02-4F Cavaliers', 'title': 'Mistral FATP EPM Sync up', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:30-10:00', 'end_slot': '09:30-10:00', 'booker': 'Rachel'},
    {'room': 'C02-4F Lakers', 'title': 'PD Flex Bending Daily meeting W/ TPM Others', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '09:30-10:00', 'end_slot': '09:30-10:00', 'booker': 'Patty'},
    {'room': 'C02-4F Thunder', 'title': 'Others RIM Daily Sync up with AME Others', 'start_date': '6/25', 'end_date': '8/30', 'start_slot': '09:30-10:00', 'end_slot': '09:30-10:00', 'booker': 'Kitsa'},
    {'room': 'C01-4F Dumbo', 'title': 'IT DOE Daily meeting Others', 'start_date': '6/25', 'end_date': '7/31', 'start_slot': '10:00-10:30', 'end_slot': '10:00-10:30', 'booker': 'Ella'},
    {'room': 'C01-4F Minnie', 'title': 'Others RIM FA Meeting Others', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '10:00-10:30', 'end_slot': '10:00-10:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Bambi', 'title': 'EERF Sync Meeting', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '10:00-10:30', 'end_slot': '10:00-10:30', 'booker': 'Amber'},
    {'room': 'C01-4F Aurora', 'title': 'AAE Zac with VM8, DFM report, ZAC with PD function Others', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '10:00-10:30', 'end_slot': '10:00-10:30', 'booker': 'Zac'},
    {'room': 'C02-4F Clippers', 'title': 'EPM Rachel Input Online Others', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '10:00-10:30', 'end_slot': '10:00-10:30', 'booker': 'Rachel'},
    {'room': 'C01-4F Goofy', 'title': 'AAE JMP boxplot Meeting Others', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '11:00-11:30', 'end_slot': '11:00-11:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Pluto', 'title': 'Others Mistral DFM Sync up & Wrap up & TPM daily work', 'start_date': '6/1', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Govinda'},
    {'room': 'C01-4F Minnie', 'title': 'AAE ZAC/ASF cross function Others', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Elsa', 'title': 'HWTE War Room', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Rose Wang'},
    {'room': 'C01-4F Aurora', 'title': 'AAE Zac with VM8, DFM report, ZAC with PD Others', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Zac'},
    {'room': 'C02-4F Magic', 'title': 'Mistral FATP EPM', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Clippers', 'title': 'DOE Meeting Tue & Friday', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Ella'},
    {'room': 'C02-4F Lakers', 'title': 'PCC System Sync up Meeting', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Patty'},
    {'room': 'C02-4F Thunder', 'title': 'EPM War Room', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '13:00-13:30', 'end_slot': '13:00-13:30', 'booker': 'Rachel'},
    {'room': 'C01-4F Mickey', 'title': 'RF Daily FA', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '14:00-14:30', 'end_slot': '14:00-14:30', 'booker': 'Amber'},
    {'room': 'C01-4F Donald', 'title': 'Mistral MLB EPM', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '14:00-14:30', 'end_slot': '14:00-14:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Clippers', 'title': 'EPM War Room', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '14:00-14:30', 'end_slot': '14:00-14:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Celtics', 'title': 'EPM War Room', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '14:00-14:30', 'end_slot': '14:00-14:30', 'booker': 'Rachel'},
    {'room': 'C02-4F Knicks', 'title': 'AAE War Room', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '14:00-14:30', 'end_slot': '14:00-14:30', 'booker': 'Brynn'},
    {'room': 'C01-4F Pluto', 'title': 'SQE QA pre Sync w/PQM', 'start_date': '6/25', 'end_date': '8/1', 'start_slot': '16:30-17:00', 'end_slot': '16:30-17:00', 'booker': 'Bay'},
    {'room': 'C01-4F Goofy', 'title': 'EERF Sync Meeting', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '16:30-17:00', 'end_slot': '16:30-17:00', 'booker': 'Amber'},
    {'room': 'C01-4F Aurora', 'title': 'Others Tritium-A Wrap up', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '16:30-17:00', 'end_slot': '16:30-17:00', 'booker': 'Kitsa'},
    {'room': 'C02-4F Clippers', 'title': 'Mistral FATP EPM', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '16:30-17:00', 'end_slot': '16:30-17:00', 'booker': 'Rachel'},
    {'room': 'C02-4F Lakers', 'title': 'AAE Morning Wrap up', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '16:30-17:00', 'end_slot': '16:30-17:00', 'booker': 'Brynn'},
    {'room': 'C02-4F Rockets', 'title': 'SQE QA pre Sync w/PQM', 'start_date': '6/25', 'end_date': '8/1', 'start_slot': '16:30-17:00', 'end_slot': '16:30-17:00', 'booker': 'Bay'},
    {'room': 'C02-4F Clippers', 'title': 'Mistral FATP EPM Wrap up', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '17:00-17:30', 'end_slot': '17:00-17:30', 'booker': 'Rachel'},
    {'room': 'C01-4F Mickey', 'title': 'Others RIM DVT & OVB', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '17:30-18:00', 'end_slot': '17:30-18:00', 'booker': 'Kitsa'},
    {'room': 'C02-4F Clippers', 'title': 'Mistral FATP EPM', 'start_date': '6/22', 'end_date': '8/30', 'start_slot': '19:00-19:30', 'end_slot': '19:00-19:30', 'booker': 'Rachel'},
]

def main():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    print('Creating users...')
    user_map = {}
    for user in users_data:
        c.execute('SELECT id FROM users WHERE email = ?', (user['email'],))
        existing = c.fetchone()
        if existing:
            user_map[user['name']] = existing[0]
            print(f'  User {user["name"]} already exists')
            continue
        
        user_id = str(uuid.uuid4())
        c.execute('''INSERT INTO users (id, email, name, password, role, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)''',
                  (user_id, user['email'], user['name'], '123456', 'user', datetime.now().isoformat()))
        user_map[user['name']] = user_id
        print(f'  Created user: {user["name"]}')
    
    conn.commit()
    
    print('\nCreating bookings...')
    count = 0
    for booking in bookings_data:
        room_id = ROOM_MAP.get(booking['room'])
        user_id = user_map.get(booking['booker'])
        start_date = parse_date(booking['start_date'])
        end_date = parse_date(booking['end_date'])
        start_slot = get_slot(booking['start_slot'])
        end_slot = get_slot(booking['end_slot'])
        
        if not room_id:
            print(f'  Skipping {booking["room"]}: Room not found')
            continue
        if not user_id:
            print(f'  Skipping {booking["title"]}: User {booking["booker"]} not found')
            continue
        if not start_date or not end_date:
            print(f'  Skipping {booking["title"]}: Invalid date')
            continue
        if not start_slot or not end_slot:
            print(f'  Skipping {booking["title"]}: Invalid time slot')
            continue
        
        booking_id = str(uuid.uuid4())
        c.execute('''INSERT INTO bookings (id, room_id, user_id, title, start_date, end_date, 
                     start_slot, end_slot, note, status, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (booking_id, room_id, user_id, booking['title'], start_date, end_date,
                   start_slot, end_slot, '', 'approved', datetime.now().isoformat()))
        count += 1
        print(f'  Created booking: {booking["room"]} - {booking["title"]}')
    
    conn.commit()
    conn.close()
    
    print(f'\nImport completed! Created {count} bookings.')

if __name__ == '__main__':
    main()
