"""AIOS Extension Contracts (M8 — TASK-045).

Four API namespaces protect the Core from unstable third-party coupling:
Internal / Public / Extension / Experimental. The Compatibility Matrix is a
pure, fail-closed gate checked BEFORE a plugin loads.

Public API:
    from aios_core.extension import ApiNamespace, check_requires, parse_constraint
"""

from __future__ import annotations

from .contracts import ApiNamespace, CompatibilityResult, ContractRequirement, ExtensionContract
from .errors import CompatibilityViolation, ExtensionError
from .matrix import assert_namespace_allowed, check_requires, parse_constraint

__all__ = [
    "ApiNamespace",
    "CompatibilityResult",
    "CompatibilityViolation",
    "ContractRequirement",
    "ExtensionContract",
    "ExtensionError",
    "assert_namespace_allowed",
    "check_requires",
    "parse_constraint",
]
