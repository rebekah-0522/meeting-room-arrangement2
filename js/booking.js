/**
 * Booking logic, permissions, conflicts
 */

function getCurrentUser() {
  let raw = sessionStorage.getItem('currentUser');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setCurrentUser(user) {
  sessionStorage.setItem('currentUser', JSON.stringify(user));
  if (user?.email) {
    const record = getUserRecord(user.email);
    record.name = user.name || record.name;
    if (user.role) record.role = user.role;
    saveUserRecord(record);
  }
}

function clearCurrentUser() {
  sessionStorage.removeItem('currentUser');
}

function isValidPhone(phone) {
  phone = phone.replace(/\s+/g, '');
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    return false;
  }
  const prefix = phone.substring(0, 3);
  const validPrefixes = [
    '130', '131', '132', '133', '134', '135', '136', '137', '138', '139',
    '145', '147', '148',
    '150', '151', '152', '153', '155', '156', '157', '158', '159',
    '162', '165', '166', '167',
    '170', '171', '172', '173', '174', '175', '176', '177', '178', '179',
    '180', '181', '182', '183', '184', '185', '186', '187', '188', '189',
    '191', '192', '193', '195', '196', '197', '198', '199'
  ];
  return validPrefixes.includes(prefix);
}

function isEPM(user) {
  if (!user) return false;
  return user.role === ROLES.epm || user.email?.toLowerCase() === EPM_EMAIL.toLowerCase();
}

function isLeader(user) {
  if (!user) return false;
  return isEPM(user) || user.role === ROLES.leader;
}

function getEffectiveRole(user) {
  if (!user) return null;
  const record = getUserRecord(user.email);
  return record.role || user.role || ROLES.user;
}

function canBookRoom(user, room) {
  return { allowed: true };
}

function needsApproval(user, startDate, endDate, room) {
  const days = countDays(startDate, endDate);
  if (isEPM(user)) return { required: false, reason: '' };
  if (isBadCredit(user.email)) {
    return { required: true, reason: 'Bad credit record (more than 3 cancellations this month). Booking requires Meeting EPM approval.' };
  }
  if (days >= MAX_SELF_BOOK_DAYS) {
    return { required: true, reason: `Booking is ${days} days (≥ ${MAX_SELF_BOOK_DAYS} days). Waiting for Meeting EPM approval.` };
  }
  if (room && room.capacity >= LARGE_ROOM_CAPACITY) {
    return { required: true, reason: `Room capacity ${room.capacity} (≥ ${LARGE_ROOM_CAPACITY}). Waiting for Meeting EPM approval.` };
  }
  return { required: false, reason: '' };
}

function getBookingWarnings(startDate, endDate) {
  const days = countDays(startDate, endDate);
  const warnings = [];
  return warnings;
}

function canDirectEdit(user, startDate, endDate) {
  if (isEPM(user)) return true;
  const days = countDays(startDate, endDate);
  return days <= MAX_SELF_BOOK_DAYS;
}

function getActiveBookings() {
  return appState.bookings.filter(b =>
    b.status === BOOKING_STATUS.approved || b.status === BOOKING_STATUS.pending
  );
}

function bookingOccupiesSlot(booking, date, slot) {
  if (booking.status === BOOKING_STATUS.cancelled || booking.status === BOOKING_STATUS.rejected) {
    return false;
  }
  const dates = getDateRange(booking.startDate, booking.endDate);
  if (!dates.includes(date)) return false;
  const slots = booking.slots || slotsBetween(booking.startSlot, booking.endSlot);
  return slots.includes(slot);
}

