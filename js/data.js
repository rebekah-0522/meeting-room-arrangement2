/**
 * Foxconn C01/C02 Meeting Room Data
 */
const EPM_EMAIL = 'rebekah.xy.he@mail.foxconn.com';
const EPM_NAME = 'Rebekah';

const TIME_SLOTS = [
  '08:00-08:30', '08:30-09:00', '09:00-09:30', '09:30-10:00',
  '10:00-10:30', '10:30-11:00', '11:00-11:30', '11:30-12:00',
  '12:00-12:30', '12:30-13:00', '13:00-13:30', '13:30-14:00',
  '14:00-14:30', '14:30-15:00', '15:00-15:30', '15:30-16:00',
  '16:00-16:30', '16:30-17:00', '17:00-17:30', '17:30-18:00',
  '18:00-18:30', '18:30-19:00', '19:00-19:30', '19:30-20:00',
  '20:00-20:30'
];

const TIME_POINTS = [
  '08:00', '08:30', '09:00', '09:30',
  '10:00', '10:30', '11:00', '11:30',
  '12:00', '12:30', '13:00', '13:30',
  '14:00', '14:30', '15:00', '15:30',
  '16:00', '16:30', '17:00', '17:30',
  '18:00', '18:30', '19:00', '19:30',
  '20:00', '20:30'
];

const ROOM_TYPES = {
  normal: { label: 'Normal', color: '#ffffff' },
  epm: { label: 'EPM Only', color: '#fff9c4' },
  warroom: { label: 'War Room', color: '#f5f0e6' }
};

