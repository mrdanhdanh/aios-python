"""Context optimizer (M5 TASK-024): priority-ordered, budgeted context."""

from .contracts import (
    CompressionReport,
    ContextSection,
    FinalContext,
    PriorityTier,
    TierBudgetReport,
)
from .optimizer import (
    ContentCompressor,
    ContextOptimizer,
    ContextOptimizerConfig,
    extractive_compress,
    level1_compress,
)

__all__ = [
    "CompressionReport",
    "ContentCompressor",
    "ContextOptimizer",
    "ContextOptimizerConfig",
    "ContextSection",
    "FinalContext",
    "PriorityTier",
    "TierBudgetReport",
    "extractive_compress",
    "level1_compress",
]