function findConflicts(roomId, startDate, endDate, startSlot, endSlot, excludeId) {
  const dates = getDateRange(startDate, endDate);
  const slots = slotsBetween(startSlot, endSlot);
  const conflicts = [];

  getActiveBookings().forEach(booking => {
    if (booking.id === excludeId) return;
    if (booking.roomId !== roomId) return;
    dates.forEach(date => {
      slots.forEach(slot => {
        if (bookingOccupiesSlot(booking, date, slot)) {
          conflicts.push({
            booking,
            date,
            slot,
            booker: booking.bookerName || booking.bookerEmail
          });
        }
      });
    });
  });

  const unique = [];
  const seen = new Set();
  conflicts.forEach(c => {
    const key = `${c.booking.id}_${c.date}_${c.slot}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(c);
    }
  });
  return unique;
}

function summarizeConflicts(conflicts) {
  const map = {};
  conflicts.forEach(c => {
    const key = `${c.date}|${c.booker}`;
    if (!map[key]) map[key] = { date: c.date, booker: c.booker, slots: new Set() };
    map[key].slots.add(c.slot);
  });
  return Object.values(map).map(item => ({
    date: item.date,
    booker: item.booker,
    slots: [...item.slots]
  }));
}

function createBooking(payload, user, options = {}) {
  console.log('createBooking called with:', payload, 'user:', user);
  const { roomId, title, startDate, endDate, startSlot, endSlot, note, buildId, contactName, contactPhone, bookerName } = payload;
  const room = getRoomById(roomId);
  if (!room) throw new Error('会议室不存在');

  const roomCheck = canBookRoom(user, room);
  if (!roomCheck.allowed) throw new Error(roomCheck.reason);

  const days = countDays(startDate, endDate);

  if (!contactName || !contactName.trim()) {
    throw new Error('请填写会议预约人姓名');
  }
  if (!contactPhone || !contactPhone.trim()) {
    throw new Error('请填写联系方式');
  }
  if (!isValidPhone(contactPhone)) {
    throw new Error('无效的手机号码，请输入11位有效的中国移动、联通或电信手机号');
  }

  const approval = needsApproval(user, startDate, endDate, room);
  const conflicts = findConflicts(roomId, startDate, endDate, startSlot, endSlot);

  if (conflicts.length > 0 && !options.forceOverwrite) {
    return { success: false, conflicts: summarizeConflicts(conflicts) };
  }

  if (conflicts.length > 0 && options.forceOverwrite) {
    conflicts.forEach(c => {
      const b = appState.bookings.find(x => x.id === c.booking.id);
      if (b) {
        b.status = BOOKING_STATUS.cancelled;
        b.cancelReason = `被 ${user.name || user.email} 导入覆盖`;
        addLog('覆盖取消', `${formatRoomLabel(room)} ${c.date} 原预约人 ${c.booker}`, user.name || user.email);
      }
    });
  }

  const status = approval.required ? BOOKING_STATUS.pending : BOOKING_STATUS.approved;
  const booking = {
    id: generateId('bk'),
    roomId,
    title: title || '会议',
    bookerName: bookerName || user.name,
    bookerEmail: user.email,
    contactName: contactName.trim(),
    contactPhone: contactPhone.replace(/\s+/g, ''),
    startDate,
    endDate,
    startSlot,
    endSlot,
    slots: slotsBetween(startSlot, endSlot),
    note: note || '',
    buildId: buildId || appState.currentBuildId,
    status,
    createdAt: new Date().toISOString(),
    approvedBy: status === BOOKING_STATUS.approved ? (user.name || user.email) : null,
    approvedAt: status === BOOKING_STATUS.approved ? new Date().toISOString() : null
  };

  console.log('Creating booking:', booking);
  appState.bookings.push(booking);
  saveState(appState);

  addLog(
    status === BOOKING_STATUS.pending ? '提交预约申请' : '创建预约',
    `${formatRoomLabel(room)} ${startDate}~${endDate} ${startSlot}-${endSlot} 「${booking.title}」`,
    user.name || user.email
  );

  const warnings = getBookingWarnings(startDate, endDate);

  if (status === BOOKING_STATUS.pending) {
    addNotification({
      type: 'approval_request',
      targetEmail: EPM_EMAIL,
      title: '新预约待审批',
      message: `${user.name} (${user.email}) 申请 ${formatRoomLabel(room)} ${startDate}~${endDate}`,
      bookingId: booking.id
    });
  }

  console.log('Booking created successfully, returning result');
  return { success: true, booking, warnings, needsApproval: approval.required };
}

function approveBooking(bookingId, approver) {
  const booking = appState.bookings.find(b => b.id === bookingId);
  if (!booking) throw new Error('预约不存在');
  if (booking.status !== BOOKING_STATUS.pending) throw new Error('该预约不在待审批状态');

  const conflicts = findConflicts(booking.roomId, booking.startDate, booking.endDate, booking.startSlot, booking.endSlot, bookingId);
  if (conflicts.length > 0) {
    return { success: false, conflicts: summarizeConflicts(conflicts) };
  }

  booking.status = BOOKING_STATUS.approved;
  booking.approvedBy = approver.name || approver.email;
  booking.approvedAt = new Date().toISOString();
  saveState(appState);

  const room = getRoomById(booking.roomId);
  addLog('审批通过', `${formatRoomLabel(room)} ${booking.startDate}~${booking.endDate} 预约人 ${booking.bookerName}`, approver.name || approver.email);

  addNotification({
    type: 'approved',
    targetEmail: booking.bookerEmail,
    title: '预约已通过',
    message: `您的 ${formatRoomLabel(room)} 预约已批准`,
    bookingId: booking.id
  });

  sendEmailNotification({
    to: booking.bookerEmail,
    subject: `[已通过] 会议室预约 - ${formatRoomLabel(room)}`,
    body: buildEmailBody('approved', booking, { name: booking.bookerName, email: booking.bookerEmail }, room, [])
  });

  return { success: true, booking };
}

function rejectBooking(bookingId, approver, reason) {
  const booking = appState.bookings.find(b => b.id === bookingId);
  if (!booking) throw new Error('预约不存在');

  booking.status = BOOKING_STATUS.rejected;
  booking.rejectReason = reason || 'EPM 未通过';
  booking.approvedBy = approver.name || approver.email;
  booking.approvedAt = new Date().toISOString();
  saveState(appState);

  const room = getRoomById(booking.roomId);
  addLog('审批拒绝', `${formatRoomLabel(room)} 预约人 ${booking.bookerName}`, approver.name || approver.email);

  sendEmailNotification({
    to: booking.bookerEmail,
    subject: `[未通过] 会议室预约 - ${formatRoomLabel(room)}`,
    body: buildEmailBody('rejected', booking, { name: booking.bookerName, email: booking.bookerEmail }, room, [reason])
  });

  return { success: true, booking };
}

function cancelBooking(bookingId, user, reason) {
  const booking = appState.bookings.find(b => b.id === bookingId);
  if (!booking) throw new Error('预约不存在');

  const isOwner = booking.bookerEmail?.toLowerCase() === user.email?.toLowerCase();
  if (!isOwner && !isEPM(user)) throw new Error('无权取消此预约');

  booking.status = BOOKING_STATUS.cancelled;
  booking.cancelReason = reason || '用户取消';
  booking.cancelledAt = new Date().toISOString();
  saveState(appState);

  if (isOwner && !isEPM(user)) {
    recordCancellation(user.email);
  }

  const room = getRoomById(booking.roomId);
  addLog('取消预约', `${formatRoomLabel(room)} ${booking.startDate}~${booking.endDate}`, user.name || user.email);

  return { success: true, booking, badCredit: isBadCredit(user.email) };
}

function deleteBooking(bookingId, user) {
  if (!isEPM(user)) throw new Error('仅 Meeting EPM 可删除预约记录');
  const idx = appState.bookings.findIndex(b => b.id === bookingId);
  if (idx === -1) throw new Error('预约不存在');
  const booking = appState.bookings[idx];
  appState.bookings.splice(idx, 1);
  saveState(appState);
  const room = getRoomById(booking.roomId);
  addLog('删除预约', `${formatRoomLabel(room)} ${booking.startDate}`, user.name || user.email);
  return booking;
}

function getBookingsForDate(date, buildingFilter, roomFilter) {
  return getActiveBookings().filter(b => {
    const dates = getDateRange(b.startDate, b.endDate);
    if (!dates.includes(date)) return false;
    if (buildingFilter && buildingFilter !== 'all') {
      const room = getRoomById(b.roomId);
      if (room?.building !== buildingFilter) return false;
    }
    if (roomFilter && roomFilter !== 'all') {
      if (b.roomId !== roomFilter) return false;
    }
    return true;
  });
}

function getBookingsForRoomDate(roomId, date) {
  return getActiveBookings().filter(b => bookingOccupiesSlot(b, date, TIME_POINTS[0]) || getDateRange(b.startDate, b.endDate).includes(date) && b.roomId === roomId);
}

function buildBookingIndex() {
  const index = new Map();
  getActiveBookings().forEach(b => {
    const dates = getDateRange(b.startDate, b.endDate);
    const slots = b.slots || slotsBetween(b.startSlot, b.endSlot);
    dates.forEach(date => {
      slots.forEach(slot => {
        const key = `${b.roomId}_${date}_${slot}`;
        if (!index.has(key)) {
          index.set(key, b);
        }
      });
    });
  });
  return index;
}

let bookingIndex = null;
let lastIndexTime = 0;

function getSlotStatus(roomId, date, slot) {
  const now = Date.now();
  if (!bookingIndex || now - lastIndexTime > 1000) {
    bookingIndex = buildBookingIndex();
    lastIndexTime = now;
  }
  const key = `${roomId}_${date}_${slot}`;
  const booking = bookingIndex.get(key);
  if (!booking) return { status: 'free', booking: null };
  return {
    status: booking.status === BOOKING_STATUS.pending ? 'pending' : 'booked',
    booking
  };
}

function buildEmailBody(type, booking, user, room, extras) {
  const lines = [
    'Foxconn Meeting Room Booking System',
    '---',
    `Room: ${formatRoomLabel(room)}`,
    `Meeting Title: ${booking.title}`,
    `Booker: ${user.name} (${user.email})`,
    `Date: ${booking.startDate} ~ ${booking.endDate}`,
    `Time: ${booking.startSlot} - ${booking.endSlot}`,
    `Status: ${booking.status}`,
  ];
  if (extras?.length) {
    lines.push('---', ...extras);
  }
  lines.push('---', `For special requests, please contact Meeting EPM ${EPM_NAME}: ${EPM_EMAIL}`);
  return lines.join('\n');
}

function sendEmailNotification({ to, subject, body }) {
  const mailLog = {
    id: generateId('mail'),
    to,
    subject,
    body,
    sentAt: new Date().toISOString(),
    method: 'simulated'
  };
  if (!appState.mailLog) appState.mailLog = [];
  appState.mailLog.unshift(mailLog);
  if (appState.mailLog.length > 100) appState.mailLog = appState.mailLog.slice(0, 100);
  saveState(appState);

  console.info('[邮件模拟]', subject, '→', to);
  return mailLog;
}

function getRecentMailLog(limit = 10) {
  return (appState.mailLog || []).slice(0, limit);
}
