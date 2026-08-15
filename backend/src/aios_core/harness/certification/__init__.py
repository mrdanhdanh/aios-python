"""Certification Suite 1.0 — M10-F5 (TASK-073)."""

from .checks import AreaChecks
from .conformance import ConformanceRunner, format_conformance
from .contracts import (
    AreaResult,
    CertificationArea,
    ConformanceReport,
    GoldenScenario,
    PassFail,
)
from .golden import GOLDEN_SCENARIOS

__all__ = [
    "AreaChecks",
    "AreaResult",
    "CertificationArea",
    "ConformanceReport",
    "ConformanceRunner",
    "GOLDEN_SCENARIOS",
    "GoldenScenario",
    "PassFail",
    "format_conformance",
]
