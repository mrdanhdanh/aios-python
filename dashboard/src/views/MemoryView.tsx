import { useEffect, useState } from "react";
import { get } from "../api";

interface Conversation {
  id: string;
  messages: Array<{ role: string; content: string }>;
}

export function MemoryView() {
  const [convs, setConvs] = useState<Conversation[]>([]);
  useEffect(() => {
    // C1-01: session_id=api khớp chat hardcode.
    get<Conversation[]>("/conversations?session_id=api").then(setConvs).catch(() => undefined);
  }, []);
  if (convs.length === 0) return <p data-testid="memory-empty">No conversations</p>;
  return (
    <div>
      {convs.map((c) => (
        <div key={c.id} className="card" data-testid="conversation-row">
          <strong>{c.id}</strong>
          <ul>
            {c.messages.map((m, i) => (
              <li key={i}>
                <em>{m.role}:</em> {m.content.slice(0, 120)}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
