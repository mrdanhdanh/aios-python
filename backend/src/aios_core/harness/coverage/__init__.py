"""Harness Coverage package (M13-P1, TASK-090).

Coverage model 9 chiều + negative-path 8 + Harness Readiness 7 dims.
Fail-closed: v1 báo NOT_READY cho tới khi TASK-091 cover đủ negative-path.
"""

from .contracts import (
    CoverageDimension,
    CoverageItem,
    DimensionCoverage,
    HarnessCoverageReport,
    HarnessReadinessReport,
    HarnessReadinessStatus,
    NegativePath,
    NegativePathCoverage,
)
from .coverage import HarnessCoverage
from .errors import CoverageError
from .harness import CoverageHarness
from .readiness import HarnessReadinessScorer

__all__ = [
    "CoverageDimension",
    "CoverageItem",
    "DimensionCoverage",
    "HarnessCoverageReport",
    "HarnessReadinessReport",
    "HarnessReadinessStatus",
    "NegativePath",
    "NegativePathCoverage",
    "HarnessCoverage",
    "CoverageError",
    "CoverageHarness",
    "HarnessReadinessScorer",
]