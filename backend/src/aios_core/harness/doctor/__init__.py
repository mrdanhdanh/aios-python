"""Doctor & Readiness package (TASK-034, H5)."""

from .contracts import (
    DoctorKind, DoctorResult, DoctorStatus, HardGate, ReadinessReport,
)
from .errors import DoctorError, ReadinessError
from .checks import DoctorChecks
from .doctor import DoctorHarness
from .readiness import ReadinessHarness, ReadinessScorer

__all__ = [
    "DoctorKind", "DoctorResult", "DoctorStatus", "HardGate",
    "ReadinessReport",
    "DoctorError", "ReadinessError",
    "DoctorChecks", "DoctorHarness", "ReadinessHarness", "ReadinessScorer",
]
