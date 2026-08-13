import { useEffect, useState } from "react";
import { get } from "../api";

interface HealthData {
  components: Array<{ name: string; ok: boolean; status: string; detail: string }>;
  health_score: number;
}

export function HealthView() {
  const [data, setData] = useState<HealthData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    get<HealthData>("/health").then(setData).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p>Loading…</p>;
  return (
    <div>
      <p>
        Health score: <strong>{data.health_score}</strong>
      </p>
      {data.components.map((c) => (
        <div key={c.name} className="card" data-testid="health-component">
          <span className={c.ok ? "ok" : "fail"}>{c.name}</span> — {c.status}: {c.detail}
        </div>
      ))}
    </div>
  );
}
