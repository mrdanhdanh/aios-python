/** AIOS backend client — POST /api/v1/chat with 3-envelope error handling. */

export interface ChatData {
  response: string;
  intent: string;
  status: string;
}

export class AiosClient {
  constructor(serverUrl: string) {
    this.serverUrl = serverUrl.replace(/\/+$/, "");
  }
  private serverUrl: string;

  async callChat(text: string, intent?: string): Promise<ChatData> {
    let res: Response;
    try {
      res = await fetch(`${this.serverUrl}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(intent ? { text, intent } : { text }),
      });
    } catch (err) {
      throw new Error(`network error: ${err instanceof Error ? err.message : String(err)}`);
    }

    let parsed: unknown = null;
    try {
      parsed = await res.json();
    } catch {
      throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }
    const obj = parsed as { data?: ChatData; error?: { message?: string }; detail?: unknown };
    if (obj?.error?.message) throw new Error(obj.error.message);
    if (!res.ok && obj?.detail != null) {
      throw new Error(typeof obj.detail === "string" ? obj.detail : JSON.stringify(obj.detail));
    }
    if (!res.ok) throw new Error(`HTTP ${res.status} ${res.statusText}`);
    if (!obj?.data) throw new Error("malformed response: missing data");
    return obj.data;
  }
}
