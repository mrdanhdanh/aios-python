"""Goal reporting (TASK-022 — Goal Manager nâng cao) — progress + báo cáo.

Reads via GoalManager public API only (no DB access, no GoalManager changes).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .goal import GoalManager, TaskStatus

# failed_tasks = FAILED + CANCELLED (đồng bộ _recompute_goal — P2-5 v1)
_FAILED_TASK_STATUSES = {TaskStatus.FAILED, TaskStatus.CANCELLED}

_ALL_STATUSES = ("active", "paused", "completed", "failed", "cancelled")


@dataclass(frozen=True)
class GoalReport:
    total: int
    by_status: dict[str, int]
    avg_progress: float
    completed_tasks: int
    failed_tasks: int
    goals: tuple[dict[str, Any], ...]


class GoalReporter:
    def __init__(self, goal_manager: GoalManager) -> None:
        self._manager = goal_manager

    def report(self) -> GoalReport:
        goals = self._manager.list_goals(limit=10_000)  # P3-1: tránh truncate
        by_status = {status: 0 for status in _ALL_STATUSES}
        completed_tasks = 0
        failed_tasks = 0
        progress_sum = 0.0
        entries: list[dict[str, Any]] = []
        for goal in sorted(goals, key=lambda g: g.id):
            by_status[goal.status.value] = by_status.get(goal.status.value, 0) + 1
            completed_tasks += sum(1 for t in goal.tasks if t.status == TaskStatus.COMPLETED)
            failed_tasks += sum(1 for t in goal.tasks if t.status in _FAILED_TASK_STATUSES)
            progress_sum += goal.progress
            entries.append(
                {
                    "id": goal.id,
                    "title": goal.title,
                    "status": goal.status.value,
                    "progress": goal.progress,
                    "task_count": len(goal.tasks),
                }
            )
        total = len(goals)
        return GoalReport(
            total=total,
            by_status=by_status,
            avg_progress=(progress_sum / total) if total else 0.0,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            goals=tuple(entries),
        )

    def report_goal(self, goal_id: str) -> dict[str, Any] | None:
        goal = self._manager.get_goal(goal_id)
        if goal is None:
            return None
        return {
            "id": goal.id,
            "title": goal.title,
            "description": goal.description,
            "status": goal.status.value,
            "progress": goal.progress,
            "created_at": goal.created_at,
            "updated_at": goal.updated_at,
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "workflow_name": t.workflow_name,
                    "status": t.status.value,
                    "priority": t.priority,
                    "result": t.result,
                }
                for t in goal.tasks
            ],
        }
