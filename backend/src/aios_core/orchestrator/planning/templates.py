"""Task templates (TASK-026 §YC-3): deterministic skeletons per intent.

``StepSpec`` is an internal class here (R3-2); ``TASK_TEMPLATES`` maps intent
-> TemplateSkeleton. Templates registered here are the source of TEMPLATE
planning (PLAN §12 review example is exact: 6 nodes).
"""

from __future__ import annotations

import threading
from typing import Any

from pydantic import BaseModel, ConfigDict

from ...kernel.execution_plan import PlanNodeType


class StepSpec(BaseModel):
    """A template step (internal to templates.py — R3-2)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    type: PlanNodeType
    description: str = ""
    capabilities: list[str] = []
    agent: str = ""
    depends_on: list[str] = []
    timeout_s: float = 300.0
    retries: int = 0


class TemplateSkeleton:
    """Named template: intent -> ordered steps (thread-safe registry)."""

    def __init__(self, intent: str, steps: list[StepSpec]) -> None:
        self.intent = intent
        self.steps = list(steps)

    def to_task_specs(self) -> list[Any]:
        from .contracts import TaskSpec

        return [
            TaskSpec(
                id=step.id,
                name=step.name,
                type=step.type,
                description=step.description,
                capabilities=list(step.capabilities),
                agent=step.agent,
                depends_on=list(step.depends_on),
                timeout_s=step.timeout_s,
                retries=step.retries,
            )
            for step in self.steps
        ]


def _review_skeleton() -> TemplateSkeleton:
    return TemplateSkeleton(
        intent="review",
        steps=[
            StepSpec(id="T1", name="Analyze module", type=PlanNodeType.LLM,
                     agent="coder", capabilities=["code_analysis"], depends_on=[]),
            StepSpec(id="T2", name="Scan vulnerabilities", type=PlanNodeType.TASK,
                     agent="coder", capabilities=["code_analysis"], depends_on=["T1"]),
            StepSpec(id="T3", name="Scan missing tests", type=PlanNodeType.TASK,
                     agent="coder", capabilities=["code_analysis"], depends_on=["T1"]),
            StepSpec(id="T4", name="Write tests", type=PlanNodeType.TASK,
                     agent="coder", capabilities=["test_writing"], depends_on=["T2", "T3"]),
            StepSpec(id="T5", name="Run tests", type=PlanNodeType.TOOL,
                     agent="coder", capabilities=["test_run"], depends_on=["T4"]),
            StepSpec(id="T6", name="Report", type=PlanNodeType.TASK,
                     agent="coder", capabilities=["reporting"], depends_on=["T5"]),
        ],
    )


def _coding_skeleton() -> TemplateSkeleton:
    return TemplateSkeleton(
        intent="coding",
        steps=[
            StepSpec(id="T1", name="Implement", type=PlanNodeType.LLM,
                     agent="coder", capabilities=["code_generation"], depends_on=[]),
            StepSpec(id="T2", name="Verify", type=PlanNodeType.TASK,
                     agent="coder", capabilities=["test_run"], depends_on=["T1"]),
            StepSpec(id="T3", name="Report", type=PlanNodeType.TASK,
                     agent="coder", capabilities=["reporting"], depends_on=["T2"]),
        ],
    )


#: R3-3: only review/coding have templates — "test" goes the RULE path.
TASK_TEMPLATES: dict[str, TemplateSkeleton] = {
    "review": _review_skeleton(),
    "coding": _coding_skeleton(),
}

_TEMPLATES_LOCK = threading.RLock()


def register_template(name: str, skeleton: TemplateSkeleton) -> None:
    """Additive registration (thread-safe, pattern WorkflowLibrary)."""
    with _TEMPLATES_LOCK:
        TASK_TEMPLATES[name] = skeleton


def get_template(intent: str) -> TemplateSkeleton | None:
    with _TEMPLATES_LOCK:
        return TASK_TEMPLATES.get(intent)
