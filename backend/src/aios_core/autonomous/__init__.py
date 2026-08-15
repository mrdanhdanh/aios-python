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
    AutonomousVerdict,
    Checkpoint,
    EvaluationConfig,
    EvaluationDimensions,
    ExecutionSession,
    Experiment,
    ExperimentVerdict,
    FailureEvent,
    GoalConstraints,
    GoalContract,
    GoalLifecycleState,
    GovernorDecision,
    Hypothesis,
    Lesson,
    LoopFinalState,
    LoopResult,
    MemoryEntry,
    MemoryEntryKind,
    PlanStep,
    ProgressEstimate,
    RecoveryOutcome,
    RecoveryStrategy,
    RiskClass,
    RollbackSpec,
    SessionStatus,
    STRATEGY_SCORES,
    StuckReport,
    StuckSignal,
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
from .evaluation import AutonomousEvaluator, ProgressEstimator
from .experimentation import ExperimentationEngine, new_experiment_id
from .goal import AutonomousGoalEngine, new_goal_id
from .governor import AutonomyGovernor
from .long_horizon import LongHorizonManager, new_session_id
from .loop import AutonomousLoop
from .memory import AutonomousMemory
from .planner import ACTION_KEYWORDS, AutonomousPlanner
from .recovery import AutonomousRecovery, CircuitBreaker, fingerprint_of
from .stuck import StuckDetector
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
        recovery: AutonomousRecovery | None = None,
        long_horizon: LongHorizonManager | None = None,
        autonomous_memory: AutonomousMemory | None = None,
        stuck_detector: StuckDetector | None = None,
        db_path: str = "aios/data/autonomous.db",
        event_service=None,
    ) -> None:
        self.goal_engine = goal_engine or AutonomousGoalEngine(
            event_service=event_service, db_path=db_path
        )
        self.governor = governor or AutonomyGovernor()
        self.planner = planner or AutonomousPlanner()
        self.world = world or WorldModel()
        self.loop = loop or AutonomousLoop(
            governor=self.governor,
            world=self.world,
            planner=self.planner,
        )
        self.recovery = recovery or AutonomousRecovery(event_service=event_service)
        self.long_horizon = long_horizon or LongHorizonManager(
            event_service=event_service, db_path=db_path
        )
        self.autonomous_memory = autonomous_memory or AutonomousMemory(
            event_service=event_service, db_path=db_path
        )
        self.stuck_detector = stuck_detector or StuckDetector()
        self.evaluator = AutonomousEvaluator(event_service=event_service)
        self.experimentation = None  # TASK-058: cần evaluate_fn (wiring cấp)
        self.multi_agent = None  # TASK-059 (Batch 4)
        self.scheduler = None  # TASK-062 (Batch 4)    def propose_goal(self, objective: str, **kwargs: object) -> GoalContract:
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
    "AutonomousVerdict",
    "Checkpoint",
    "EvaluationConfig",
    "EvaluationDimensions",
    "ExecutionSession",
    "Experiment",
    "ExperimentVerdict",
    "FailureEvent",
    "GoalConstraints",
    "GoalContract",
    "GoalLifecycleState",
    "GovernorDecision",
    "Hypothesis",
    "Lesson",
    "LoopFinalState",
    "LoopResult",
    "MemoryEntry",
    "MemoryEntryKind",
    "PlanStep",
    "ProgressEstimate",
    "RecoveryOutcome",
    "RecoveryStrategy",
    "RiskClass",
    "RollbackSpec",
    "SessionStatus",
    "STRATEGY_SCORES",
    "StuckReport",
    "StuckSignal",
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
    "AutonomousEvaluator",
    "AutonomousGoalEngine",
    "AutonomyGovernor",
    "AutonomousLoop",
    "AutonomousMemory",
    "AutonomousPlanner",
    "AutonomousRecovery",
    "CircuitBreaker",
    "ExperimentationEngine",
    "LongHorizonManager",
    "ProgressEstimator",
    "StuckDetector",
    "WorldModel",
    "AutonomyManager",
    "fingerprint_of",
    "new_experiment_id",
    "new_goal_id",
    "new_session_id",
]
