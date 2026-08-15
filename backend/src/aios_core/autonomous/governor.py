"""Autonomy Governor (TASK-054 — M9-P1).

Architecture invariant INV-030: **không autonomous action nào thực hiện ngoài
Governor**. Quyết định: CONTINUE · PAUSE · ASK_HUMAN · REPLAN · ROLLBACK ·
STOP. Enforce Autonomy Budget (INV-031): steps / llm_calls / cost / duration /
tool_calls / retries / parallel_agents. Risk Budget: read → autonomous,
edit → autonomous, commit → approval, push/deploy → approval, delete →
impossible.
"""

from __future__ import annotations

import threading
from typing import Callable

from .contracts import (
    AutonomyBudget,
    AutonomyDecision,
    GovernorDecision,
    RiskClass,
    UsageSnapshot,
)
from .errors import GovernorError

_DEFAULT_RISK_TABLE: dict[RiskClass, str] = {
    RiskClass.READ: "autonomous",
    RiskClass.EDIT: "autonomous",
    RiskClass.COMMIT: "approval",
    RiskClass.DEPLOY: "approval",
    RiskClass.DELETE: "impossible",
}

# Risk classes cần đếm parallel agents (C2-02 v2 — hành động thật).
_PARALLEL_COUNTED = {RiskClass.COMMIT, RiskClass.DEPLOY}


class _BudgetEntry:
    __slots__ = ("started_at", "steps", "llm_calls", "cost", "duration_s",
                 "tool_calls", "retries", "parallel_agents")

    def __init__(self, started_at: float) -> None:
        self.started_at = started_at
        self.steps = 0
        self.llm_calls = 0
        self.cost = 0.0
        self.duration_s = 0.0
        self.tool_calls = 0
        self.retries = 0
        self.parallel_agents = 0


