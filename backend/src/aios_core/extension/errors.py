"""Extension contract errors (TASK-045, M8-E3)."""


class ExtensionError(Exception):
    """Raised for extension contract misuse."""


class CompatibilityViolation(ExtensionError):
    """Raised when a plugin requirement cannot be satisfied."""
