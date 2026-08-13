import { useEffect, useState } from "react";
import { get } from "../api";

interface Tool {
  id: string;
  tool_type: string;
  capabilities: string[];
  available: boolean;
}

interface SandboxStats {
  total: number;
  idle: number;
  busy: number;
  max_size: number;
}

export function ToolUsage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [sandbox, setSandbox] = useState<SandboxStats | null>(null);
  useEffect(() => {
    get<Tool[]>("/tools").then(setTools).catch(() => undefined);
    get<SandboxStats>("/sandbox").then(setSandbox).catch(() => undefined);
  }, []);
  if (tools.length === 0) return <p data-testid="tools-empty">No tools</p>;
  return (
    <div>
      {sandbox && (
        <p>
          Sandbox pool: {sandbox.busy}/{sandbox.total} busy (max {sandbox.max_size})
        </p>
      )}
      {tools.map((t) => (
        <div key={t.id} className="card" data-testid="tool-row">
          <strong>{t.id}</strong> — {t.tool_type} — {t.capabilities.join(", ")} —{" "}
          <span className={t.available ? "ok" : "fail"}>{t.available ? "available" : "down"}</span>
        </div>
      ))}
    </div>
  );
}
