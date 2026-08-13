import { useEffect, useState } from "react";
import { get } from "../api";

interface PromptInfo {
  id: string;
  name: string;
  version: string;
  description: string;
}

export function PromptInspector() {
  const [prompts, setPrompts] = useState<PromptInfo[]>([]);
  useEffect(() => {
    get<PromptInfo[]>("/prompts").then(setPrompts).catch(() => undefined);
  }, []);
  if (prompts.length === 0) return <p data-testid="prompts-empty">No prompts</p>;
  return (
    <div>
      {prompts.map((p) => (
        <div key={p.id} className="card" data-testid="prompt-row">
          <strong>{p.name}</strong> ({p.id}) v{p.version} — {p.description}
        </div>
      ))}
    </div>
  );
}
