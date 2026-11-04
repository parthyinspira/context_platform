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
  // Full chain: discover → plan → create harvest_runs row (APPROVED).
  // The caller then launches a harvester container separately; for now the
  // run row is returned so the UI can poll it via GET /runs/{id}.
  const discoverResp = await fetch(`${API_BASE_URL}/sources/${sourceId}/discover`, { method: "POST" });
  if (!discoverResp.ok) throw new Error(`discover failed with ${discoverResp.status}`);

  const planResp = await fetch(`${API_BASE_URL}/sources/${sourceId}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  if (!planResp.ok) throw new Error(`plan failed with ${planResp.status}`);
  const planData = await planResp.json();

  const runResp = await fetch(`${API_BASE_URL}/sources/${sourceId}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan: planData.plan ?? planData }),
  });
  if (!runResp.ok) throw new Error(`create run failed with ${runResp.status}`);
  return runResp.json();
}

export async function deleteSource(sourceId) {
  const response = await fetch(`${API_BASE_URL}/sources/${sourceId}`, { method: "DELETE" });
  if (!response.ok) {
    throw new Error(`DELETE /sources/${sourceId} failed with ${response.status}`);
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

export async function getGraph(sourceIds = []) {
  const params = new URLSearchParams();
  sourceIds.forEach((id) => params.append("source_id", id));
  const qs = sourceIds.length === 1 ? `?source_id=${sourceIds[0]}` : "";
  const response = await fetch(`${API_BASE_URL}/graph${qs}`);
  if (!response.ok) {
    throw new Error(`GET /graph failed with ${response.status}`);
  }
  return response.json();
}

export async function runAgentDemo(agentName, taskKey) {
  const response = await fetch(`${API_BASE_URL}/agents/${agentName}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task_key: taskKey }),
  });
  if (!response.ok) {
    throw new Error(`POST /agents/${agentName}/run failed with ${response.status}`);
  }
  return response.json();
}

export async function agentChat(payload) {
  const response = await fetch(`${API_BASE_URL}/agents/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`POST /agents/chat failed with ${response.status}`);
  return response.json();
}

export async function listRuns(limit = 50) {
  const response = await fetch(`${API_BASE_URL}/runs?limit=${limit}`);
  if (!response.ok) throw new Error(`GET /runs failed with ${response.status}`);
  return response.json();
}

export async function listSourceRuns(sourceId, limit = 10) {
  const response = await fetch(`${API_BASE_URL}/sources/${sourceId}/runs?limit=${limit}`);
  if (!response.ok) throw new Error(`GET /sources/${sourceId}/runs failed with ${response.status}`);
  return response.json();
}

export async function extractOntology() {
  const response = await fetch(`${API_BASE_URL}/ontology/extract`, { method: "POST" });
  if (!response.ok) throw new Error(`POST /ontology/extract failed with ${response.status}`);
  return response.json();
}

export async function normalizeRun(runId) {
  const response = await fetch(`${API_BASE_URL}/runs/${runId}/normalize`, { method: "POST" });
  if (!response.ok) {
    throw new Error(`POST /runs/${runId}/normalize failed with ${response.status}`);
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
