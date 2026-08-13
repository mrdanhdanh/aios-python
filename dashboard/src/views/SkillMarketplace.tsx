import { useEffect, useState } from "react";
import { get } from "../api";

interface Skill {
  id: string;
  name: string;
  version: string;
  state: string;
}

export function SkillMarketplace() {
  const [skills, setSkills] = useState<Skill[]>([]);
  useEffect(() => {
    get<Skill[]>("/skills").then(setSkills).catch(() => undefined);
  }, []);
  if (skills.length === 0) return <p data-testid="skills-empty">No skills</p>;
  return (
    <div>
      {skills.map((s) => (
        <div key={s.id} className="card" data-testid="skill-row">
          <strong>{s.name}</strong> v{s.version} — {s.state}
        </div>
      ))}
    </div>
  );
}
