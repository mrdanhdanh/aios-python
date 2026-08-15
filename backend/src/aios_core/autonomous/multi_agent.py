"""Multi-Agent Autonomy (TASK-059 — M9-P4).

AIOS tự quyết mode — chỉ thêm complexity khi tạo giá trị đo được (PLAN
§M9-23). **Autonomous Delegation** (§M9-24): Task → Agent (owner, deadline,
budget, output contract). V1 deterministic: chạy tuần tự, mode quyết định
THỨ TỰ + AGGREGATION (parallel thật → Parallel Scheduler M5 wiring sau,
C1-02 v1).
"""

from __future__ import annotations

import threading
from typing import Any, Callable

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import (
    AgentMode,
    AgentTask,
    Delegation,
    DelegationResult,
    DelegationStatus,
)
from .errors import DelegationError

_TRANSITIONS: dict[DelegationStatus, set[DelegationStatus]] = {
    DelegationStatus.PENDING: {DelegationStatus.RUNNING, DelegationStatus.SKIPPED},
    DelegationStatus.RUNNING: {DelegationStatus.COMPLETED, DelegationStatus.FAILED},
    DelegationStatus.COMPLETED: set(),
    DelegationStatus.FAILED: set(),
    DelegationStatus.SKIPPED: set(),
}


class MultiAgentOrchestrator:
    """Delegation 4 modes — capability check + lifecycle + aggregation.

    ``agent_fn(task, context)`` injectable (C1-03 v1) — Worker qua Capability,
    orchestrator KHÔNG chạm agent registry trực tiếp.
    """

    def __init__(
        self,
        event_service: EventService | None = None,
        agent_fn: Callable[[AgentTask, dict], Any] | None = None,
    ) -> None:
        self._events = event_service
        self._agent_fn = agent_fn or (lambda _task, _ctx: None)
        self._lock = threading.RLock()

    # -- main ------------------------------------------------------------------

    def select_mode(self, tasks: list[AgentTask]) -> AgentMode:
        """Deterministic (C1-01 v1): SINGLE / PARALLEL / SEQUENTIAL / HIERARCHICAL."""
        if len(tasks) == 1:
            t = tasks[0]
            return AgentMode.HIERARCHICAL if t.hierarchical else AgentMode.SINGLE
        if any(t.depends_on for t in tasks):
            return AgentMode.SEQUENTIAL
        return AgentMode.PARALLEL

    def delegate(
        self,
        tasks: list[AgentTask],
        agents: list[dict],
        mode: AgentMode | None = None,
        owner: str = "autonomy",
    ) -> list[DelegationResult]:
        """Delegate tasks — chọn agent sorted theo id (C2-01 v2)."""
        with self._lock:
            if not tasks:
                return []
            mode = mode or self.select_mode(tasks)
            results: list[DelegationResult] = []
            context: dict[str, Any] = {}

            if mode == AgentMode.HIERARCHICAL:
                results.append(self._run_hierarchical(tasks[0], agents, owner))
            elif mode == AgentMode.SEQUENTIAL:
                results = self._run_sequential(tasks, agents, owner)
            else:  # SINGLE / PARALLEL — cùng thứ tự deterministic
                for task in tasks:
                    results.append(self._run_one(task, agents, owner, {}))
            return results

    # -- internals -------------------------------------------------------------

    def _run_one(
        self,
        task: AgentTask,
        agents: list[dict],
        owner: str,
        context: dict[str, Any],
    ) -> DelegationResult:
        agent = self._select_agent(task, agents)
        delegation = Delegation(task_id=task.id, agent_id=agent["id"], owner=owner)
        self._transition(delegation, DelegationStatus.RUNNING)
        self._emit(task.id, agent["id"], "running")
        try:
            result = self._agent_fn(task, context)
        except Exception as exc:
            self._transition(delegation, DelegationStatus.FAILED)
            self._emit(task.id, agent["id"], f"failed: {exc}")
            return DelegationResult(task_id=task.id, agent_id=agent["id"],
                                    status=DelegationStatus.FAILED, error=str(exc))
        self._transition(delegation, DelegationStatus.COMPLETED)
        self._emit(task.id, agent["id"], "completed")
        return DelegationResult(task_id=task.id, agent_id=agent["id"],
                                status=DelegationStatus.COMPLETED, result=result)

    def _run_sequential(
        self,
        tasks: list[AgentTask],
        agents: list[dict],
        owner: str,
    ) -> list[DelegationResult]:
        results: list[DelegationResult] = []
        by_id = {t.id: t for t in tasks}
        done: dict[str, Any] = {}
        skipped = False
        # topo-order đơn giản: task có depends_on phải chạy sau dependency
        order = _topo_order(tasks)
        for task_id in order:
            task = by_id[task_id]
            if skipped:
                results.append(DelegationResult(
                    task_id=task.id, status=DelegationStatus.SKIPPED,
                    error="previous task failed"))
                continue
            result = self._run_one(task, agents, owner, done)
            results.append(result)
            if result.status == DelegationStatus.COMPLETED:
                done[task.id] = result.result
            else:
                skipped = True  # C2-03 v2: fail-fast chain
        return results

    def _run_hierarchical(
        self,
        task: AgentTask,
        agents: list[dict],
        owner: str,
    ) -> DelegationResult:
        parent = self._run_one(task, agents, owner, {})
        if parent.status != DelegationStatus.COMPLETED or not task.subtasks:
            return parent
        sub_results: dict[str, Any] = {}
        for sub in task.subtasks:
            sub_result = self._run_one(sub, agents, owner, {})
            sub_results[sub.id] = sub_result.model_dump()
        parent.result = {task.id: sub_results}
        return parent

    def _select_agent(self, task: AgentTask, agents: list[dict]) -> dict:
        """Agent đầu tiên (sorted theo id) có đủ capability (C2-01 v2)."""
        needed = set(task.required_capabilities)
        if not needed:
            if not agents:
                raise DelegationError("không có agent nào để delegate")
            return sorted(agents, key=lambda a: str(a.get("id", "")))[0]
        for agent in sorted(agents, key=lambda a: str(a.get("id", ""))):
            caps = set(agent.get("capabilities", []))
            if needed.issubset(caps):
                return agent
        raise DelegationError(
            f"không agent nào có đủ capabilities: {sorted(needed)}"
        )

    @staticmethod
    def _transition(d: Delegation, target: DelegationStatus) -> None:
        if target not in _TRANSITIONS[d.status]:
            raise DelegationError(
                f"delegation transition không hợp lệ: {d.status.value} → {target.value}"
            )
        d.status = target

    def _emit(self, task_id: str, agent_id: str, note: str) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_DELEGATED,
            {"task_id": task_id, "agent_id": agent_id, "note": note},
            source="autonomous.multi_agent",
        )


def _topo_order(tasks: list[AgentTask]) -> list[str]:
    """Topo order đơn giản — dependency trước, deterministic (sorted)."""
    ids = {t.id for t in tasks}
    result: list[str] = []
    remaining = sorted(tasks, key=lambda t: t.id)
    while remaining:
        progress = False
        for task in remaining:
            deps = set(task.depends_on) & ids
            if deps.issubset(set(result)):
                result.append(task.id)
                remaining.remove(task)
                progress = True
                break
        if not progress:
            # cycle hoặc dependency thiếu — append phần còn lại (sorted)
            result.extend(t.id for t in remaining)
            break
    return result
