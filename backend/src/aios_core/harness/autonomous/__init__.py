"""Autonomous module (M15, TASK-099..102): loop + trust budget + improvement."""

from .contracts import (
    AutonomyLevel, AutonomousReport, ImprovementCandidate,
    LoopAction, LoopState, TrustBudget,
)
from .engine import AutonomousEngine
from .errors import AutonomousError
from .harness import AutonomousHarness

__all__ = [
    "AutonomyLevel", "AutonomousReport", "ImprovementCandidate",
    "LoopAction", "LoopState", "TrustBudget",
    "AutonomousEngine", "AutonomousError", "AutonomousHarness",
]
