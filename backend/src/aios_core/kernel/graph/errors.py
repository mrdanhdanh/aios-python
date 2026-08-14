"""Execution graph errors (TASK-027)."""


class GraphError(Exception):
    """Base error for the execution graph layer."""


class GraphValidationError(GraphError):
    """Graph/runner/settings are invalid (INV-015 or contract violations)."""


class GraphExecutionError(GraphError):
    """Runtime failure inside the executor (e.g. wave cannot make progress)."""
