import { useEffect, useState } from "react";
import { get } from "../api";

/** Execution Timeline — Goal→Plan→Agent→Capability→Tool→Result→Evaluation (M10-F7). */

export interface TimelineStep {
  seq: number;
  type: string;
  label: string;
  execution_id: string;
  ts: string;
}

export function ExecutionTimeline() {
  const [steps, setSteps] = useState<TimelineStep[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    get<TimelineStep[]>("/m10/timeline")
      .then(setSteps)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (steps.length === 0) return <p>No executions yet.</p>;
  return (
    <div data-testid="execution-timeline">
      <h3>Execution Timeline</h3>
      <ol>
        {steps.map((s) => (
          <li key={`${s.seq}-${s.label}`} className="card" data-testid="timeline-step">
            <span className="ok">[{s.type}]</span> {s.label}
            <span className="muted"> — {s.execution_id}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
