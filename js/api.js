const API_BASE = '/api';

async function apiRequest(url, options = {}) {
  try {
    console.log('API Request:', `${API_BASE}${url}`, options);
    const response = await fetch(`${API_BASE}${url}`, {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    console.log('API Response status:', response.status);
    const data = await response.json();
    console.log('API Response data:', data);
    return data;
  } catch (error) {
    console.error('API request failed:', error);
    return { success: false, message: 'Network error: ' + error.message };
  }
}

async function apiLogin(email, password) {
  return apiRequest('/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}

async function apiGetUsers() {
  return apiRequest('/users');
}

async function apiGetUser(userId) {
  return apiRequest(`/users/${userId}`);
}

async function apiCreateUser(email, name, password = '123456', role = 'user') {
  return apiRequest('/users', {
    method: 'POST',
    body: JSON.stringify({ email, name, password, role })
  });
}

async function apiUpdatePassword(userId, password) {
  return apiRequest(`/users/${userId}/password`, {
    method: 'PUT',
    body: JSON.stringify({ password })
  });
}

async function apiGetRooms(building = null) {
  const url = building ? `/rooms?building=${building}` : '/rooms';
  return apiRequest(url);
}

async function apiGetRoom(roomId) {
  return apiRequest(`/rooms/${roomId}`);
}

async function apiUpdateRoom(roomId, data) {
  return apiRequest(`/rooms/${roomId}`, {
    method: 'PUT',
    body: JSON.stringify(data)
  });
}

async function apiGetBookings(params = {}) {
  const query = new URLSearchParams(params).toString();
  const url = query ? `/bookings?${query}` : '/bookings';
  return apiRequest(url);
}

async function apiGetBooking(bookingId) {
  return apiRequest(`/bookings/${bookingId}`);
}

async function apiCreateBooking(data) {
  return apiRequest('/bookings', {
    method: 'POST',
    body: JSON.stringify(data)
  });
}

async function apiApproveBooking(bookingId) {
  return apiRequest(`/bookings/${bookingId}/approve`, {
    method: 'PUT'
  });
}

async function apiRejectBooking(bookingId) {
  return apiRequest(`/bookings/${bookingId}/reject`, {
    method: 'PUT'
  });
}

async function apiCancelBooking(bookingId) {
  return apiRequest(`/bookings/${bookingId}/cancel`, {
    method: 'PUT'
  });
}

async function apiGetBuilds() {
  return apiRequest('/builds');
}

async function apiGetCurrentBuild() {
  return apiRequest('/builds/current');
}

async function apiCreateBuild(name, startDate, endDate) {
  return apiRequest('/builds', {
    method: 'POST',
    body: JSON.stringify({ name, startDate, endDate })
  });
}

async function apiSetCurrentBuild(buildId) {
  return apiRequest(`/builds/${buildId}/set-current`, {
    method: 'PUT'
  });
}

async function apiDeleteBuild(buildId) {
  return apiRequest(`/builds/${buildId}`, {
    method: 'DELETE'
  });
}

async function apiGetLogs() {
  return apiRequest('/logs');
}

async function apiGetStats() {
  return apiRequest('/stats/bookings');
}

async function apiGetBuildings() {
  return apiRequest('/buildings');
}