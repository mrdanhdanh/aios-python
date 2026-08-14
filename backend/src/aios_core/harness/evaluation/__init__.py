"""Evaluation package (TASK-032, H4)."""

from .contracts import (
    EvaluationItem, EvaluationKind, EvaluationResult, EvaluationStatus,
    Metric, Score, Suite, Trajectory, TrajectoryStep,
)
from .errors import EvaluationError, SuiteError
from .evaluators import (
    CompositeEvaluator, DeterministicEvaluator, Engine, HumanEvaluator,
    LLMJudgeEvaluator, SemanticEvaluator,
)
from .suites import load, load_many
from .trajectory import TrajectoryEvaluator
from .evaluation import EvaluationHarness

__all__ = [
    "EvaluationItem", "EvaluationKind", "EvaluationResult", "EvaluationStatus",
    "Metric", "Score", "Suite", "Trajectory", "TrajectoryStep",
    "EvaluationError", "SuiteError",
    "CompositeEvaluator", "DeterministicEvaluator", "Engine", "HumanEvaluator",
    "LLMJudgeEvaluator", "SemanticEvaluator",
    "load", "load_many", "TrajectoryEvaluator", "EvaluationHarness",
]
