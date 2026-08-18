"""Diagnose errors (M14-P0, TASK-094)."""

from ..errors import HarnessError


class DiagnoseError(HarnessError):
    """Diagnose harness error — corpus empty when failures exist (fail-closed)."""
