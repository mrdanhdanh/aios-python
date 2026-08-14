"""Capability resolver (TASK-026 §YC-5): check capabilities, fill agents."""

from __future__ import annotations

from .contracts import RiskItem, RiskReport, TaskSpec, ValidationRule

_AGENT_MAP = {
    "review": "coder",
    "test": "coder",
    "coding": "coder",
    "chat": "general",
    "doctor": "doctor",
    "system": "system_doctor",
}


class CapabilityResolver:
    """Deterministic capability check + agent assignment (model_copy-based)."""

    def resolve(self, tasks: list[TaskSpec], capabilities, intent: str = "") -> tuple[list[TaskSpec], RiskReport]:
        known = set(capabilities.list())
        issues: list[RiskItem] = []
        resolved: list[TaskSpec] = []
        for task in tasks:
            for capability in task.capabilities:
                if capability not in known:
                    issues.append(RiskItem(
                        level="high", kind="unknown_capability",
                        message=f"task {task.id} requires unknown capability {capability!r}"))
            task = self._fill_agent(task, intent)
            for capability in task.capabilities:
                if capability in known and not capabilities.tools_for(capability):
                    issues.append(RiskItem(
                        level="medium", kind="capability_no_tools",
                        message=f"capability {capability!r} has no tools"))
            resolved.append(task)
        issues.sort(key=lambda item: (item.level, item.kind))
        return resolved, RiskReport(items=issues)

    def _fill_agent(self, task: TaskSpec, intent: str) -> TaskSpec:
        if task.agent:
            return task
        agent = _AGENT_MAP.get(intent) or _AGENT_MAP["chat"]
        return task.model_copy(update={"agent": agent})
