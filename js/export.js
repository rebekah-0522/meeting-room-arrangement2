/**
 * CSV / Excel export utilities
 */

function escapeCSV(value) {
  const str = String(value ?? '');
  if (/[",\n\r]/.test(str)) return `"${str.replace(/"/g, '""')}"`;
  return str;
}

function downloadCSV(filename, rows) {
  const bom = '\uFEFF';
  const content = bom + rows.map(row => row.map(escapeCSV).join(',')).join('\r\n');
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportWeeklySchedule(weekStartDate, buildingFilter) {
  const dates = getWeekDates(weekStartDate);
  const rooms = appState.rooms.filter(r => !buildingFilter || buildingFilter === 'all' || r.building === buildingFilter);
  const header = ['会议室', '楼栋', '容量', 'Webex', '投影仪', '类型', ...dates.flatMap(d => TIME_POINTS.slice(0, -1).map(s => `${d} ${s}`))];
  const rows = [header];

  rooms.forEach(room => {
    const row = [
      room.name,
      `${room.building}-${room.floor}`,
      room.capacity,
      room.hasWebex ? '是' : '否',
      room.hasProjector ? '是' : '否',
      ROOM_TYPES[room.roomType]?.label || '普通',
    ];
    dates.forEach(date => {
      TIME_POINTS.slice(0, -1).forEach(slot => {
        const { status, booking } = getSlotStatus(room.id, date, slot);
        if (status === 'free') row.push('');
        else row.push(`${booking.bookerName || booking.bookerEmail} - ${booking.title}${status === 'pending' ? '(待审)' : ''}`);
      });
    });
    rows.push(row);
  });

  downloadCSV(`会议室周排期_${dates[0]}_${dates[6]}.csv`, rows);
  addLog('导出周排期', `${dates[0]} ~ ${dates[6]}`, getCurrentUser()?.name || '未知');
}

function exportBuildSchedule(buildId) {
  const build = getBuildById(buildId);
  if (!build) throw new Error('Build 不存在');

  const bookings = appState.bookings.filter(b =>
    b.buildId === buildId &&
    b.status !== BOOKING_STATUS.cancelled &&
    b.status !== BOOKING_STATUS.rejected
  );

  const header = ['Build', '会议室', '楼栋', '容量', 'Webex', '预约人', '邮箱', '主题', '开始日期', '结束日期', '开始时段', '结束时段', '状态', '备注'];
  const rows = [header];

  bookings.sort((a, b) => a.startDate.localeCompare(b.startDate)).forEach(b => {
    const room = getRoomById(b.roomId);
    rows.push([
      build.name,
      room?.name || '',
      room ? `${room.building}-${room.floor}` : '',
      room?.capacity || '',
      room?.hasWebex ? '是' : '否',
      b.bookerName,
      b.bookerEmail,
      b.title,
      b.startDate,
      b.endDate,
      b.startSlot,
      b.endSlot,
      b.status,
      b.note || ''
    ]);
  });

  downloadCSV(`Build排期_${build.name}_${build.startDate}.csv`, rows);
  addLog('导出 Build 排期', build.name, getCurrentUser()?.name || '未知');
}

function exportMonthlySchedule(year, month, buildingFilter) {
  const dates = getMonthDates(year, month);
  const rooms = appState.rooms.filter(r => !buildingFilter || buildingFilter === 'all' || r.building === buildingFilter);

  const header = ['日期', '时段', '会议室', '楼栋', '容量', 'Webex', '投影仪', '预约人', '邮箱', '主题', '状态', '备注'];
  const rows = [header];

  dates.forEach(date => {
    TIME_POINTS.slice(0, -1).forEach(slot => {
      rooms.forEach(room => {
        const { status, booking } = getSlotStatus(room.id, date, slot);
        if (status === 'free') return;
        rows.push([
          date,
          slot,
          room.name,
          `${room.building}-${room.floor}`,
          room.capacity,
          room.hasWebex ? '是' : '否',
          room.hasProjector ? '是' : '否',
          booking.bookerName,
          booking.bookerEmail,
          booking.title,
          booking.status === BOOKING_STATUS.pending ? '待审批' : '已确认',
          booking.note || ''
        ]);
      });
    });
  });

  downloadCSV(`会议室月视图_${year}-${String(month).padStart(2, '0')}.csv`, rows);
  addLog('导出月视图', `${year}-${month}`, getCurrentUser()?.name || '未知');
}

function exportLogs() {
  const header = ['时间', '操作人', '操作', '详情'];
  const rows = [header, ...appState.logs.map(l => [l.timestamp, l.operator, l.action, l.detail])];
  downloadCSV(`操作日志_${todayStr()}.csv`, rows);
}

function parseImportCSV(text) {
  const lines = text.replace(/^\uFEFF/, '').split(/\r?\n/).filter(l => l.trim());
  if (lines.length < 2) return [];

  const parseRow = (line) => {
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (inQuotes) {
        if (ch === '"' && line[i + 1] === '"') {
          current += '"';
          i++;
        } else if (ch === '"') {
          inQuotes = false;
        } else {
          current += ch;
        }
      } else if (ch === '"') {
        inQuotes = true;
      } else if (ch === ',') {
        result.push(current.trim());
        current = '';
      } else {
        current += ch;
      }
    }
    result.push(current.trim());
    return result;
  };

  const header = parseRow(lines[0]).map(h => h.toLowerCase());
  const records = [];

  for (let i = 1; i < lines.length; i++) {
    const cols = parseRow(lines[i]);
    if (cols.every(c => !c)) continue;
    const record = {};
    header.forEach((h, idx) => {
      record[h] = cols[idx] || '';
    });
    records.push(normalizeImportRecord(record));
  }
  return records.filter(r => r.roomId && r.startDate);
}

function normalizeImportRecord(record) {
  const roomName = record['会议室'] || record['room'] || record['roomname'] || '';
  const building = record['楼栋'] || record['building'] || '';
  const room = appState.rooms.find(r =>
    r.name.toLowerCase() === roomName.toLowerCase() ||
    `${r.building}-${r.floor} ${r.name}`.toLowerCase() === `${building} ${roomName}`.toLowerCase().trim()
  );

  return {
    roomId: room?.id,
    roomName: room?.name || roomName,
    title: record['主题'] || record['title'] || record['会议主题'] || '导入会议',
    bookerName: record['预约人'] || record['booker'] || record['name'] || '导入',
    bookerEmail: record['邮箱'] || record['email'] || 'import@foxconn.com',
    startDate: normalizeDate(record['开始日期'] || record['startdate'] || record['date'] || record['日期']),
    endDate: normalizeDate(record['结束日期'] || record['enddate'] || record['开始日期'] || record['startdate'] || record['date'] || record['日期']),
    startSlot: normalizeSlot(record['开始时段'] || record['startslot'] || record['时段'] || '08:00-08:30'),
    endSlot: normalizeSlot(record['结束时段'] || record['endslot'] || record['时段'] || '08:00-08:30'),
    note: record['备注'] || record['note'] || ''
  };
}

function normalizeDate(val) {
  if (!val) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(val)) return val;
  const d = new Date(val);
  if (!isNaN(d)) return d.toISOString().slice(0, 10);
  return val;
}

function normalizeSlot(val) {
  if (!val) return TIME_POINTS[0];
  const strVal = String(val).trim();
  const foundPoint = TIME_POINTS.find(s => s === strVal || s.startsWith(strVal));
  if (foundPoint) return foundPoint;
  if (strVal.includes('-')) {
    const parts = strVal.split('-');
    if (parts.length === 2) {
      const startPart = parts[0].trim();
      const foundStart = TIME_POINTS.find(s => s === startPart || s.startsWith(startPart));
      if (foundStart) return foundStart;
    }
  }
  const foundSlot = TIME_SLOTS.find(s => s === strVal || s.startsWith(strVal));
  return foundSlot || TIME_POINTS[0];
}

function importBookingsFromRecords(records, user, forceOverwrite = false) {
  const results = { success: [], failed: [], conflicts: [] };

  records.forEach(record => {
    if (!record.roomId) {
      results.failed.push({ record, reason: `找不到会议室: ${record.roomName}` });
      return;
    }
    const importUser = { name: record.bookerName, email: record.bookerEmail, role: ROLES.user };
    const result = createBooking({
      roomId: record.roomId,
      title: record.title,
      startDate: record.startDate,
      endDate: record.endDate || record.startDate,
      startSlot: record.startSlot,
      endSlot: record.endSlot,
      note: record.note
    }, isEPM(user) ? importUser : user, { forceOverwrite });

    if (result.success) {
      results.success.push(result.booking);
    } else {
      results.conflicts.push({ record, conflicts: result.conflicts });
    }
  });

  if (results.success.length) {
    addLog('批量导入', `成功 ${results.success.length} 条`, user.name || user.email);
  }
  return results;
}

function getImportTemplateCSV() {
  const header = ['会议室', '楼栋', '主题', '预约人', '邮箱', '开始日期', '结束日期', '开始时段', '结束时段', '备注'];
  const sample = ['Mickey', 'C01-4F', '项目例会', '张三', 'zhang@foxconn.com', '2026-06-23', '2026-06-23', '09:00-09:30', '11:30-12:00', ''];
  downloadCSV('会议室导入模板.csv', [header, sample]);
}
