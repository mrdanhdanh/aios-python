"""Harness errors (TASK-029, H1)."""


class HarnessError(Exception):
    """Base harness error."""


class HarnessRegistrationError(HarnessError):
    """Duplicate id or empty metadata."""


class HarnessNotFoundError(HarnessError):
    """get/require/execute on an unknown harness id."""


class HarnessLifecycleError(HarnessError):
    """Invalid state transition."""


class HarnessHookError(HarnessError):
    """A harness hook raised — message carries phase + root cause."""
