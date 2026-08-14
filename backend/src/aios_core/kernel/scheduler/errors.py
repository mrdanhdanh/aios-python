"""Scheduler errors (TASK-028)."""


class SchedulerError(Exception):
    """Base error for the scheduler layer."""


class ResourceUnavailableError(SchedulerError):
    """Acquire timed out — reason carries node id + wait time."""


class ExecutionNodeError(SchedulerError):
    """ExecutionServiceRunner: node execution failed — reason from ExecutionResult."""
