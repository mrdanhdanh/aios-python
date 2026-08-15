"""Plugin errors (TASK-044, M8-E2)."""


class PluginError(Exception):
    """Raised for plugin lifecycle misuse (not found, already exists, broken dep)."""


class PluginStateError(PluginError):
    """Raised on invalid state transitions / missing history."""


class PluginCompatibilityError(PluginError):
    """Raised when a plugin manifest is incompatible with the running AIOS
    version (aios range check) or the manifest itself is malformed."""


class PluginDependencyError(PluginError):
    """Raised when a plugin dependency is missing, removed, or not compatible."""
