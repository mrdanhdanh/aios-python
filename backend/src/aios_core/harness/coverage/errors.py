"""Harness Coverage errors (M13-P1, TASK-090)."""

from ..errors import HarnessError


class CoverageError(HarnessError):
    """Coverage/readiness config invalid hoặc verify fail-closed."""