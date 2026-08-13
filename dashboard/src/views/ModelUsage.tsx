import { useEffect, useState } from "react";
import { get } from "../api";

interface ModelInfo {
  name: string;
  available: boolean;
}

export function ModelUsage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  useEffect(() => {
    get<ModelInfo[]>("/models").then(setModels).catch(() => undefined);
  }, []);
  if (models.length === 0) return <p data-testid="models-empty">No models</p>;
  return (
    <div>
      {models.map((m) => (
        <div key={m.name} className="card" data-testid="model-row">
          <strong>{m.name}</strong> —{" "}
          <span className={m.available ? "ok" : "fail"}>{m.available ? "available" : "down"}</span>
        </div>
      ))}
    </div>
  );
}
