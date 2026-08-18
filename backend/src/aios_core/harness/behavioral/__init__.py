"""Behavioral Conformance package (M13-P0, TASK-089).

Chứng minh harness hành vi ổn định qua thời gian (temporal determinism),
dưới tải (load), chạy dài (soak) và phục hồi lỗi (failure recovery).
"""

from .contracts import (
    ConformanceConfig,
    ConformanceIterationSummary,
    ConformanceProfile,
    ConformanceReport,
    ConformanceStatus,
)
from .engine import PROFILE_ITERATIONS, BehavioralConformanceEngine
from .errors import BehavioralConformanceError
from .harness import BehavioralConformanceHarness

__all__ = [
    "ConformanceConfig",
    "ConformanceIterationSummary",
    "ConformanceProfile",
    "ConformanceReport",
    "ConformanceStatus",
    "PROFILE_ITERATIONS",
    "BehavioralConformanceEngine",
    "BehavioralConformanceError",
    "BehavioralConformanceHarness",
]