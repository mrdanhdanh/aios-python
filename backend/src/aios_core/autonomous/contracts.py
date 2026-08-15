"""Autonomous layer contracts (M9 — P14).

Pure data contracts — extra=forbid, no aios_core imports (leaf module).
Autonomy Layer sits ABOVE the Orchestrator (PLAN §M9-31/32):
``Autonomy → Orchestrator → Runtime``. These contracts are shared by all 13
M9 tasks (TASK-050..062).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AutonomyLevel(str, Enum):
    """Năm cấp độ autonomy (PLAN §M9-3) — năng lực hệ thống."""

    A0_REACTIVE = "A0"
    A1_TASK = "A1"
    A2_GOAL = "A2"
    A3_LONG_HORIZON = "A3"
    A4_SELF_IMPROVING = "A4"


# ---------------------------------------------------------------------------
# TASK-050 — Autonomous Goal Engine
# ---------------------------------------------------------------------------

class GoalLifecycleState(str, Enum):
    """13 trạng thái lifecycle (PLAN §M9-5)."""

    PROPOSED = "proposed"
    VALIDATING = "validating"
    APPROVED = "approved"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    RECOVERY = "recovery"
    REPLANNING = "replanning"
    ESCALATED = "escalated"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GoalConstraints(BaseModel):
    """Giới hạn của goal (PLAN §M9-4)."""

    model_config = ConfigDict(extra="forbid")

    max_cost: float = 100.0
    max_duration_s: float = 604800.0  # 7 ngày


class GoalContract(BaseModel):
    """Goal contract đầy đủ (PLAN §M9-4)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    objective: str
    description: str = ""
    success: dict[str, float] = Field(default_factory=dict)  # metric → min_value
    constraints: GoalConstraints = Field(default_factory=GoalConstraints)
    permissions: list[str] = Field(default_factory=list)
    autonomy: AutonomyLevel = AutonomyLevel.A2_GOAL
    steps: list[str] = Field(default_factory=list)  # C1-03: kế hoạch bước
    completed_steps: list[str] = Field(default_factory=list)

    def progress(self) -> float:
        """progress = completed / total, clamp [0, 1] (C2-01)."""
        if not self.steps:
            return 0.0
        return min(1.0, max(0.0, len(self.completed_steps) / len(self.steps)))


# Transition map: source -> allowed targets.
_GOAL_TRANSITIONS: dict[GoalLifecycleState, set[GoalLifecycleState]] = {
    GoalLifecycleState.PROPOSED: {GoalLifecycleState.VALIDATING, GoalLifecycleState.CANCELLED},
    GoalLifecycleState.VALIDATING: {GoalLifecycleState.APPROVED, GoalLifecycleState.FAILED, GoalLifecycleState.CANCELLED},
    GoalLifecycleState.APPROVED: {GoalLifecycleState.PLANNING, GoalLifecycleState.CANCELLED},
    GoalLifecycleState.PLANNING: {GoalLifecycleState.EXECUTING, GoalLifecycleState.BLOCKED, GoalLifecycleState.CANCELLED},
    GoalLifecycleState.EXECUTING: {
        GoalLifecycleState.EVALUATING,
        GoalLifecycleState.BLOCKED,
        GoalLifecycleState.ESCALATED,
        GoalLifecycleState.FAILED,
        GoalLifecycleState.CANCELLED,
    },
    GoalLifecycleState.EVALUATING: {
        GoalLifecycleState.COMPLETED,
        GoalLifecycleState.EXECUTING,  # chưa đạt success → tiếp tục
        GoalLifecycleState.FAILED,
    },
    GoalLifecycleState.BLOCKED: {
        GoalLifecycleState.RECOVERY,
        GoalLifecycleState.ESCALATED,
        GoalLifecycleState.CANCELLED,
    },
    GoalLifecycleState.RECOVERY: {
        GoalLifecycleState.REPLANNING,
        GoalLifecycleState.EXECUTING,  # recovery thành công không cần replan
        GoalLifecycleState.ESCALATED,
        GoalLifecycleState.FAILED,
    },
    GoalLifecycleState.REPLANNING: {
        GoalLifecycleState.EXECUTING,
        GoalLifecycleState.BLOCKED,
        GoalLifecycleState.FAILED,
        GoalLifecycleState.CANCELLED,
    },
    GoalLifecycleState.COMPLETED: set(),
    GoalLifecycleState.ESCALATED: set(),  # terminal v1 (C1-04)
    GoalLifecycleState.FAILED: set(),
    GoalLifecycleState.CANCELLED: set(),
}


