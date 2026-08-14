"""Evaluation errors (TASK-032, H4)."""


class EvaluationError(Exception):
    """EvaluationHarness verification failure."""


class SuiteError(Exception):
    """Suite load/validate failure."""
