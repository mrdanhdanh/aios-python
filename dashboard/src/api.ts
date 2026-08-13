/** API client — C1-02: handle 3 error envelopes. */

const BASE: string = (import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE ?? ""; // "" = relative (dev proxy)

export async function get<T = unknown>(path: string): Promise<T> {
  return request<T>("GET", path);
}

export async function post<T = unknown>(path: string, body: unknown): Promise<T> {
  return request<T>("POST", path, body);
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1${path}`, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error(`network error: ${err instanceof Error ? err.message : String(err)}`);
  }

  let parsed: unknown = null;
  try {
    parsed = await res.json();
  } catch {
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    throw new Error("invalid JSON response");
  }

  const obj = parsed as { data?: T; error?: { message?: string; code?: string }; detail?: string };

  if (obj && obj.error && obj.error.message) throw new Error(obj.error.message);
  if (obj && obj.detail) throw new Error(obj.detail);
  if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
  if (!obj || !("data" in obj)) throw new Error("malformed response: missing data");
  return obj.data as T;
}
