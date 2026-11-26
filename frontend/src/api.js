const API_BASE = '';

async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  return res;
}

export const api = {
  register: (data) => apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login:    (data) => apiFetch('/auth/login',    { method: 'POST', body: JSON.stringify(data) }),
  getMe:    ()     => apiFetch('/auth/me'),
  predict:  (data) => apiFetch('/predict',       { method: 'POST', body: JSON.stringify(data) }),
  explain:  (data) => apiFetch('/explain',       { method: 'POST', body: JSON.stringify(data) }),
  generatePlan: (data) => apiFetch('/generate-plan', { method: 'POST', body: JSON.stringify(data) }),
  chat:     (data) => apiFetch('/chat',          { method: 'POST', body: JSON.stringify(data) }),
};
