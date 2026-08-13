import { useState } from "react";
import { post } from "../api";

interface ChatData {
  response: string;
  intent: string;
  status: string;
}

export function ChatView() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<ChatData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const send = async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await post<ChatData>("/chat", { text });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <textarea
        rows={3}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Nhập yêu cầu…"
        data-testid="chat-input"
      />
      <br />
      <button className="primary" onClick={send} disabled={busy} data-testid="chat-send">
        {busy ? "Đang xử lý…" : "Gửi"}
      </button>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="card" data-testid="chat-result">
          <p>
            <em>intent: {result.intent}</em>
          </p>
          <pre>{result.response}</pre>
        </div>
      )}
    </div>
  );
}
