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

export async function discoverSource(sourceId) {
  const response = await fetch(`${API_BASE_URL}/sources/${sourceId}/discover`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`POST /sources/${sourceId}/discover failed with ${response.status}`);
  }
  return response.json();
}

export async function planSource(sourceId, body) {
  const response = await fetch(`${API_BASE_URL}/sources/${sourceId}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST /sources/${sourceId}/plan failed with ${response.status}`);
  }
  return response.json();
}

export async function createRun(sourceId, plan) {
  const response = await fetch(`${API_BASE_URL}/sources/${sourceId}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan }),
  });
  if (!response.ok) {
    throw new Error(`POST /sources/${sourceId}/runs failed with ${response.status}`);
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

export async function getRun(runId) {
  const response = await fetch(`${API_BASE_URL}/runs/${runId}`);
  if (!response.ok) {
    throw new Error(`GET /runs/${runId} failed with ${response.status}`);
  }
  return response.json();
}

export async function stopRun(runId) {
  const response = await fetch(`${API_BASE_URL}/runs/${runId}/stop`, { method: "PATCH" });
  if (!response.ok) {
    throw new Error(`PATCH /runs/${runId}/stop failed with ${response.status}`);
  }
  return response.json();
}

export async function getEntity(entityId) {
  const response = await fetch(`${API_BASE_URL}/entities/${entityId}`);
  if (!response.ok) {
    throw new Error(`GET /entities/${entityId} failed with ${response.status}`);
  }
  return response.json();
}

export async function getRunValidation(runId) {
  const response = await fetch(`${API_BASE_URL}/runs/${runId}/validation`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`GET /runs/${runId}/validation failed with ${response.status}`);
  }
  return response.json();
}
