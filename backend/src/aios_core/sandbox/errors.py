"""Sandbox pool errors (TASK-015)."""


class SandboxPoolError(Exception):
    """Raised on pool misuse (full, invalid language, double release)."""
