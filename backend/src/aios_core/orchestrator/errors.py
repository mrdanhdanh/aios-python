"""Orchestrator errors."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # planning.contracts imports kernel.execution_plan only
    from .planning.contracts import PlanValidationReport


class OrchestratorError(Exception):
    """Raised for orchestrator misuse."""


class PlanningError(OrchestratorError):
    """Raised by the Planning Engine (TASK-026) for invalid plans or failures.

    Carries the validation report so enforcement tests can assert issues
    (e.g. a cycle). Import is deferred (TYPE_CHECKING) to keep the errors
    module import-light (allow-list friendly).
    """

    def __init__(self, message: str, report: "PlanValidationReport | None" = None) -> None:
        super().__init__(message)
        self._report = report

    @property
    def report(self) -> "PlanValidationReport | None":
        return self._report
