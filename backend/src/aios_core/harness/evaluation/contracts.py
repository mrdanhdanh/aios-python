"""Evaluation contracts (TASK-032, H4): suite, metric, score, trajectory."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class EvaluationKind(str, Enum):
    """Evaluation Model — LLM Judge KHÔNG mặc định (PLAN §H4)."""

    DETERMINISTIC = "deterministic"
    SEMANTIC = "semantic"
    LLM_JUDGE = "llm_judge"
    HUMAN = "human"
    COMPOSITE = "composite"


class Metric(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: EvaluationKind = EvaluationKind.DETERMINISTIC
    params: dict = {}
    weight: float = 1.0


class Suite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    dataset: str = ""
    metrics: list[Metric] = []
    thresholds: dict[str, float] = {}

    @field_validator("thresholds")
    @classmethod
    def _thresholds_non_negative(cls, value: dict[str, float]) -> dict[str, float]:
        for name, threshold in value.items():
            if threshold < 0:
                raise ValueError(f"threshold must be >= 0: {name}")
        return value


class TrajectoryStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: str  # "decision" | "tool" | "recovery" | "output"
    tool: str | None = None
    ok: bool | None = None
    denied: bool = False
    note: str = ""


class Trajectory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    steps: list[TrajectoryStep] = []
    final_correct: bool | None = None
    warning: bool = False
    marks: dict[str, bool] = {}


class EvaluationItem(BaseModel):
    """Dataset item — trajectory optional; score cho LLM/Human (P2-02)."""

    model_config = ConfigDict(extra="forbid")

    input: str
    output: str
    expected: str
    trajectory: list[TrajectoryStep] = []
    score: float | None = None


class Score(BaseModel):
    """Aggregate mean per metric (C1-02); None value = inconclusive."""

    model_config = ConfigDict(extra="forbid")

    metric: str
    value: float | None = None
    threshold: float
    passed: bool = False
    kind: EvaluationKind = EvaluationKind.DETERMINISTIC


class EvaluationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suite_id: str
    dataset: str = ""
    scores: list[Score] = []
    passed_all: bool = False
    status: EvaluationStatus = EvaluationStatus.FAILED
    trajectory: Trajectory | None = None  # item đầu có steps (P1-01)
    summary: str = ""
    metrics: dict = {}  # counts — deterministic (P2-03)
    reproducible: dict = {}  # INV-020: LLM_JUDGE only (C3-03)
