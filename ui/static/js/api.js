const BASE_URL = "/api/v1";

// Auth (when CLR_API_KEY is configured) rides the clr_session cookie set by
// POST /auth/login — no key is ever embedded in the page. A 401 here means
// the session expired or was never established; bounce to the login screen.
function handleUnauthorized(res) {
  if (res.status === 401) {
    window.location.reload();
  }
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

export const uuid = () =>
  typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, c =>
        (c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16)
      );

async function post(path, body, timeout = 30000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(BASE_URL + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      handleUnauthorized(res);
      const err = await res.json().catch(() => ({}));
      throw new ApiError(res.status, err.detail ?? "Request failed");
    }
    return res.json();
  } catch (e) {
    clearTimeout(timer);
    if (e.name === "AbortError") throw new ApiError(408, "Request timed out after " + timeout / 1000 + "s");
    throw e;
  }
}

async function get(path) {
  const res = await fetch(BASE_URL + path, { credentials: "same-origin" });
  if (!res.ok) {
    handleUnauthorized(res);
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail ?? "Request failed");
  }
  return res.json();
}

async function del(path) {
  const res = await fetch(BASE_URL + path, { method: "DELETE", credentials: "same-origin" });
  if (!res.ok) {
    handleUnauthorized(res);
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, err.detail ?? "Request failed");
  }
  return res.json();
}

export async function processMessage(message) {
  return post("/process", { message });
}

export async function processBatch(messages) {
  return post("/process/batch", { messages }, 120000);
}

export async function rewriteText(text) {
  return post("/rewrite", { text });
}

export async function summarizeText(text) {
  return post("/summarize", { text });
}

export async function filterNotification(notification) {
  return post("/filter/notification", { notification });
}

export async function decide(task) {
  return post("/decide", { task });
}

export async function health() {
  return get("/health");
}

export async function getHistory(limit = 20, offset = 0) {
  return get(`/history?limit=${limit}&offset=${offset}`);
}

export async function deleteHistoryItem(id) {
  return del(`/history/${encodeURIComponent(id)}`);
}

export async function clearHistory() {
  return del("/history");
}