const DEFAULT_ROOMS = [
  // C01-4F - Webex (blue)
  { id: 'c01-mickey', building: 'C01', floor: '4F', name: 'Mickey', capacity: 102, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c01-donald', building: 'C01', floor: '4F', name: 'Donald', capacity: 80, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c01-pluto', building: 'C01', floor: '4F', name: 'Pluto', capacity: 34, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c01-dumbo', building: 'C01', floor: '4F', name: 'Dumbo', capacity: 20, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c01-pinocchio', building: 'C01', floor: '4F', name: 'Pinocchio', capacity: 20, hasWebex: true, hasProjector: true, roomType: 'normal' },
  // C01-4F - No Webex
  { id: 'c01-minnie', building: 'C01', floor: '4F', name: 'Minnie', capacity: 20, hasWebex: false, hasProjector: true, roomType: 'normal' },
  { id: 'c01-goofy', building: 'C01', floor: '4F', name: 'Goofy', capacity: 23, hasWebex: false, hasProjector: true, roomType: 'normal' },
  { id: 'c01-bambi', building: 'C01', floor: '4F', name: 'Bambi', capacity: 24, hasWebex: false, hasProjector: true, roomType: 'normal' },
  { id: 'c01-elsa', building: 'C01', floor: '4F', name: 'Elsa', capacity: 14, hasWebex: false, hasProjector: false, roomType: 'epm' },
  { id: 'c01-aurora', building: 'C01', floor: '4F', name: 'Aurora', capacity: 13, hasWebex: false, hasProjector: false, roomType: 'warroom' },
  { id: 'c01-ariel', building: 'C01', floor: '4F', name: 'Ariel', capacity: 12, hasWebex: false, hasProjector: false, roomType: 'normal' },
  // C02-4F - Webex
  { id: 'c02-magic', building: 'C02', floor: '4F', name: 'Magic', capacity: 102, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c02-cavaliers', building: 'C02', floor: '4F', name: 'Cavaliers', capacity: 80, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c02-clippers', building: 'C02', floor: '4F', name: 'Clippers', capacity: 17, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c02-celtics', building: 'C02', floor: '4F', name: 'Celtics', capacity: 25, hasWebex: true, hasProjector: true, roomType: 'normal' },
  { id: 'c02-knicks', building: 'C02', floor: '4F', name: 'Knicks', capacity: 28, hasWebex: true, hasProjector: true, roomType: 'normal' },
  // C02-4F - No Webex
  { id: 'c02-lakers', building: 'C02', floor: '4F', name: 'Lakers', capacity: 20, hasWebex: false, hasProjector: true, roomType: 'normal' },
  { id: 'c02-spurs', building: 'C02', floor: '4F', name: 'Spurs', capacity: 20, hasWebex: false, hasProjector: false, roomType: 'epm' },
  { id: 'c02-thunder', building: 'C02', floor: '4F', name: 'Thunder', capacity: 13, hasWebex: false, hasProjector: false, roomType: 'warroom' },
  { id: 'c02-bulls', building: 'C02', floor: '4F', name: 'Bulls', capacity: 13, hasWebex: false, hasProjector: false, roomType: 'normal' },
  { id: 'c02-rockets', building: 'C02', floor: '4F', name: 'Rockets', capacity: 14, hasWebex: false, hasProjector: false, roomType: 'normal' }
];

const ROLES = {
  user: 'user',
  leader: 'leader',
  epm: 'epm'
};

const BOOKING_STATUS = {
  pending: 'pending',
  approved: 'approved',
  rejected: 'rejected',
  cancelled: 'cancelled'
};

const MAX_SELF_BOOK_DAYS = 3;
const EPM_ONLY_DAYS = 7;
const MAX_CONSECUTIVE_DAYS = 5;
const LARGE_ROOM_CAPACITY = 40;
const BAD_CREDIT_THRESHOLD = 3;

function formatRoomLabel(room) {
  return `${room.building}-${room.floor} ${room.name}`;
}

function getDateRange(startDate, endDate) {
  const dates = [];
  const current = new Date(startDate);
  const end = new Date(endDate);
  while (current <= end) {
    dates.push(current.toISOString().slice(0, 10));
    current.setDate(current.getDate() + 1);
  }
  return dates;
}

function countDays(startDate, endDate) {
  return getDateRange(startDate, endDate).length;
}

function parseTimeToMinutes(timeStr) {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + minutes;
}

function slotIndex(slot) {
  if (!slot) return -1;
  let timeStr = slot;
  if (slot.includes('-')) {
    timeStr = slot.split('-')[0];
  }
  const minutes = parseTimeToMinutes(timeStr);
  return Math.floor((minutes - 480) / 30);
}

function slotsBetween(startSlot, endSlot) {
  if (!startSlot || !endSlot) return [];
  
  let startStr = startSlot;
  let endStr = endSlot;
  
  if (startSlot.includes('-')) {
    startStr = startSlot.split('-')[0];
  }
  if (endSlot.includes('-')) {
    endStr = endSlot.split('-')[1];
  }
  
  const startMinutes = parseTimeToMinutes(startStr);
  const endMinutes = parseTimeToMinutes(endStr);
  
  const slots = [];
  for (let m = startMinutes; m < endMinutes; m += 30) {
    const h = Math.floor(m / 60);
    const min = m % 60;
    slots.push(`${h.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`);
  }
  return slots;
}

function getWeekStartDate(date) {
  const d = new Date(date);
  const day = d.getDay();
  const monday = new Date(d);
  monday.setDate(d.getDate() - (day === 0 ? 6 : day - 1));
  return monday.toISOString().slice(0, 10);
}

function getWeekDates(baseDate) {
  const date = new Date(baseDate);
  const day = date.getDay();
  const monday = new Date(date);
  monday.setDate(date.getDate() - (day === 0 ? 6 : day - 1));
  const dates = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    dates.push(d.toISOString().slice(0, 10));
  }
  return dates;
}

function getMonthDates(year, month) {
  const dates = [];
  const d = new Date(year, month - 1, 1);
  while (d.getMonth() === month - 1) {
    dates.push(d.toISOString().slice(0, 10));
    d.setDate(d.getDate() + 1);
  }
  return dates;
}

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

function isWeekend(dateStr) {
  const d = new Date(dateStr);
  const day = d.getDay();
  return day === 0 || day === 6;
}
