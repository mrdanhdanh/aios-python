import { useEffect, useState } from "react";
import { get } from "../api";

interface Artifact {
  id: string;
  name: string;
  artifact_type: string;
  metadata: Record<string, unknown>;
}

export function ArtifactBrowser() {
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  useEffect(() => {
    get<Artifact[]>("/artifacts").then(setArtifacts).catch(() => undefined);
  }, []);
  if (artifacts.length === 0) return <p data-testid="artifacts-empty">No artifacts</p>;
  return (
    <div>
      {artifacts.map((a) => (
        <div key={a.id} className="card" data-testid="artifact-row">
          <strong>{a.name}</strong> ({a.artifact_type}) — {a.id}
        </div>
      ))}
    </div>
  );
}
