"""Upgrade pipeline errors (TASK-020)."""


class UpgradeError(Exception):
    """Raised for upgrade pipeline misuse (component not found, migrate/rollback failure)."""
