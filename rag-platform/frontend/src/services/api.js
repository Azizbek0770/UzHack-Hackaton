const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function parseError(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    const errorJson = await response.json();
    return errorJson.detail || "Request failed";
  }
  const errorText = await response.text();
  return errorText || "Request failed";
}

/**
 * Submit a query to the backend.
 * @param {string} question
 * @returns {Promise<{answer: string, relevant_chunks: Array<{file: string, page: number}>, response_time_ms?: number}>}
 */
export async function queryRag(question, options = {}) {
  const payload = { question };
  if (options.company) {
    payload.company = options.company;
  }
  if (options.doc_type) {
    payload.doc_type = options.doc_type;
  }
  const timeoutMs = options.timeoutMs ?? 45000;
  const controller = new AbortController();
  const timeoutHandle = setTimeout(() => controller.abort(), timeoutMs);
  if (options.signal) {
    if (options.signal.aborted) {
      controller.abort();
    } else {
      options.signal.addEventListener("abort", () => controller.abort(), { once: true });
    }
  }
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: controller.signal
  });
  clearTimeout(timeoutHandle);

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return response.json();
}

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getMetrics() {
  const response = await fetch(`${API_BASE_URL}/metrics`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getIngestionReport() {
  const response = await fetch(`${API_BASE_URL}/ingestion/report`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getAuditRuns() {
  const response = await fetch(`${API_BASE_URL}/audit/runs`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function uploadDocuments({ company, files }) {
  const form = new FormData();
  form.append("company", company);
  files.forEach((file) => form.append("files", file));
  const response = await fetch(`${API_BASE_URL}/ingestion/upload`, {
    method: "POST",
    body: form
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function getUploadedFiles() {
  const response = await fetch(`${API_BASE_URL}/ingestion/uploads`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}
