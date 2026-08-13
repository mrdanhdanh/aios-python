import { useState } from "react";
import { ArtifactBrowser } from "./views/ArtifactBrowser";
import { ChatView } from "./views/ChatView";
import { EventTimeline } from "./views/EventTimeline";
import { HealthView } from "./views/HealthView";
import { MemoryView } from "./views/MemoryView";
import { ModelUsage } from "./views/ModelUsage";
import { PromptInspector } from "./views/PromptInspector";
import { SkillMarketplace } from "./views/SkillMarketplace";
import { ToolUsage } from "./views/ToolUsage";
import { WorkflowView } from "./views/WorkflowView";

const TABS: Array<[string, React.ComponentType]> = [
  ["Chat", ChatView],
  ["Workflow", WorkflowView],
  ["Events", EventTimeline],
  ["Tools", ToolUsage],
  ["Memory", MemoryView],
  ["Artifacts", ArtifactBrowser],
  ["Skills", SkillMarketplace],
  ["Models", ModelUsage],
  ["Prompts", PromptInspector],
  ["Health", HealthView],
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
