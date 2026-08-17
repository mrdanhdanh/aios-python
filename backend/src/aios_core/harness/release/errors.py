"""Release Gate errors (M13-P3, TASK-092)."""

from ..errors import HarnessError


class ReleaseGateError(HarnessError):
    """Release gate fail-closed: status != PASS → raise (INV-035)."""
