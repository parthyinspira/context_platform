const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const SCHEDULER_BASE_URL = import.meta.env.VITE_SCHEDULER_BASE_URL ?? "http://localhost:8001";

export async function listSources() {
  const response = await fetch(`${API_BASE_URL}/sources`);
  if (!response.ok) {
    throw new Error(`GET /sources failed with ${response.status}`);
  }
  return response.json();
}

export async function runSource(sourceId) {
  const response = await fetch(`${SCHEDULER_BASE_URL}/sources/${sourceId}/run`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`POST /sources/${sourceId}/run failed with ${response.status}`);
  }
  return response.json();
}

export async function testConnection(payload) {
  const response = await fetch(`${API_BASE_URL}/sources/test-connection`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`POST /sources/test-connection failed with ${response.status}`);
  }
  return response.json();
}

export async function createSource(payload) {
  const response = await fetch(`${API_BASE_URL}/sources`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`POST /sources failed with ${response.status}`);
  }
  return response.json();
}
