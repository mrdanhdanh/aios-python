"""Autonomous Loop (TASK-053 — M9-P1).

Trái tim M9 (PLAN §M9-10): ``Observe ↓ Understand ↓ Decide ↓ Plan ↓ Policy ↓
Act ↓ Verify ↓ Learn (→ Observe)``. Loop KHÔNG ``while True: agent.run()`` —
mọi hành động đi qua **Autonomy Governor** (INV-030) và bounded bởi budget
(INV-031). 8 bước đều injectable — offline-first deterministic mặc định,
KHÔNG LLM. Loop không chạm Tool trực tiếp (act qua Orchestrator — wiring).
"""

from __future__ import annotations

from typing import Any, Callable

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import (
    AutonomyDecision,
    AutonomyPlan,
    GovernorDecision,
    GoalContract,
    LoopFinalState,
    LoopResult,
    RiskClass,
    UsageSnapshot,
    VerificationResult,
)
from .errors import AutonomousError
from .governor import AutonomyGovernor
from .planner import AutonomousPlanner
from .world import WorldModel

# Mặc định policy check: allow hết (policy thật qua Orchestrator — wiring).
_DEFAULT_POLICY: Callable[[str, RiskClass], bool] = lambda _action, _risk: True


class AutonomousLoop:
    """Vòng lặp autonomous — governor-gated, bounded, observable.

    Mỗi vòng emit event ``autonomy.loop_step`` (C1-04 v1). Loop dừng sớm khi
    verify success hoặc goal success_achieved (AC9).
    """

    def __init__(
        self,
        governor: AutonomyGovernor,
        world: WorldModel,
        planner: AutonomousPlanner | None = None,
        max_iterations: int = 100,
        event_service: EventService | None = None,
        observer: Callable[[], Any] | None = None,
        understander: Callable[[Any, GoalContract], dict[str, Any]] | None = None,
        policy_check: Callable[[str, RiskClass], bool] | None = None,
        actor: Callable[[AutonomyPlan, GoalContract, Any], UsageSnapshot] | None = None,
        verifier: Callable[[Any, GoalContract], VerificationResult] | None = None,
        learner: Callable[[VerificationResult, GoalContract], None] | None = None,
    ) -> None:
        self._governor = governor
        self._world = world
        self._planner = planner or AutonomousPlanner()
        self._max_iterations = max_iterations
        self._events = event_service
        self._observer = observer or (lambda: world.snapshot())
        self._understander = understander or self._default_understand
        self._policy = policy_check or _DEFAULT_POLICY
        self._actor = actor or (lambda _plan, _goal, _ctx: UsageSnapshot())
        self._verifier = verifier or (
            lambda _ctx, _goal: VerificationResult(success=True, score=1.0)
        )
        self._learner = learner or (lambda _result, _goal: None)

    # -- main ------------------------------------------------------------------

    def run_goal(
        self,
        goal: GoalContract,
        capabilities: list[str] | None = None,
        step_risk: RiskClass = RiskClass.EDIT,
    ) -> LoopResult:
        """Chạy loop cho 1 goal. Governor STOP → không Act (INV-030)."""
        self._governor.start_goal(goal.id)
        result = LoopResult(goal_id=goal.id)
        plan: AutonomyPlan | None = None
        ctx: Any = None
        caps = list(capabilities) if capabilities else ["python"]  # offline default

        try:
            for iteration in range(1, self._max_iterations + 1):
                # 1. Observe
                ctx = self._observer()
                # 2. Understand
                analysis = self._understander(ctx, goal)
                # 3. Decide (governor — 1 lần/vòng, C2-01 v2)
                decision = self._governor.check_action(goal.id, step_risk)
                result.decisions.append(decision)
                self._emit_step(goal.id, iteration, decision, plan.steps[0].id if plan and plan.steps else "")

                if decision.decision in (AutonomyDecision.STOP, AutonomyDecision.ASK_HUMAN):
                    result.final_state = (
                        LoopFinalState.AWAITING_HUMAN
                        if decision.decision == AutonomyDecision.ASK_HUMAN
                        else LoopFinalState.STOPPED
                    )
                    result.iterations = iteration - 1
                    return result
                if decision.decision == AutonomyDecision.PAUSE:
                    result.final_state = LoopFinalState.STOPPED
                    result.iterations = iteration - 1
                    return result
                if decision.decision == AutonomyDecision.ROLLBACK:
                    result.final_state = LoopFinalState.STOPPED
                    result.iterations = iteration - 1
                    return result

                # 4. Plan (chỉ khi chưa có plan hoặc REPLAN — C2-03 v2)
                if plan is None or decision.decision == AutonomyDecision.REPLAN:
                    plan = self._planner.plan(goal, world=self._world, capabilities=caps)

                # 5. Policy (trước Act — AC3)
                if plan.steps:
                    step = plan.steps[0]
                    if not self._policy(step.capability, step_risk):
                        decision = GovernorDecision(
                            decision=AutonomyDecision.STOP,
                            reason=f"policy denied {step.capability}",
                        )
                        result.decisions.append(decision)
                        result.final_state = LoopFinalState.STOPPED
                        result.iterations = iteration
                        return result

                # 6. Act (chỉ khi CONTINUE — C2-01 v2)
                usage = self._actor(plan, goal, ctx) if plan else UsageSnapshot()
                self._governor.apply_usage(goal.id, usage)

                # 7. Verify
                verdict = self._verifier(ctx, goal)

                # 8. Learn (luôn chạy — C2-04 v2)
                self._learner(verdict, goal)

                result.iterations = iteration
                if verdict.success or self._world_changed_success(goal):
                    result.final_state = LoopFinalState.COMPLETED
                    result.success = True
                    break
            else:
                result.final_state = LoopFinalState.BUDGET_EXCEEDED
        except AutonomousError as exc:
            result.final_state = LoopFinalState.ERROR
            result.decisions.append(
                GovernorDecision(decision=AutonomyDecision.STOP, reason=str(exc))
            )
        finally:
            self._governor.end_goal(goal.id)
        return result

    # -- internals -------------------------------------------------------------

    @staticmethod
    def _default_understand(ctx: Any, goal: GoalContract) -> dict[str, Any]:
        """Deterministic mặc định (C2-02 v2): đếm fact từ world snapshot."""
        if isinstance(ctx, dict):
            return {"fact_count": len(ctx.get("history", {})), "changed": bool(ctx.get("history"))}
        return {"fact_count": 0, "changed": False}

    def _world_changed_success(self, goal: GoalContract) -> bool:
        try:
            return goal.progress() >= 1.0
        except Exception:
            return False

    def _emit_step(
        self,
        goal_id: str,
        iteration: int,
        decision: GovernorDecision,
        step_id: str,
    ) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_LOOP_STEP,
            {
                "goal_id": goal_id,
                "iteration": iteration,
                "decision": decision.decision.value,
                "reason": decision.reason,
                "step_id": step_id,
            },
            source="autonomous.loop",
        )
