"""Heal errors (M14-P1, TASK-095)."""

from ..errors import HarnessError


class HealError(HarnessError):
    """Heal harness error."""
