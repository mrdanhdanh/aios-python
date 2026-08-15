"""Autonomous Planner (TASK-051 — M9-P1).

``Goal → World State → Constraints → Available Capabilities → History → Plan``
(PLAN §M9-6). Deterministic v1 (offline-first — KHÔNG LLM mặc định):
keyword-based decomposition. Hỗ trợ Dynamic Replanning: plan không bất biến —
``replan()`` sinh plan mới từ world mới + lý do.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .contracts import (
    AutonomyPlan,
    GoalContract,
    PlanStep,
    RiskClass,
    RollbackSpec,
)
from .errors import PlanError

# Keyword → capabilities (C1-02 v1). Sorted deterministic.
ACTION_KEYWORDS: dict[str, list[str]] = {
    "analyze": ["python", "filesystem"],
    "deploy": ["docker"],
    "docs": ["filesystem"],
    "fix": ["python", "filesystem"],
    "review": ["filesystem"],
    "test": ["python"],
}

_DEFAULT_CAPABILITY = "python"  # C2-01: keyword không khớp → step mặc định

# RiskClass → policy level (dùng chung DEFAULT_RISK_TABLE trong contracts).
_ROLLBACK_FORBIDDEN = {RiskClass.DELETE}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutonomousPlanner:
    """Sinh plan deterministic từ goal + world + constraints + capabilities.

    V1: decomposition keyword-based; dependencies luôn [] (C1-03 v1); mỗi step
    có estimated_duration_s (60s mặc định) — tổng vượt max_duration → over_budget
    (C1-05 v1, KHÔNG raise).
    """

    def __init__(
        self,
        risk_table: dict[RiskClass, str] | None = None,
        clock: Any = None,
    ) -> None:
        from .contracts import DEFAULT_RISK_TABLE

        self._risk = risk_table or dict(DEFAULT_RISK_TABLE)
        self._clock = clock

    # -- plan ------------------------------------------------------------------

    def plan(
        self,
        goal: GoalContract,
        world: Any = None,  # WorldModel (duck-typed — không import)
        constraints: dict[str, Any] | None = None,
        capabilities: list[str] | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> AutonomyPlan:
        """Sinh plan từ goal. capabilities rỗng → raise (fail-closed, C1-01)."""
        if not goal.objective.strip():
            raise PlanError("objective rỗng — không plan được")
        caps = list(capabilities or [])
        if not caps:
            raise PlanError("capabilities rỗng — không plan được")

        steps = self._decompose(goal.objective, caps)
        total = sum(s.estimated_duration_s for s in steps)
        max_duration = goal.constraints.max_duration_s
        over_budget = total > max_duration

        return AutonomyPlan(
            id=f"plan-{goal.id}",
            goal_id=goal.id,
            assumptions=self._assumptions(world),
            steps=steps,
            success_conditions=[f"{m} >= {v}" for m, v in sorted(goal.success.items())],
            rollback=self._rollback(goal),
            reasons=[],
            over_budget=over_budget,
            created_at=_now_iso(),
        )

    def replan(
        self,
        goal: GoalContract,
        world: Any,
        plan: AutonomyPlan,
        reason: str,
        completed_step_ids: list[str] | None = None,
        capabilities: list[str] | None = None,
    ) -> AutonomyPlan:
        """Dynamic replanning (PLAN §M9-7): plan mới từ world mới + lý do.

        Steps đã hoàn thành được giữ nguyên (C2-03 v2).
        """
        done = set(completed_step_ids or [])
        new_plan = self.plan(
            goal,
            world=world,
            capabilities=capabilities or self._plan_capabilities(plan),
        )
        new_plan.reasons = [*plan.reasons, reason]
        for step in new_plan.steps:
            if step.id in done:
                step.completed = True
        return new_plan

    # -- decomposition ---------------------------------------------------------

    def _decompose(self, objective: str, caps: list[str]) -> list[PlanStep]:
        lower = objective.lower()
        steps: list[PlanStep] = []
        used: set[str] = set()
        for keyword in sorted(ACTION_KEYWORDS):
            if keyword in lower:
                wanted = [c for c in ACTION_KEYWORDS[keyword] if c in caps]
                if not wanted:
                    wanted = [caps[0]]  # C2-02: filter rỗng → capability đầu input
                step_id = f"{keyword}"
                if step_id not in used:
                    steps.append(
                        PlanStep(
                            id=step_id,
                            description=f"{keyword}: {objective}",
                            capability=wanted[0],
                        )
                    )
                    used.add(step_id)
        if not steps:
            # C2-01: keyword không khớp → step mặc định
            steps.append(
                PlanStep(
                    id="default",
                    description=objective,
                    capability=caps[0],
                )
            )
        return steps

    # -- helpers ---------------------------------------------------------------

    def _assumptions(self, world: Any) -> list[str]:
        if world is None:
            return ["world chưa được observe"]
        try:
            snapshot = world.snapshot()
            return [f"world facts: {len(snapshot.get('history', {}))} changes"]
        except Exception:
            return ["world snapshot không đọc được"]

    def _rollback(self, goal: GoalContract) -> RollbackSpec:
        for perm in goal.permissions:
            for rc, level in self._risk.items():
                if rc in _ROLLBACK_FORBIDDEN and level == "impossible":
                    return RollbackSpec(enabled=False, strategy="")
        # DELETE trong permissions → không rollback được
        if "delete" in [p.lower() for p in goal.permissions]:
            return RollbackSpec(enabled=False, strategy="")
        return RollbackSpec(enabled=True, strategy="restore_snapshot")

    @staticmethod
    def _plan_capabilities(plan: AutonomyPlan) -> list[str]:
        seen: list[str] = []
        for step in plan.steps:
            if step.capability not in seen:
                seen.append(step.capability)
        return seen