# ---------------------------------------------------------------------------
# TASK-051 — Autonomous Planner
# ---------------------------------------------------------------------------

class PlanStep(BaseModel):
    """Một bước trong AutonomyPlan."""

    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    capability: str
    dependencies: list[str] = Field(default_factory=list)
    estimated_duration_s: float = 60.0
    completed: bool = False


class RollbackSpec(BaseModel):
    """Rollback của plan (PLAN §M9-6)."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    strategy: str = ""  # VD: "restore_snapshot", "reverse_patch", ""


class AutonomyPlan(BaseModel):
    """Plan từ AutonomousPlanner (PLAN §M9-6)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    goal_id: str
    assumptions: list[str] = Field(default_factory=list)
    steps: list[PlanStep] = Field(default_factory=list)
    success_conditions: list[str] = Field(default_factory=list)
    rollback: RollbackSpec = Field(default_factory=RollbackSpec)
    reasons: list[str] = Field(default_factory=list)  # replan history
    over_budget: bool = False
    created_at: str = ""


# ---------------------------------------------------------------------------
# TASK-052 — World Model
# ---------------------------------------------------------------------------

class WorldScope(str, Enum):
    """7 nhóm World State (PLAN §M9-8)."""

    SYSTEM = "system"
    RUNTIME = "runtime"
    GOALS = "goals"
    TASKS = "tasks"
    ENVIRONMENT = "environment"
    CONSTRAINTS = "constraints"
    HISTORY = "history"


class WorldFact(BaseModel):
    """Một fact với source/timestamp/confidence/freshness (PLAN §M9-9)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    value: Any
    source: str
    observed_at: float  # epoch seconds (C2-01)
    confidence: float = 1.0  # 0..1 raw


class WorldState(BaseModel):
    """Snapshot World State (PLAN §M9-8)."""

    model_config = ConfigDict(extra="forbid")

    system: dict[str, Any] = Field(default_factory=dict)
    runtime: dict[str, Any] = Field(default_factory=dict)
    goals: dict[str, Any] = Field(default_factory=dict)
    tasks: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)  # C2-03 flat
    history: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# TASK-054 — Autonomy Governor
# ---------------------------------------------------------------------------

class AutonomyDecision(str, Enum):
    """6 quyết định của Governor (PLAN §M9-11)."""

    CONTINUE = "continue"
    PAUSE = "pause"
    ASK_HUMAN = "ask_human"
    REPLAN = "replan"
    ROLLBACK = "rollback"
    STOP = "stop"


class RiskClass(str, Enum):
    """5 cấp risk (C1-02 v1)."""

    READ = "read"
    EDIT = "edit"
    COMMIT = "commit"
    DEPLOY = "deploy"
    DELETE = "delete"


class AutonomyBudget(BaseModel):
    """Autonomy Budget (PLAN §M9-13)."""

    model_config = ConfigDict(extra="forbid")

    max_steps: int = 100
    max_llm_calls: int = 50
    max_cost: float = 10.0
    max_duration_s: float = 7200.0
    max_tool_calls: int = 200
    max_retries: int = 5
    max_parallel_agents: int = 4


class UsageSnapshot(BaseModel):
    """Usage cộng dồn cho budget check (C2-02 v2)."""

    model_config = ConfigDict(extra="forbid")

    steps: int = 0
    llm_calls: int = 0
    cost: float = 0.0
    duration_s: float = 0.0
    tool_calls: int = 0
    retries: int = 0
    parallel_agents: int = 0


class GovernorDecision(BaseModel):
    """Kết quả check_action — decision + reason (C1-05)."""

    model_config = ConfigDict(extra="forbid")

    decision: AutonomyDecision
    reason: str = ""


# Risk table mặc định (C1-04/C2-03 v2): RiskClass → policy level.
# "autonomous" = tự chạy; "approval" = cần human; "impossible" = không bao giờ.
DEFAULT_RISK_TABLE: dict[RiskClass, str] = {
    RiskClass.READ: "autonomous",
    RiskClass.EDIT: "autonomous",
    RiskClass.COMMIT: "approval",
    RiskClass.DEPLOY: "approval",
    RiskClass.DELETE: "impossible",
}


# ---------------------------------------------------------------------------
# TASK-053 — Autonomous Loop
# ---------------------------------------------------------------------------

class LoopFinalState(str, Enum):
    """Trạng thái cuối của loop (C1-05 v1)."""

    COMPLETED = "completed"
    STOPPED = "stopped"
    AWAITING_HUMAN = "awaiting_human"
    ERROR = "error"
    BUDGET_EXCEEDED = "budget_exceeded"


class VerificationResult(BaseModel):
    """Kết quả verify (C1-01 v1)."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    evidence: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0


