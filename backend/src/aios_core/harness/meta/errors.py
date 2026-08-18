"""Meta-Harness errors (M13-P2, TASK-091)."""

from __future__ import annotations

from ..errors import HarnessError


class MetaError(HarnessError):
    """Raised when Meta status != PASS under strict mode (fail-closed INV-035)."""
