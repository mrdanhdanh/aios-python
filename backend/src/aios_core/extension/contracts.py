"""Extension contract models (TASK-045, M8-E3).

Four API namespaces (PLAN §M8-E3):
    Internal     — aios.core.internal.*        ❌ never public
    Public       — aios.sdk.*                  ✅ stable public API
    Extension    — aios.extension.*            ✅ stable extension API
    Experimental — aios.experimental.*         ⚠️ may change without notice
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ApiNamespace(str, Enum):
    INTERNAL = "internal"
    PUBLIC = "public"
    EXTENSION = "extension"
    EXPERIMENTAL = "experimental"


class ContractRequirement(BaseModel):
    """A single ``requires`` entry: contract id -> version constraint."""

    model_config = ConfigDict(extra="forbid")

    contract: str  # e.g. "capability_contract"
    constraint: str  # "^2.0" | ">=1.8" | "1.8.0" | "*" | "~1.9"


class ExtensionContract(BaseModel):
    """A public/extension contract declaration with its requirements."""

    model_config = ConfigDict(extra="forbid")

    id: str
    namespace: ApiNamespace
    version: str
    requires: list[ContractRequirement] = Field(default_factory=list)


class CompatibilityResult(BaseModel):
    """Outcome of a compatibility check (fail-closed on any error)."""

    model_config = ConfigDict(extra="forbid")

    ok: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


__all__ = [
    "ApiNamespace",
    "CompatibilityResult",
    "ContractRequirement",
    "ExtensionContract",
]
