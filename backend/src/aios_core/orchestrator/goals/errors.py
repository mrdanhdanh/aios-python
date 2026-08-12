"""Errors for the goals / task-queue / permission-broker / recovery modules."""

from __future__ import annotations

from ..errors import OrchestratorError


class GoalError(OrchestratorError):
    """Raised on invalid goal/task operations (state machine violations, not found)."""


class QueueError(OrchestratorError):
    """Raised on invalid task-queue operations (bad transition, reorder misuse)."""
