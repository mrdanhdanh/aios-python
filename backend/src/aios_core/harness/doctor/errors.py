"""Doctor & Readiness errors (TASK-034, H5)."""


class DoctorError(Exception):
    """Doctor harness failure."""


class ReadinessError(DoctorError):
    """Readiness blocked — RELEASE BLOCKED (hard gate)."""
