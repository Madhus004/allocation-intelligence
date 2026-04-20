const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function handleResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }
  return response.json();
}

export async function fetchDecisionTraces(limit = 50) {
  const response = await fetch(`${API_BASE_URL}/decision-traces?limit=${limit}`);
  return handleResponse(response);
}

export async function fetchDecisionTraceDetail(runId) {
  const response = await fetch(`${API_BASE_URL}/decision-traces/${runId}`);
  return handleResponse(response);
}

export async function fetchOptionEvaluations(runId) {
  const response = await fetch(`${API_BASE_URL}/option-evaluations/${runId}`);
  return handleResponse(response);
}

export async function evaluateOrder(payload) {
  const response = await fetch(`${API_BASE_URL}/evaluate-order`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}