class AutonomyGovernor:
    """Gate duy nhất cho autonomous action (INV-030) + budget enforce (INV-031).

    Budget entry lazy-init theo goal_id (C2-01 v2); ``end_goal`` xóa entry —
    check sau đó tạo entry fresh. Thread-safe (RLock).
    """

    def __init__(
        self,
        budget: AutonomyBudget | None = None,
        risk_table: dict[RiskClass, str] | None = None,
        clock: Callable[[], float] | None = None,
        world_changed: Callable[[], bool] | None = None,
    ) -> None:
        self._budget = budget or AutonomyBudget()
        self._risk = risk_table or dict(_DEFAULT_RISK_TABLE)
        self._clock = clock or _default_clock
        self._world_changed = world_changed or (lambda: False)  # C2-04 v2
        self._lock = threading.RLock()
        self._entries: dict[str, _BudgetEntry] = {}

    # -- lifecycle -------------------------------------------------------------

    def start_goal(self, goal_id: str) -> None:
        """Idempotent (C1-01 v1): không reset nếu entry đã tồn tại."""
        with self._lock:
            if goal_id not in self._entries:
                self._entries[goal_id] = _BudgetEntry(self._clock())

    def end_goal(self, goal_id: str) -> None:
        """Xóa entry (C2-01 v2) — check sau đó lazy-init fresh."""
        with self._lock:
            self._entries.pop(goal_id, None)

    def apply_usage(self, goal_id: str, delta: UsageSnapshot) -> None:
        """Loop cộng dồn usage sau mỗi Act (C2-02 v2)."""
        with self._lock:
            entry = self._entry(goal_id)
            entry.steps += delta.steps
            entry.llm_calls += delta.llm_calls
            entry.cost += delta.cost
            entry.duration_s += delta.duration_s
            entry.tool_calls += delta.tool_calls
            entry.retries += delta.retries
            entry.parallel_agents += delta.parallel_agents

    # -- gate ------------------------------------------------------------------

    def check_action(
        self,
        goal_id: str,
        risk_class: RiskClass,
        usage: UsageSnapshot | None = None,
    ) -> GovernorDecision:
        """Quyết định cho action tiếp theo. Fail-closed (C1-01 v1 spec)."""
        with self._lock:
            entry = self._entry(goal_id)
            u = usage or UsageSnapshot()
            now = self._clock()
            duration = u.duration_s if u.duration_s > 0 else now - entry.started_at

            # Budget checks (thứ tự deterministic — review R2-2).
            # >= : đạt limit = cạn kiệt — không action nào tiếp (C1-05 v2).
            if entry.steps + u.steps >= self._budget.max_steps:
                return self._exceeded("budget.steps", entry.steps + u.steps, self._budget.max_steps)
            if entry.cost + u.cost >= self._budget.max_cost:
                return self._exceeded("budget.cost", round(entry.cost + u.cost, 4), self._budget.max_cost)
            if duration >= self._budget.max_duration_s:
                return self._exceeded("budget.duration", round(duration, 2), self._budget.max_duration_s)
            if entry.tool_calls + u.tool_calls >= self._budget.max_tool_calls:
                return self._exceeded("budget.tool_calls", entry.tool_calls + u.tool_calls, self._budget.max_tool_calls)
            if entry.llm_calls + u.llm_calls >= self._budget.max_llm_calls:
                return self._exceeded("budget.llm_calls", entry.llm_calls + u.llm_calls, self._budget.max_llm_calls)
            if entry.retries + u.retries >= self._budget.max_retries:
                return self._exceeded("budget.retries", entry.retries + u.retries, self._budget.max_retries)

            # Parallel agents (C1-02 v1/C2-02 v2) — TRƯỚC risk check: tài nguyên
            # đầy thì không cần hỏi quyền (PAUSE — có thể chờ).
            if (
                risk_class in _PARALLEL_COUNTED
                and entry.parallel_agents + u.parallel_agents >= self._budget.max_parallel_agents
            ):
                return self._exceeded(
                    "budget.parallel_agents",
                    entry.parallel_agents + u.parallel_agents,
                    self._budget.max_parallel_agents,
                    decision=AutonomyDecision.PAUSE,  # C1-03: PAUSE — có thể chờ
                )

            # Risk check.
            level = self._risk.get(risk_class, "approval")
            if level == "impossible":
                return GovernorDecision(
                    decision=AutonomyDecision.STOP,
                    reason=f"risk.{risk_class.value} is impossible",
                )
            if level == "approval":
                return GovernorDecision(
                    decision=AutonomyDecision.ASK_HUMAN,
                    reason=f"risk.{risk_class.value} requires approval",
                )

            # World change → REPLAN (C1-04 v1). Verify-fail loop tự gọi ROLLBACK
            # riêng qua recovery — governor chỉ báo khi world thay đổi.
            if self._world_changed():
                return GovernorDecision(
                    decision=AutonomyDecision.REPLAN,
                    reason="world changed",
                )

            return GovernorDecision(decision=AutonomyDecision.CONTINUE, reason="ok")

    def usage(self, goal_id: str) -> UsageSnapshot:
        """Usage hiện tại (test/observability)."""
        with self._lock:
            entry = self._entry(goal_id)
            return UsageSnapshot(
                steps=entry.steps,
                llm_calls=entry.llm_calls,
                cost=round(entry.cost, 4),
                duration_s=round(entry.duration_s or 0.0, 2),
                tool_calls=entry.tool_calls,
                retries=entry.retries,
                parallel_agents=entry.parallel_agents,
            )

    # -- internals -------------------------------------------------------------

    def _entry(self, goal_id: str) -> _BudgetEntry:
        entry = self._entries.get(goal_id)
        if entry is None:
            entry = _BudgetEntry(self._clock())
            self._entries[goal_id] = entry
        return entry

    @staticmethod
    def _exceeded(
        category: str,
        used: float | int,
        limit: float | int,
        decision: AutonomyDecision = AutonomyDecision.STOP,
    ) -> GovernorDecision:
        return GovernorDecision(
            decision=decision,
            reason=f"{category} exceeded (used {used}/{limit})",
        )


def _default_clock() -> float:
    import time

    return time.time()
