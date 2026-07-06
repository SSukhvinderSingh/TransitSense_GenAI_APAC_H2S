const API_BASE = import.meta.env.VITE_API_URL || '';

export async function postQuery(query, sessionId) {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Server error ${res.status}` }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export async function fetchStatsSummary() {
  const res = await fetch(`${API_BASE}/stats/summary`);
  if (!res.ok) throw new Error('Failed to load summary');
  return res.json();
}

export async function fetchRoutes() {
  const res = await fetch(`${API_BASE}/stats/routes`);
  if (!res.ok) throw new Error('Failed to load routes');
  return res.json();
}

export async function fetchForecast(routeId) {
  const res = await fetch(`${API_BASE}/stats/forecast/${routeId}`);
  if (!res.ok) throw new Error('Failed to load forecast');
  return res.json();
}

export async function fetchZones() {
  const res = await fetch(`${API_BASE}/stats/zones`);
  if (!res.ok) throw new Error('Failed to load zones');
  return res.json();
}

export async function fetchAnomalies(routeId) {
  const res = await fetch(`${API_BASE}/stats/anomalies${routeId ? `/${routeId}` : ''}`);
  if (!res.ok) throw new Error('Failed to load anomalies');
  return res.json();
}
