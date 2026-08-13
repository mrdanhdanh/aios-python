import { useEffect, useState } from "react";
import { get } from "../api";

interface Goal {
  id: string;
  title: string;
  status: string;
  progress: number;
}

export function WorkflowView() {
  const [goals, setGoals] = useState<Goal[]>([]);
  useEffect(() => {
    get<Goal[]>("/goals").then(setGoals).catch(() => undefined);
  }, []);
  if (goals.length === 0) return <p data-testid="workflow-empty">No goals</p>;
  return (
    <div>
      {goals.map((g) => (
        <div key={g.id} className="card" data-testid="goal-row">
          {g.title} — {g.status} ({Math.round(g.progress * 100)}%)
        </div>
      ))}
    </div>
  );
}
