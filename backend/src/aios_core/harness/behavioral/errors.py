"""Behavioral Conformance errors (M13-P0, TASK-089)."""

from ..errors import HarnessError


class BehavioralConformanceError(HarnessError):
    """Config invalid / fail-fast fault_iterations / verify fail-closed."""