class LoopResult(BaseModel):
    """Kết quả run_goal."""

    model_config = ConfigDict(extra="forbid")

    goal_id: str
    iterations: int = 0
    decisions: list[GovernorDecision] = Field(default_factory=list)
    final_state: LoopFinalState = LoopFinalState.STOPPED
    success: bool = False


# ---------------------------------------------------------------------------
# TASK-055 — Autonomous Recovery
# ---------------------------------------------------------------------------

class FailureEvent(BaseModel):
    """Một failure cần recovery (PLAN §M9-15)."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str
    error_type: str
    message: str
    at: float = 0.0


class RecoveryStrategy(str, Enum):
    """Các chiến lược deterministic (C1-02 v1)."""

    RETRY = "retry"
    FALLBACK = "fallback"
    ALTERNATIVE = "alternative"
    ESCALATE = "escalate"


# Score deterministic: RETRY > FALLBACK > ALTERNATIVE > ESCALATE.
STRATEGY_SCORES: dict[RecoveryStrategy, float] = {
    RecoveryStrategy.RETRY: 1.0,
    RecoveryStrategy.FALLBACK: 0.7,
    RecoveryStrategy.ALTERNATIVE: 0.5,
    RecoveryStrategy.ESCALATE: 0.0,
}


class RecoveryOutcome(BaseModel):
    """Kết quả recover() (C1-04 v1: escalate là outcome hợp lệ, không raise)."""

    model_config = ConfigDict(extra="forbid")

    recovered: bool = False
    escalated: bool = False
    strategy: RecoveryStrategy | None = None
    attempts: int = 0
    reason: str = ""


# ---------------------------------------------------------------------------
# TASK-056 — Long-Horizon Execution
# ---------------------------------------------------------------------------

class SessionStatus(str, Enum):
    """Trạng thái session (C1-04 v1)."""

    ACTIVE = "active"
    RESUMED = "resumed"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionSession(BaseModel):
    """Session dài hạn (PLAN §M9-17)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    goal_id: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: str = ""


