/**
 * Main application UI
 */
(function () {
  let selectedRole = ROLES.user;
  let pendingImportRecords = null;

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  function showModal(title, bodyHtml, buttons = []) {
    $('#modalTitle').textContent = title;
    $('#modalBody').innerHTML = bodyHtml;
    const footer = $('#modalFooter');
    footer.innerHTML = '';
    buttons.forEach(btn => {
      const el = document.createElement('button');
      el.className = `btn ${btn.class || 'btn-secondary'}`;
      el.textContent = btn.text;
      el.onclick = () => {
        if (btn.onClick) btn.onClick();
        if (btn.close !== false) hideModal();
      };
      footer.appendChild(el);
    });
    $('#modalOverlay').classList.add('show');
  }

  function hideModal() {
    $('#modalOverlay').classList.remove('show');
  }

  function showToast(title, message, type = 'success') {
    showModal(title, `<div class="alert alert-${type}">${message}</div>`, [
      { text: '确定', class: 'btn-primary' }
    ]);
  }

  function navigate(page) {
    $$('.page').forEach(p => p.classList.remove('active'));
    $$('.nav-tab').forEach(t => t.classList.remove('active'));
    $(`#page-${page}`)?.classList.add('active');
    $(`.nav-tab[data-page="${page}"]`)?.classList.add('active');

    if (page === 'home') renderRoomList();
    if (page === 'schedule') renderSchedule();
    if (page === 'book') initBookForm();
    if (page === 'my') renderMyBookings();
    if (page === 'admin') renderAdmin();
  }

  function initLogin() {
    $('#loginBtn').addEventListener('click', async () => {
      const email = $('#loginEmail').value.trim().toLowerCase();
      const password = $('#loginPassword').value.trim();
      if (!email || !password) {
        showToast('Please fill in', 'Please enter email and password', 'warning');
        return;
      }
      
      try {
        const result = await apiRequest('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        
        if (result.success) {
          const user = result.user;
          setCurrentUser(user);
          
          if (password === '123456') {
            showModal('Change Password', `
              <p>Please change your initial password (123456) for security.</p>
              <div class="form-group" style="text-align:left">
                <label>New Password</label>
                <input type="password" id="newPassword" placeholder="Enter new password">
              </div>
            `, [{
              text: 'Save',
              class: 'btn-primary',
              onClick: async () => {
                const newPwd = $('#newPassword').value.trim();
                if (!newPwd || newPwd === '123456') {
                  showToast('Invalid Password', 'Please set a different password', 'warning');
                  return;
                }
                try {
                  const updateResult = await apiRequest(`/users/${user.id}/password`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password: newPwd })
                  });
                  if (updateResult.success) {
                    showToast('Success', 'Password updated successfully', 'success');
                    await enterApp();
                  } else {
                    showToast('Error', updateResult.message || 'Failed to update password', 'danger');
                  }
                } catch (err) {
                  console.error('Password update error:', err);
                  showToast('Error', 'Unable to update password', 'danger');
                }
              }
            }]);
          } else {
            await enterApp();
          }
        } else {
          showToast('Login Failed', result.message || 'Unknown error', 'danger');
        }
      } catch (err) {
        console.error('Login error:', err);
        showToast('Login Failed', 'Unable to connect to server', 'danger');
      }
    });
    
    $('#showRegisterLink').addEventListener('click', (e) => {
      e.preventDefault();
      $('#loginForm').classList.add('hidden');
      $('#registerForm').classList.remove('hidden');
    });
    
    $('#showLoginLink').addEventListener('click', (e) => {
      e.preventDefault();
      $('#registerForm').classList.add('hidden');
      $('#loginForm').classList.remove('hidden');
    });
    
    $('#registerBtn').addEventListener('click', async () => {
      const name = $('#registerName').value.trim();
      const email = $('#registerEmail').value.trim().toLowerCase();
      
      if (!email) {
        showToast('Please fill in', 'Email is required', 'warning');
        return;
      }
      
      try {
        const result = await apiRequest('/users', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email })
        });
        
        if (result.success) {
          showToast('Success', 'Account created! Initial password is 123456.', 'success');
          $('#registerForm').classList.add('hidden');
          $('#loginForm').classList.remove('hidden');
          $('#loginEmail').value = email;
          $('#loginPassword').value = '';
        } else {
          showToast('Registration Failed', result.message || 'Unknown error', 'danger');
        }
      } catch (err) {
        console.error('Registration error:', err);
        showToast('Registration Failed', 'Unable to connect to server', 'danger');
      }
    });

    $('#showForgotLink').addEventListener('click', (e) => {
      e.preventDefault();
      $('#loginForm').classList.add('hidden');
      $('#forgotForm').classList.remove('hidden');
    });

    $('#showLoginFromForgot').addEventListener('click', (e) => {
      e.preventDefault();
      $('#forgotForm').classList.add('hidden');
      $('#loginForm').classList.remove('hidden');
    });

    $('#showLoginFromReset').addEventListener('click', (e) => {
      e.preventDefault();
      $('#resetForm').classList.add('hidden');
      $('#loginForm').classList.remove('hidden');
    });

    $('#forgotSendBtn').addEventListener('click', async () => {
      const email = $('#forgotEmail').value.trim().toLowerCase();
      if (!email) {
        showToast('Please fill in', 'Please enter your email', 'warning');
        return;
      }
      try {
        const result = await apiRequest('/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email })
        });
        if (result.success) {
          showToast('Success', 'Verification code sent to your email', 'success');
          $('#forgotForm').classList.add('hidden');
          $('#resetForm').classList.remove('hidden');
          $('#resetEmail').value = email;
        } else {
          showToast('Error', result.message || 'Failed to send verification code', 'danger');
        }
      } catch (err) {
        console.error('Forgot password error:', err);
        showToast('Error', 'Unable to connect to server', 'danger');
      }
    });

    $('#resetSubmitBtn').addEventListener('click', async () => {
      const email = $('#resetEmail').value.trim().toLowerCase();
      const code = $('#resetCode').value.trim();
      const newPassword = $('#resetPassword').value.trim();
      if (!email || !code || !newPassword) {
        showToast('Please fill in', 'Please enter all fields', 'warning');
        return;
      }
      if (newPassword === '123456') {
        showToast('Invalid Password', 'Please set a different password', 'warning');
        return;
      }
      try {
        const result = await apiRequest('/reset-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, code, password: newPassword })
        });
        if (result.success) {
          showToast('Success', 'Password reset successfully', 'success');
          $('#resetForm').classList.add('hidden');
          $('#loginForm').classList.remove('hidden');
          $('#loginEmail').value = email;
          $('#loginPassword').value = '';
        } else {
          showToast('Error', result.message || 'Failed to reset password', 'danger');
        }
      } catch (err) {
        console.error('Reset password error:', err);
        showToast('Error', 'Unable to connect to server', 'danger');
      }
    });

    $('#showQRCodeLink').addEventListener('click', (e) => {
      e.preventDefault();
      showQRCode();
    });

    $('#qrModalClose').addEventListener('click', () => {
      $('#qrModal').classList.add('hidden');
    });

    $('#qrModal').addEventListener('click', (e) => {
      if (e.target.id === 'qrModal') {
        $('#qrModal').classList.add('hidden');
      }
    });
  }

  function showQRCode() {
    const url = window.location.origin + window.location.pathname;
    const qrContainer = $('#qrcode');
    qrContainer.innerHTML = '';
    
    try {
      new QRCode(qrContainer, {
        text: url,
        width: 200,
        height: 200,
        colorDark: '#000000',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.H
      });
      $('#qrUrl').textContent = url;
      $('#qrModal').classList.remove('hidden');
    } catch (err) {
      console.error('QR code generation error:', err);
      showToast('Error', 'Failed to generate QR code', 'danger');
    }
  }

  async function enterApp() {
    const user = getCurrentUser();
    $('#loginPage').classList.add('hidden');
    $('#mainNav').style.display = '';
    $('#mainContent').classList.remove('hidden');
    $('#userDisplay').textContent = user.name;
    if (isEPM(user)) {
      $('#adminTab').classList.remove('hidden');
    }
    
    try {
      const bookingsResult = await apiRequest('/bookings');
      if (bookingsResult && Array.isArray(bookingsResult)) {
        appState.bookings = bookingsResult.map(b => ({
          id: b.id,
          roomId: b.room_id,
          userId: b.user_id,
          title: b.title,
          bookerName: b.booker_name,
          bookerEmail: b.booker_email || '',
          startDate: b.start_date,
          endDate: b.end_date,
          startSlot: b.start_slot,
          endSlot: b.end_slot,
          contactPhone: b.contact_phone || '',
          note: b.note || '',
          status: b.status,
          createdAt: b.created_at,
          approvedAt: b.approved_at,
          cancelledAt: b.cancelled_at
        }));
        saveState(appState);
        console.log('Loaded', appState.bookings.length, 'bookings from server');
      }
    } catch (err) {
      console.error('Failed to load bookings from server:', err);
    }
    
    updateNotifBadge();
    navigate('home');
  }

  function updateNotifBadge() {
    const user = getCurrentUser();
    const count = getUnreadNotifications(user.email).length;
    const badge = $('#notifBadge');
    if (count > 0) {
      badge.textContent = count;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }
  }

  function renderRoomList() {
    const building = $('#homeBuildingFilter').value;
    const webexOnly = $('#filterWebex').checked;

    let rooms = [...appState.rooms];
    if (building !== 'all') rooms = rooms.filter(r => r.building === building);
    if (webexOnly) rooms = rooms.filter(r => r.hasWebex);

    const container = $('#roomList');
    container.innerHTML = rooms.map(room => `
      <div class="room-card type-${room.roomType === 'normal' ? 'normal' : room.roomType}">
        <div class="room-name ${room.hasWebex ? 'has-webex' : ''}">${room.name}</div>
        <div class="room-meta">
          <span>${room.building}-${room.floor}</span>
          <span>${room.capacity} people</span>
          ${room.hasWebex ? '<span class="tag webex">Webex</span>' : ''}
        </div>
      </div>
    `).join('');
  }

  function renderSchedule() {
    const mode = $('#viewMode').value;
    const date = $('#scheduleDate').value || todayStr();
    const building = $('#scheduleBuilding').value;
    const room = $('#scheduleRoom').value;
    const container = $('#scheduleContent');

    if (mode === 'month') {
      renderMonthView(container, date, building, room);
    } else if (mode === 'week') {
      renderWeekView(container, date, building, room);
    } else {
      renderDayView(container, date, building, room);
    }
  }

  function filteredRooms(building, roomId) {
    let rooms = building === 'all' ? appState.rooms : appState.rooms.filter(r => r.building === building);
    if (roomId && roomId !== 'all') {
      rooms = rooms.filter(r => r.id === roomId);
    }
    return rooms;
  }

  function updateScheduleRoomOptions() {
    const building = $('#scheduleBuilding').value;
    const $roomSelect = $('#scheduleRoom');
    if (!$roomSelect) return;
    
    const rooms = filteredRooms(building);
    let html = '<option value="all">All</option>';
    rooms.forEach(r => {
      const suffix = r.hasWebex ? ' ★Webex' : '';
      html += `<option value="${r.id}">${r.name} (${r.capacity} people)${suffix}</option>`;
    });
    $roomSelect.innerHTML = html;
  }

  function renderDayView(container, date, building, room) {
    const rooms = filteredRooms(building, room);
    let html = `<div class="schedule-wrap"><table class="schedule-table"><thead><tr>
      <th class="time-col">Time Slot</th>`;
    rooms.forEach(room => {
      html += `<th class="room-col" style="${room.hasWebex ? 'color:var(--webex);font-weight:600' : 'color:#333'}">${room.name}</th>`;
    });
    html += '</tr></thead><tbody>';

    TIME_SLOTS.forEach(slot => {
      html += `<tr><td class="time-col">${slot.split('-')[0]}</td>`;
      rooms.forEach(room => {
        const { status, booking } = getSlotStatus(room.id, date, slot);
        const cls = status === 'free' ? 'free' : status;
        const title = booking ? `${booking.bookerName}: ${booking.title}` : '';
        html += `<td class="slot-cell ${cls}" data-room="${room.id}" data-date="${date}" data-slot="${slot}" title="${title}">`;
        if (booking) html += `<span class="cell-title">${booking.bookerName?.split(' ')[0] || 'Booked'}</span>`;
        html += '</td>';
      });
      html += '</tr>';
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
    bindSlotClicks(container);
  }

  function renderWeekView(container, baseDate, building, room) {
    const dates = getWeekDates(baseDate);
    const rooms = filteredRooms(building, room);
    let html = `<div class="schedule-wrap"><table class="schedule-table"><thead><tr>
      <th class="time-col">Time Slot</th>`;
    dates.forEach(d => {
      const label = new Date(d).toLocaleDateString('en-US', { weekday: 'short', month: 'numeric', day: 'numeric' });
      html += `<th colspan="${rooms.length}">${label}</th>`;
    });
    html += '</tr><tr><th class="time-col"></th>';
    dates.forEach(date => {
      rooms.forEach(room => {
        html += `<th class="room-col" style="${room.hasWebex ? 'color:var(--webex);font-weight:600;font-size:10px' : 'color:#333;font-size:10px'}">${room.name}</th>`;
      });
    });
    html += '</tr></thead><tbody>';

    TIME_SLOTS.forEach(slot => {
      html += `<tr><td class="time-col">${slot.split('-')[0]}</td>`;
      dates.forEach(date => {
        rooms.forEach(room => {
          const { status, booking } = getSlotStatus(room.id, date, slot);
          const cls = status === 'free' ? 'free' : status;
          html += `<td class="slot-cell ${cls}" data-room="${room.id}" data-date="${date}" data-slot="${slot}">`;
          if (booking) html += `<span class="cell-title">●</span>`;
          html += '</td>';
        });
      });
      html += '</tr>';
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
    bindSlotClicks(container);
  }

  function renderMonthView(container, baseDate, building, room) {
    const d = new Date(baseDate);
    const year = d.getFullYear();
    const month = d.getMonth() + 1;
    const dates = getMonthDates(year, month);
    const firstDay = new Date(year, month - 1, 1).getDay();
    const offset = firstDay === 0 ? 6 : firstDay - 1;

    let html = `<h3 style="margin:0 0 16px">${year} - ${month}</h3>`;
    html += '<div class="month-grid">';
    ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].forEach(w => {
      html += `<div class="month-day-header">${w}</div>`;
    });

    for (let i = 0; i < offset; i++) html += '<div class="month-day other"></div>';

    dates.forEach(date => {
      const dayBookings = getBookingsForDate(date, building === 'all' ? null : building, room === 'all' ? null : room);
      const isToday = date === todayStr();
      html += `<div class="month-day ${isToday ? 'today' : ''}" data-date="${date}">
        <div class="month-day-num">${parseInt(date.slice(8), 10)}</div>
        <div class="month-day-events">${dayBookings.length} bookings</div>
      </div>`;
    });
    html += '</div>';
    container.innerHTML = html;

    container.querySelectorAll('.month-day[data-date]').forEach(el => {
      el.addEventListener('click', () => {
        $('#viewMode').value = 'day';
        $('#scheduleDate').value = el.dataset.date;
        renderSchedule();
      });
    });
  }

  function bindSlotClicks(container) {
    container.querySelectorAll('.slot-cell').forEach(cell => {
      cell.addEventListener('click', () => {
        const { room, date, slot } = cell.dataset;
        const { status, booking } = getSlotStatus(room, date, slot);
        const roomObj = getRoomById(room);
        if (status === 'free') {
          navigate('book');
          $('#bookBuilding').value = roomObj.building;
          updateBookRoomOptions();
          $('#bookRoom').value = room;
          $('#bookStartDate').value = date;
          $('#bookEndDate').value = date;
          $('#bookStartSlot').value = slot;
          $('#bookEndSlot').value = slot;
          updateBookPreview();
        } else if (booking) {
          showModal('预约详情', `
            <p><strong>${booking.title}</strong></p>
            <p>会议室：${formatRoomLabel(roomObj)}</p>
            <p>预约人：${booking.bookerName} (${booking.bookerEmail})</p>
            <p>日期：${booking.startDate} ~ ${booking.endDate}</p>
            <p>时段：${booking.startSlot} - ${booking.endSlot}</p>
            <p>状态：<span class="status-pill ${booking.status}">${statusLabel(booking.status)}</span></p>
            ${booking.note ? `<p>备注：${booking.note}</p>` : ''}
          `, [{ text: '关闭', class: 'btn-primary' }]);
        }
      });
    });
  }

  function statusLabel(status) {
    const map = { approved: 'Confirmed', pending: 'Pending', rejected: 'Rejected', cancelled: 'Cancelled' };
    return map[status] || status;
  }

  function initBookForm() {
    populateSlotSelects();
    updateBookRoomOptions();
    $('#bookStartDate').value = todayStr();
    $('#bookEndDate').value = todayStr();
    updateBookAlerts();
    updateBookPreview();
  }

  function populateSlotSelects() {
    ['#bookStartSlot', '#bookEndSlot'].forEach(sel => {
      const el = $(sel);
      el.innerHTML = TIME_SLOTS.map(s => `<option value="${s}">${s}</option>`).join('');
    });
    $('#bookEndSlot').value = TIME_SLOTS[3];
  }

  function updateBookRoomOptions() {
    const building = $('#bookBuilding').value;
    const user = getCurrentUser();
    const rooms = appState.rooms.filter(r => r.building === building);
    const select = $('#bookRoom');
    select.innerHTML = rooms.map(r => {
      const check = canBookRoom(user, r);
      const disabled = check.allowed ? '' : 'disabled';
      const suffix = r.hasWebex ? ' ★Webex' : '';
      return `<option value="${r.id}" ${disabled}>${r.name} (${r.capacity} people)${suffix}${!check.allowed ? ' - EPM Only' : ''}</option>`;
    }).join('');
  }

  function updateBookAlerts() {
    const user = getCurrentUser();
    const container = $('#bookAlerts');
    let html = '';
    if (isBadCredit(user.email)) {
      html += '<div class="alert alert-warning">You have cancelled more than 3 times this month. Marked as "Bad Credit", bookings require Meeting EPM approval.</div>';
    }
    container.innerHTML = html;
  }

  function updateBookPreview() {
    const start = $('#bookStartDate').value;
    const end = $('#bookEndDate').value;
    const roomId = $('#bookRoom').value;
    if (!start || !end) return;
    const days = countDays(start, end);
    const room = roomId ? getRoomById(roomId) : null;
    const approval = needsApproval(getCurrentUser(), start, end, room);
    const warnings = getBookingWarnings(start, end);
    const preview = $('#bookPreview');
    preview.classList.remove('hidden');
    let text = `预约 ${days} 天`;
    if (approval.required) text += ` · 需 EPM 审批（${approval.reason}）`;
    else text += ' · 可即时确认';
    if (warnings.length) text += '<br>' + warnings.join('<br>');
    preview.innerHTML = text;
  }

  async function handleBookSubmit(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const user = getCurrentUser();
    if (!user) {
      showToast('Error', 'Please login first', 'danger');
      return;
    }
    
    const payload = {
      roomId: $('#bookRoom').value,
      title: $('#bookTitle').value.trim(),
      contactName: $('#bookContactName').value.trim(),
      contactPhone: $('#bookContactPhone').value.trim(),
      startDate: $('#bookStartDate').value,
      endDate: $('#bookEndDate').value,
      startSlot: $('#bookStartSlot').value,
      endSlot: $('#bookEndSlot').value,
      note: $('#bookNote').value.trim()
    };

    if (payload.endDate < payload.startDate) {
      showToast('Date Error', 'End date cannot be earlier than start date', 'danger');
      return;
    }
    if (slotIndex(payload.endSlot) < slotIndex(payload.startSlot)) {
      showToast('Time Error', 'End time cannot be earlier than start time', 'danger');
      return;
    }

    try {
      const result = createBooking(payload, user);
      
      if (!result.success) {
        const conflictText = result.conflicts.map(c =>
          `在 <strong>${c.date}</strong> 已被 <strong>${c.booker}</strong> 预约`
        ).join('<br>');
        showModal('预约失败', `
          <p>以下会议室存在时间冲突：</p>
          <div class="alert alert-danger">${conflictText}</div>
          <p>请重新选择时间或会议室。</p>
        `, [{ text: '确定', class: 'btn-primary' }]);
        return;
      }

      const { booking, warnings, needsApproval: pending } = result;
      let msg = pending
        ? '<div class="alert alert-info">预约成功，等待Meeting Room Admin确认。</div>'
        : '<div class="alert alert-success">预约成功！您的会议室已被预定。</div>';
      if (warnings.length) msg += '<br><br>' + warnings.map(w => `<div class="alert alert-warning">${w}</div>`).join('');

      showModal(pending ? '等待确认' : '预约成功', msg, [
        { text: '查看我的预约', class: 'btn-primary', onClick: () => navigate('my') },
        { text: '继续预约', class: 'btn-secondary' }
      ]);

      if (!pending) {
        showToast('Success', 'Booking successful! Your meeting room has been reserved.', 'success');
      } else {
        showToast('Pending', 'Booking submitted! Waiting for Meeting Room Admin confirmation.', 'info');
      }

      $('#bookForm').reset();
      initBookForm();
      updateNotifBadge();
    } catch (err) {
      console.error('Booking error:', err);
      showToast('Booking Failed', err.message || 'An error occurred', 'danger');
    }
  }

  function renderMyBookings() {
    const user = getCurrentUser();
    const mine = appState.bookings.filter(b =>
      b.bookerEmail?.toLowerCase() === user.email?.toLowerCase()
    ).sort((a, b) => b.createdAt.localeCompare(a.createdAt));

    const cancelCount = getCancelCountThisMonth(user.email);
    $('#myCreditInfo').innerHTML = `
      <div class="alert ${isBadCredit(user.email) ? 'alert-danger' : 'alert-info'}">
        ${cancelCount} cancellations this month ${isBadCredit(user.email) ? '· <strong>Bad Credit</strong>' : ''}
      </div>`;

    const container = $('#myBookingsList');
    if (!mine.length) {
      container.innerHTML = '<div class="empty-state">No booking records</div>';
    } else {
      container.innerHTML = mine.map(b => {
        const room = getRoomById(b.roomId);
        const canCancel = b.status === BOOKING_STATUS.approved || b.status === BOOKING_STATUS.pending;
        return `<div class="list-item">
          <div class="list-item-main">
            <div class="list-item-title">${b.title}</div>
            <div class="list-item-meta">
              ${formatRoomLabel(room)} · ${b.startDate}${b.endDate !== b.startDate ? '~' + b.endDate : ''}
              · ${b.startSlot}-${b.endSlot}
              · <span class="status-pill ${b.status}">${statusLabel(b.status)}</span>
            </div>
          </div>
          ${canCancel ? `<button class="btn btn-secondary btn-sm" data-cancel="${b.id}">Cancel</button>` : ''}
        </div>`;
      }).join('');

      container.querySelectorAll('[data-cancel]').forEach(btn => {
        btn.addEventListener('click', () => {
          const id = btn.dataset.cancel;
          showModal('Confirm Cancellation', '<p>Are you sure you want to cancel this booking? Frequent cancellations will affect your credit record.</p>', [
            { text: 'Keep', class: 'btn-secondary' },
            { text: 'Confirm Cancel', class: 'btn-danger', onClick: () => {
              const res = cancelBooking(id, user);
              if (res.badCredit) {
                showToast('Cancelled', 'More than 3 cancellations this month, marked as Bad Credit', 'warning');
              }
              renderMyBookings();
            }}
          ]);
        });
      });
    }

    if (isEPM(user)) {
      renderPendingApprovals();
    } else {
      $('#pendingApprovalsCard').classList.add('hidden');
    }
  }

  function renderPendingApprovals() {
    const pending = appState.bookings.filter(b => b.status === BOOKING_STATUS.pending);
    $('#pendingApprovalsCard').classList.remove('hidden');
    $('#pendingCount').textContent = pending.length;

    const container = $('#pendingList');
    if (!pending.length) {
      container.innerHTML = '<div class="empty-state">No pending approvals</div>';
      return;
    }

    container.innerHTML = pending.map(b => {
      const room = getRoomById(b.roomId);
      return `<div class="list-item">
        <div class="list-item-main">
          <div class="list-item-title">${b.title}</div>
          <div class="list-item-meta">
            ${b.bookerName} (${b.bookerEmail}) · ${formatRoomLabel(room)}
            · ${b.startDate}~${b.endDate} · ${b.startSlot}-${b.endSlot}
          </div>
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-success btn-sm" data-approve="${b.id}">Approve</button>
          <button class="btn btn-danger btn-sm" data-reject="${b.id}">Reject</button>
        </div>
      </div>`;
    }).join('');

    container.querySelectorAll('[data-approve]').forEach(btn => {
      btn.addEventListener('click', () => {
        const res = approveBooking(btn.dataset.approve, getCurrentUser());
        if (!res.success) {
          showToast('Conflict', 'This time slot conflicts with another booking', 'danger');
        } else {
          showToast('Approved', 'Confirmation email sent to booker (simulated)', 'success');
        }
        renderMyBookings();
        updateNotifBadge();
      });
    });

    container.querySelectorAll('[data-reject]').forEach(btn => {
      btn.addEventListener('click', () => {
        rejectBooking(btn.dataset.reject, getCurrentUser(), 'Rejected by EPM');
        showToast('Rejected', 'Notified the booker', 'info');
        renderMyBookings();
      });
    });
  }

  function renderAdmin() {
    renderBuildList();
    renderRoomEditList();
    renderLogTable();
    renderMailLog();
  }

  function renderBuildList() {
    const container = $('#buildList');
    const current = getCurrentBuild();
    if (!appState.builds.length) {
      container.innerHTML = '<p class="empty-state">No Builds. Please add the current project phase.</p>';
      return;
    }
    container.innerHTML = appState.builds.map(b => `
      <div class="list-item">
        <div class="list-item-main">
          <div class="list-item-title">${b.name} ${b.id === appState.currentBuildId ? '<span class="tag webex">Current</span>' : ''}</div>
          <div class="list-item-meta">${b.startDate} ~ ${b.endDate}</div>
        </div>
        <button class="btn btn-secondary btn-sm" data-set-build="${b.id}">Set as Current</button>
      </div>
    `).join('');

    container.querySelectorAll('[data-set-build]').forEach(btn => {
      btn.addEventListener('click', () => {
        appState.currentBuildId = btn.dataset.setBuild;
        saveState(appState);
        addLog('Switch Build', getBuildById(btn.dataset.setBuild)?.name, getCurrentUser().name);
        renderBuildList();
      });
    });
  }

  function renderRoomEditList() {
    const container = $('#roomEditList');
    container.innerHTML = appState.rooms.map(room => `
      <div class="list-item" style="flex-wrap:wrap">
        <div class="list-item-main">
          <div class="list-item-title ${room.hasWebex ? 'has-webex' : ''}">${formatRoomLabel(room)} · ${room.capacity} people</div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
          <label><input type="checkbox" data-room="${room.id}" data-field="hasWebex" ${room.hasWebex ? 'checked' : ''}> Webex</label>
          <select data-room="${room.id}" data-field="roomType">
            <option value="normal" ${room.roomType === 'normal' ? 'selected' : ''}>Normal</option>
            <option value="epm" ${room.roomType === 'epm' ? 'selected' : ''}>EPM Only</option>
            <option value="warroom" ${room.roomType === 'warroom' ? 'selected' : ''}>War Room</option>
          </select>
        </div>
      </div>
    `).join('');

    container.querySelectorAll('input, select').forEach(el => {
      el.addEventListener('change', () => {
        const room = getRoomById(el.dataset.room);
        if (!room) return;
        if (el.type === 'checkbox') {
          room[el.dataset.field] = el.checked;
        } else {
          room[el.dataset.field] = el.value;
        }
        saveState(appState);
        addLog('Edit Room', `${formatRoomLabel(room)} ${el.dataset.field}=${el.type === 'checkbox' ? el.checked : el.value}`, getCurrentUser().name);
      });
    });
  }

  function renderLogTable() {
    const tbody = $('#logTableBody');
    tbody.innerHTML = appState.logs.slice(0, 50).map(l => `
      <tr>
        <td>${new Date(l.timestamp).toLocaleString('en-US')}</td>
        <td>${l.operator}</td>
        <td>${l.action}</td>
        <td>${l.detail}</td>
      </tr>
    `).join('');
  }

  function renderMailLog() {
    const logs = getRecentMailLog(15);
    const container = $('#mailLogList');
    if (!logs.length) {
      container.innerHTML = '<div class="empty-state">No email records</div>';
      return;
    }
    container.innerHTML = logs.map(m => `
      <div class="list-item">
        <div class="list-item-main">
          <div class="list-item-title">${m.subject}</div>
          <div class="list-item-meta">→ ${m.to} · ${new Date(m.sentAt).toLocaleString('en-US')}</div>
        </div>
      </div>
    `).join('');
  }

  function handleImportFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const records = parseImportCSV(e.target.result);
      if (!records.length) {
        showToast('Import Failed', 'No valid data recognized. Please check CSV format.', 'danger');
        return;
      }

      const user = getCurrentUser();
      const allConflicts = [];
      records.forEach(record => {
        if (!record.roomId) return;
        const conflicts = findConflicts(record.roomId, record.startDate, record.endDate || record.startDate, record.startSlot, record.endSlot);
        if (conflicts.length) {
          allConflicts.push({ record, conflicts: summarizeConflicts(conflicts) });
        }
      });

      if (allConflicts.length) {
        pendingImportRecords = records;
        const conflictHtml = allConflicts.map(item => {
          const c = item.conflicts[0];
          return `Room <strong>${item.record.roomName}</strong> on ${c.date} is booked by <strong>${c.booker}</strong>`;
        }).join('<br>');

        showModal('Import Conflict', `
          <p>The following rooms are already booked on specified dates:</p>
          <div class="alert alert-warning">${conflictHtml}</div>
          <p>Overwrite existing bookings?</p>
        `, [
          { text: 'Cancel Import', class: 'btn-secondary', onClick: () => { pendingImportRecords = null; } },
          { text: 'Overwrite & Import', class: 'btn-danger', onClick: () => {
            const res = importBookingsFromRecords(pendingImportRecords, user, true);
            pendingImportRecords = null;
            showToast('Import Complete', `${res.success.length} success, ${res.failed.length} failed`, 'success');
            renderAdmin();
          }}
        ]);
      } else {
        const res = importBookingsFromRecords(records, user, false);
        showToast('Import Complete', `Successfully imported ${res.success.length} bookings`, 'success');
        renderAdmin();
      }
    };
    reader.readAsText(file, 'UTF-8');
  }

  function bindEvents() {
    $$('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => navigate(tab.dataset.page));
    });

    const $logoutBtn = $('#logoutBtn');
    if ($logoutBtn) $logoutBtn.addEventListener('click', () => {
      clearCurrentUser();
      location.reload();
    });

    const $homeBuildingFilter = $('#homeBuildingFilter');
    if ($homeBuildingFilter) $homeBuildingFilter.addEventListener('change', renderRoomList);
    const $filterWebex = $('#filterWebex');
    if ($filterWebex) $filterWebex.addEventListener('change', renderRoomList);

    const $viewMode = $('#viewMode');
    if ($viewMode) $viewMode.addEventListener('change', renderSchedule);
    const $scheduleDate = $('#scheduleDate');
    if ($scheduleDate) {
      $scheduleDate.addEventListener('change', renderSchedule);
      $scheduleDate.value = todayStr();
    }
    const $scheduleBuilding = $('#scheduleBuilding');
    if ($scheduleBuilding) $scheduleBuilding.addEventListener('change', () => {
      updateScheduleRoomOptions();
      renderSchedule();
    });

    const $scheduleRoom = $('#scheduleRoom');
    if ($scheduleRoom) $scheduleRoom.addEventListener('change', renderSchedule);

    updateScheduleRoomOptions();

    const $exportWeekBtn = $('#exportWeekBtn');
    if ($exportWeekBtn) $exportWeekBtn.addEventListener('click', () => {
      exportWeeklySchedule($('#scheduleDate').value, $('#scheduleBuilding').value);
      showToast('导出成功', '周排期 CSV 已下载', 'success');
    });

    const $exportMonthBtn = $('#exportMonthBtn');
    if ($exportMonthBtn) $exportMonthBtn.addEventListener('click', () => {
      const d = new Date($('#scheduleDate').value || todayStr());
      exportMonthlySchedule(d.getFullYear(), d.getMonth() + 1, $('#scheduleBuilding').value);
      showToast('导出成功', '月视图 CSV 已下载', 'success');
    });

    const $bookBuilding = $('#bookBuilding');
    if ($bookBuilding) $bookBuilding.addEventListener('change', updateBookRoomOptions);
    ['#bookStartDate', '#bookEndDate', '#bookStartSlot', '#bookEndSlot'].forEach(sel => {
      const el = $(sel);
      if (el) el.addEventListener('change', updateBookPreview);
    });
    const $bookForm = $('#bookForm');
    if ($bookForm) $bookForm.addEventListener('submit', handleBookSubmit);

    const $addBuildBtn = $('#addBuildBtn');
    if ($addBuildBtn) $addBuildBtn.addEventListener('click', () => {
      const name = $('#buildName').value.trim();
      const startDate = $('#buildStart').value;
      const endDate = $('#buildEnd').value;
      if (!name || !startDate || !endDate) {
        showToast('Please Fill', 'Build name and dates cannot be empty', 'warning');
        return;
      }
      const build = { id: generateId('build'), name, startDate, endDate };
      appState.builds.push(build);
      appState.currentBuildId = build.id;
      saveState(appState);
      addLog('Add Build', name, getCurrentUser().name);
      renderBuildList();
      showToast('Added', `${name} has been set as current Build`, 'success');
    });

    const $exportBuildBtn = $('#exportBuildBtn');
    if ($exportBuildBtn) $exportBuildBtn.addEventListener('click', () => {
      if (!appState.currentBuildId) {
        showToast('No Build', 'Please add and select a current Build first', 'warning');
        return;
      }
      exportBuildSchedule(appState.currentBuildId);
      showToast('Export Successful', 'Build schedule CSV downloaded', 'success');
    });

    const $downloadTemplateBtn = $('#downloadTemplateBtn');
    if ($downloadTemplateBtn) $downloadTemplateBtn.addEventListener('click', getImportTemplateCSV);
    const $importFile = $('#importFile');
    if ($importFile) $importFile.addEventListener('change', (e) => {
      if (e.target.files[0]) handleImportFile(e.target.files[0]);
      e.target.value = '';
    });

    const $importDefaultBtn = $('#importDefaultBtn');
    if ($importDefaultBtn) $importDefaultBtn.addEventListener('click', async () => {
      showModal('Confirm Import', '<p>Are you sure you want to import all default bookings? This will create 44 bookings.</p>', [
        { text: 'Cancel', class: 'btn-secondary' },
        { text: 'Confirm', class: 'btn-primary', onClick: async () => {
          try {
            const result = await apiRequest('/bookings/import', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({})
            });
            if (result.success) {
              showToast('Success', result.message, 'success');
              renderAdmin();
            } else {
              showToast('Error', result.message || 'Import failed', 'danger');
            }
          } catch (err) {
            console.error('Import error:', err);
            showToast('Error', 'Unable to connect to server', 'danger');
          }
        }}
      ]);
    });

    const $exportLogsBtn = $('#exportLogsBtn');
    if ($exportLogsBtn) $exportLogsBtn.addEventListener('click', exportLogs);
    const $resetDataBtn = $('#resetDataBtn');
    if ($resetDataBtn) $resetDataBtn.addEventListener('click', () => {
      showModal('Reset Data', '<p>Are you sure you want to reset all demo data? This action cannot be undone.</p>', [
        { text: 'Cancel', class: 'btn-secondary' },
        { text: 'Confirm Reset', class: 'btn-danger', onClick: () => {
          resetDemoData();
          location.reload();
        }}
      ]);
    });

    const $modalClose = $('#modalClose');
    if ($modalClose) $modalClose.addEventListener('click', hideModal);
    const $modalOverlay = $('#modalOverlay');
    if ($modalOverlay) $modalOverlay.addEventListener('click', (e) => {
      if (e.target === $modalOverlay) hideModal();
    });
  }

  async function init() {
    initLogin();
    bindEvents();
    if (getCurrentUser()) {
      await enterApp();
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
