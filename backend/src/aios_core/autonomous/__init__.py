"""AIOS Autonomous package (M9 — P14).

Autonomy Layer định hướng Orchestrator (PLAN §M9-31/32):
``Autonomy → Orchestrator → Runtime`` — KHÔNG thay thế Control Plane.
13 task (TASK-050..062) nhóm thành các module; facade ``AutonomyManager``
compose tất cả với dependency injection — không God Object (INV-030..034
enforced bởi test_m9_* trong test_architecture.py).

Public API:
    from aios_core.autonomous import AutonomyManager, AutonomyGovernor, ...
"""

from __future__ import annotations

from .contracts import (
    AutonomyBudget,
    AutonomyDecision,
    AutonomyLevel,
    AutonomyPlan,
    GoalConstraints,
    GoalContract,
    GoalLifecycleState,
    GovernorDecision,
    LoopFinalState,
    LoopResult,
    PlanStep,
    RiskClass,
    RollbackSpec,
    UsageSnapshot,
    VerificationResult,
    WorldFact,
    WorldScope,
    WorldState,
)
from .errors import (
    AutonomousError,
    DelegationError,
    ExperimentError,
    GoalLifecycleError,
    GovernorError,
    LongHorizonError,
    MemoryPromotionError,
    PlanError,
    RecoveryError,
    ScheduleError,
    StuckError,
)
from .goal import AutonomousGoalEngine, new_goal_id
from .governor import AutonomyGovernor
from .loop import AutonomousLoop
from .planner import ACTION_KEYWORDS, AutonomousPlanner
from .world import WorldModel


class AutonomyManager:
    """Facade compose toàn bộ Autonomous Layer (M9).

    Constructed with injected dependencies; mặc định offline-first (in-memory/
    SQLite local) — usable và testable không cần external services.
    """

    def __init__(
        self,
        goal_engine: AutonomousGoalEngine | None = None,
        governor: AutonomyGovernor | None = None,
        planner: AutonomousPlanner | None = None,
        world: WorldModel | None = None,
        loop: AutonomousLoop | None = None,
    ) -> None:
        self.goal_engine = goal_engine or AutonomousGoalEngine(
            event_service=None, db_path="aios/data/autonomous.db"
        )
        self.governor = governor or AutonomyGovernor()
        self.planner = planner or AutonomousPlanner()
        self.world = world or WorldModel()
        self.loop = loop or AutonomousLoop(
            governor=self.governor,
            world=self.world,
            planner=self.planner,
        )
        self.recovery = None  # TASK-055 (Batch 2)
        self.long_horizon = None  # TASK-056 (Batch 2)
        self.autonomous_memory = None  # TASK-057 (Batch 2)
        self.stuck_detector = None  # TASK-061 (Batch 2)
        self.experimentation = None  # TASK-058 (Batch 3)
        self.evaluator = None  # TASK-060 (Batch 3)
        self.multi_agent = None  # TASK-059 (Batch 4)
        self.scheduler = None  # TASK-062 (Batch 4)

    def propose_goal(self, objective: str, **kwargs: object) -> GoalContract:
        """Tiện ích: tạo + propose goal từ objective."""
        goal = GoalContract(id=new_goal_id(), objective=objective, **kwargs)
        return self.goal_engine.propose(goal)

    def run_goal(self, goal_id: str, capabilities: list[str] | None = None) -> LoopResult:
        goal = self.goal_engine.get(goal_id)
        if not self.goal_engine.get_state(goal_id).value in (
            GoalLifecycleState.EXECUTING.value,
            GoalLifecycleState.APPROVED.value,
        ):
            self.goal_engine.transition(goal_id, GoalLifecycleState.EXECUTING, "autonomy")
        return self.loop.run_goal(goal, capabilities=capabilities)


__all__ = [
    # contracts
    "AutonomyBudget",
    "AutonomyDecision",
    "AutonomyLevel",
    "AutonomyPlan",
    "GoalConstraints",
    "GoalContract",
    "GoalLifecycleState",
    "GovernorDecision",
    "LoopFinalState",
    "LoopResult",
    "PlanStep",
    "RiskClass",
    "RollbackSpec",
    "UsageSnapshot",
    "VerificationResult",
    "WorldFact",
    "WorldScope",
    "WorldState",
    # errors
    "AutonomousError",
    "DelegationError",
    "ExperimentError",
    "GoalLifecycleError",
    "GovernorError",
    "LongHorizonError",
    "MemoryPromotionError",
    "PlanError",
    "RecoveryError",
    "ScheduleError",
    "StuckError",
    # modules
    "ACTION_KEYWORDS",
    "AutonomousGoalEngine",
    "AutonomyGovernor",
    "AutonomousLoop",
    "AutonomousPlanner",
    "WorldModel",
    "AutonomyManager",
    "new_goal_id",
]
