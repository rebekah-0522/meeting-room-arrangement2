/**
 * LocalStorage persistence layer
 */
const STORAGE_KEY = 'foxconn_meeting_rooms_v1';

function defaultState() {
  return {
    rooms: JSON.parse(JSON.stringify(DEFAULT_ROOMS)),
    bookings: [],
    builds: [],
    currentBuildId: null,
    users: {},
    logs: [],
    notifications: [],
    settings: {
      epmEmail: EPM_EMAIL,
      epmName: EPM_NAME
    }
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const state = JSON.parse(raw);
    if (!state.rooms || state.rooms.length === 0) state.rooms = defaultState().rooms;
    if (!state.bookings) state.bookings = [];
    if (!state.logs) state.logs = [];
    if (!state.notifications) state.notifications = [];
    if (!state.users) state.users = {};
    if (!state.builds) state.builds = [];
    return state;
  } catch {
    return defaultState();
  }
}

function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

let appState = loadState();

function getState() {
  return appState;
}

function setState(updater) {
  if (typeof updater === 'function') {
    appState = updater(appState);
  } else {
    appState = updater;
  }
  saveState(appState);
  return appState;
}

function generateId(prefix = 'id') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function getRoomById(roomId) {
  return appState.rooms.find(r => r.id === roomId);
}

function getBuildById(buildId) {
  return appState.builds.find(b => b.id === buildId);
}

function getCurrentBuild() {
  if (!appState.currentBuildId) return null;
  return getBuildById(appState.currentBuildId);
}

function getUserRecord(email) {
  const key = email.toLowerCase();
  if (!appState.users[key]) {
    appState.users[key] = {
      email: key,
      name: '',
      password: '123456',
      role: key === EPM_EMAIL.toLowerCase() ? ROLES.epm : ROLES.user,
      cancelHistory: [],
      badCreditMonths: []
    };
  }
  return appState.users[key];
}

function saveUserRecord(user) {
  appState.users[user.email.toLowerCase()] = user;
  saveState(appState);
}

function addLog(action, detail, operator) {
  const entry = {
    id: generateId('log'),
    timestamp: new Date().toISOString(),
    operator: operator || '系统',
    action,
    detail
  };
  appState.logs.unshift(entry);
  if (appState.logs.length > 500) appState.logs = appState.logs.slice(0, 500);
  saveState(appState);
  return entry;
}

function addNotification(notification) {
  const item = {
    id: generateId('ntf'),
    read: false,
    createdAt: new Date().toISOString(),
    ...notification
  };
  appState.notifications.unshift(item);
  saveState(appState);
  return item;
}

function getUnreadNotifications(email) {
  return appState.notifications.filter(n =>
    !n.read && (!n.targetEmail || n.targetEmail.toLowerCase() === email.toLowerCase())
  );
}

function markNotificationRead(id) {
  const n = appState.notifications.find(x => x.id === id);
  if (n) {
    n.read = true;
    saveState(appState);
  }
}

function getMonthKey(dateStr) {
  return dateStr.slice(0, 7);
}

function getCancelCountThisMonth(email) {
  const user = getUserRecord(email);
  const monthKey = getMonthKey(todayStr());
  return user.cancelHistory.filter(c => c.slice(0, 7) === monthKey).length;
}

function isBadCredit(email) {
  const user = getUserRecord(email);
  const monthKey = getMonthKey(todayStr());
  return user.badCreditMonths.includes(monthKey) || getCancelCountThisMonth(email) > BAD_CREDIT_THRESHOLD;
}

function recordCancellation(email) {
  const user = getUserRecord(email);
  const now = todayStr();
  user.cancelHistory.push(now);
  const monthKey = getMonthKey(now);
  if (getCancelCountThisMonth(email) > BAD_CREDIT_THRESHOLD && !user.badCreditMonths.includes(monthKey)) {
    user.badCreditMonths.push(monthKey);
  }
  saveUserRecord(user);
}

function resetDemoData() {
  appState = defaultState();
  saveState(appState);
}
