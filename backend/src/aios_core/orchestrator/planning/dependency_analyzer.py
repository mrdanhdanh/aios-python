"""Dependency analyzer (TASK-026 §YC-4): verify + topological order.

Does NOT add edges — templates/rules declare dependencies. Violations are
flagged via an internal ``invalid`` attribute consumed by the validator.
"""

from __future__ import annotations

from collections import defaultdict, deque

from .contracts import TaskSpec


class DependencyAnalyzer:
    """Normalize + verify dependency graph, stable topological order.

    Returns ``(ordered_tasks, invalid_ids)`` — invalid flags are surfaced
    to the validator (TaskSpec is extra="forbid"; no dynamic attributes).
    """

    def analyze(self, tasks: list[TaskSpec]) -> tuple[list[TaskSpec], set[str]]:
        ids = {task.id for task in tasks}
        flagged: set[str] = set()
        for task in tasks:
            for dep in task.depends_on:
                if dep not in ids or dep == task.id:
                    flagged.add(task.id)
        ordered = self._topological(tasks, ids)
        return ordered, flagged

    def _topological(self, tasks: list[TaskSpec], ids: set[str]) -> list[TaskSpec]:
        by_id = {task.id: task for task in tasks}
        # Kahn with stable tie-break (id asc).
        dependents: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {task.id: 0 for task in tasks}
        for task in tasks:
            for dep in task.depends_on:
                if dep in ids and dep != task.id:
                    dependents[dep].append(task.id)
                    in_degree[task.id] += 1
        ready = deque(sorted((tid for tid, deg in in_degree.items() if deg == 0)))
        result: list[TaskSpec] = []
        while ready:
            tid = ready.popleft()
            result.append(by_id[tid])
            for child in sorted(dependents.get(tid, [])):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    ready.append(child)
        # Cycle/unknown remainders appended in stable order (validator flags them).
        remaining = [by_id[tid] for tid in sorted(ids) if by_id[tid] not in result]
        return result + remaining