class Checkpoint(BaseModel):
    """Checkpoint: Completed · Current · Pending · State (PLAN §M9-18)."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    completed: list[str] = Field(default_factory=list)
    current: str = ""  # C2-02: mặc định "" (chưa bắt đầu)
    pending: list[str] = Field(default_factory=list)
    state: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    at: str = ""


# ---------------------------------------------------------------------------
# TASK-057 — Autonomous Memory
# ---------------------------------------------------------------------------

class MemoryEntryKind(str, Enum):
    """6 loại memory (PLAN §M9-19)."""

    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    FAILURE = "failure"
    GOAL = "goal"


class MemoryEntry(BaseModel):
    """Một entry memory autonomous."""

    model_config = ConfigDict(extra="forbid")

    kind: MemoryEntryKind
    key: str
    content: dict[str, Any]
    confidence: float = 0.0
    validated: bool = False
    promoted: bool = False
    source: str = ""
    created_at: str = ""


class Lesson(BaseModel):
    """Lesson từ Learning Loop (PLAN §M9-20)."""

    model_config = ConfigDict(extra="forbid")

    key: str
    when: str
    failure: str
    cause: str = ""
    fix: str = ""
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# TASK-061 — Advanced Stuck Detection
# ---------------------------------------------------------------------------

class StuckSignal(str, Enum):
    """7 signal stuck (PLAN §M9-27)."""

    REPEATED_TOOL_CALLS = "repeated_tool_calls"
    REPEATED_ERRORS = "repeated_errors"
    NO_STATE_CHANGE = "no_state_change"
    NO_PROGRESS = "no_progress"
    OSCILLATION = "oscillation"
    BUDGET_BURN = "budget_burn"
    CONTRADICTORY_PLANS = "contradictory_plans"


class StuckReport(BaseModel):
    """Báo cáo detect()."""

    model_config = ConfigDict(extra="forbid")

    signals: list[str] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    verdict: str = "normal"  # "stuck" | "normal"
    window_size: int = 0


# ---------------------------------------------------------------------------
# TASK-058 — Autonomous Experimentation
# ---------------------------------------------------------------------------

class ExperimentVerdict(str, Enum):
    """Verdict experiment (PLAN §M9-21)."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class Hypothesis(BaseModel):
    """Giả thuyết cải thiện (PLAN §M9-21/§M9-33)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    statement: str
    baseline: float  # giá trị hiện tại
    target_metric: str
    target_value: float
    direction: str = "higher"  # "higher" | "lower" (C1-01 v1)


class Experiment(BaseModel):
    """Kết quả 1 experiment — evidence bắt buộc (INV-033)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    hypothesis_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    result: Any = None
    metric_value: float | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    verdict: ExperimentVerdict = ExperimentVerdict.INCONCLUSIVE
    deployed: bool = False
    canary: bool = False
    at: str = ""


# ---------------------------------------------------------------------------
# TASK-060 — Autonomous Evaluation
# ---------------------------------------------------------------------------

class AutonomousVerdict(str, Enum):
    """5 quyết định evaluation (PLAN §M9-25)."""

    CONTINUE = "continue"
    RETRY = "retry"
    REPLAN = "replan"
    STOP = "stop"
    ASK_HUMAN = "ask_human"


class EvaluationDimensions(BaseModel):
    """6 chiều đánh giá (PLAN §M9-25)."""

    model_config = ConfigDict(extra="forbid")

    correctness: float = 0.0
    quality: float = 0.0
    cost: float = 0.0  # tỷ lệ dùng/budget (C2-01 v2)
    risk: float = 0.0
    progress: float = 0.0
    confidence: float = 0.0
    trajectory_evidence: dict[str, Any] = Field(default_factory=dict)  # C1-02


class EvaluationConfig(BaseModel):
    """Thresholds injectable (C2-03 v2)."""

    model_config = ConfigDict(extra="forbid")

    correctness_min: float = 0.7
    risk_max: float = 0.8
    cost_max: float = 1.0
    stuck_iterations: int = 3


class ProgressEstimate(BaseModel):
    """Ước lượng tiến độ (PLAN §M9-26)."""

    model_config = ConfigDict(extra="forbid")

    completion: float = 0.0  # % hoàn thành
    confidence: float = 0.0
    risk: float = 0.0
    budget_remaining: float = 1.0
    progress_stuck: bool = False
    trajectory_warning: bool = False
