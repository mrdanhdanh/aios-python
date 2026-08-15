import { useState } from "react";
import { ArtifactBrowser } from "./views/ArtifactBrowser";
import { ChatView } from "./views/ChatView";
import { EventTimeline } from "./views/EventTimeline";
import { ExecutionTimeline } from "./views/ExecutionTimeline";
import { HealthView } from "./views/HealthView";
import { MemoryView } from "./views/MemoryView";
import { ModelUsage } from "./views/ModelUsage";
import { Overview } from "./views/Overview";
import { SkillMarketplace } from "./views/SkillMarketplace";
import { ToolUsage } from "./views/ToolUsage";
import { WorkflowView } from "./views/WorkflowView";

// Dashboard 1.0 — 11 tabs (PLAN §M10-29). Views M3 giữ nguyên, nhóm lại.
// Overview · Operations · Autonomy · Agents · Workflows · Knowledge · Memory
// · Harness · Enterprise · Ecosystem · System
const TABS: Array<[string, React.ComponentType]> = [
  ["Overview", Overview],
  ["Operations", EventTimeline],
  ["Autonomy", ExecutionTimeline],
  ["Agents", ChatView],
  ["Workflows", WorkflowView],
  ["Knowledge", ToolUsage],
  ["Memory", MemoryView],
  ["Harness", HealthView],
  ["Enterprise", ArtifactBrowser],
  ["Ecosystem", SkillMarketplace],
  ["System", ModelUsage],
];

export function App() {
  const [active, setActive] = useState(0);
  const [label, View] = TABS[active];
  return (
    <div>
      <nav aria-label="views">
        {TABS.map(([name], i) => (
          <button
            key={name}
            className={i === active ? "active" : ""}
            onClick={() => setActive(i)}
            data-testid={`tab-${name.toLowerCase()}`}
          >
            {name}
          </button>
        ))}
      </nav>
      <main>
        <h2>{label}</h2>
        <View />
      </main>
    </div>
  );
}
