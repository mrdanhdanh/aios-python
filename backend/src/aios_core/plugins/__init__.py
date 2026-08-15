"""AIOS Plugin Runtime (M8 — TASK-044).

Public API:
    from aios_core.plugins import PluginManager, PluginRegistry, PluginType, PluginManifest

Lifecycle (10 states) is REUSED from the Skills Manager state machine
(``SkillState`` + ``assert_transition``) — this package never defines a second
lifecycle machine (PLAN §M8-E2).
"""

from __future__ import annotations

from .compat import check_compatibility, parse_constraint
from .contracts import (
    AiosRange,
    Plugin,
    PluginManifest,
    PluginState,
    PluginType,
    ProvidedEntry,
)
from .errors import (
    PluginCompatibilityError,
    PluginDependencyError,
    PluginError,
    PluginStateError,
)
from .manager import PluginManager
from .registry import PluginRegistry

__all__ = [
    "AiosRange",
    "Plugin",
    "PluginManager",
    "PluginManifest",
    "PluginRegistry",
    "PluginState",
    "PluginType",
    "ProvidedEntry",
    "PluginCompatibilityError",
    "PluginDependencyError",
    "PluginError",
    "PluginStateError",
    "check_compatibility",
    "parse_constraint",
]
