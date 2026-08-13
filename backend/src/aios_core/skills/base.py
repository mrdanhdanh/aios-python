"""Skill state machine + manifest contract (TASK-015)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ..metadata import AiOSMetadata
from ..semver import parse_version
from .errors import SkillError, SkillStateError


class SkillState(str, Enum):
    RESOLVED = "resolved"
    VALIDATED = "validated"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    RELOADED = "reloaded"
    UPGRADED = "upgraded"
    ROLLED_BACK = "rolled_back"
    REMOVED = "removed"


class SkillSource(str, Enum):
    ZIP = "zip"
    GIT = "git"
    PIP = "pip"


_ALL_STATES = tuple(s.value for s in SkillState)
_ALL_SOURCES = tuple(s.value for s in SkillSource)

# Installed-ish states (dependency considered "installed").
_INSTALLED_STATES = {
    SkillState.INSTALLED,
    SkillState.ENABLED,
    SkillState.DISABLED,
    SkillState.UNLOADED,
    SkillState.RELOADED,
    SkillState.UPGRADED,
    SkillState.ROLLED_BACK,
}
_ACTIVE_STATES = {SkillState.ENABLED, SkillState.RELOADED}


class SkillManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str  # semver — validate bằng aios_core.semver (C1-04)
    source: SkillSource
    description: str = ""
    dependencies: list[str] = Field(default_factory=list)  # "id" hoặc "id@>=X.Y.Z"
    capabilities: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    metadata: AiOSMetadata | None = None

    @classmethod
    def _validate_fields(cls, values: dict) -> dict:
        if not values.get("id", "").strip():
            raise ValueError("id must not be empty")
        if not values.get("name", "").strip():
            raise ValueError("name must not be empty")
        version = values.get("version", "")
        try:
            parse_version(version)
        except ValueError:
            raise ValueError(f"invalid semver version: {version!r}") from None
        for dep in values.get("dependencies", []):
            if not dep or not dep.strip():
                raise ValueError("dependency must not be empty")
        for cap in values.get("capabilities", []):
            if not cap or not cap.strip():
                raise ValueError("capability must not be empty")
        for perm in values.get("permissions", []):
            if not perm or not perm.strip():
                raise ValueError("permission must not be empty")
        return values

    # pydantic v2 validator hook (called by SkillManifest(...) constructor).
    @classmethod
    def validate_manifest(cls, **kwargs) -> "SkillManifest":
        values = cls._validate_fields(kwargs)
        return cls(**values)


# Transition table: op -> {source states} -> target (C1-01 — T4/T5 đã sửa).
_TRANSITIONS: dict[str, dict[frozenset[SkillState], SkillState]] = {
    "validate": {frozenset({SkillState.RESOLVED}): SkillState.VALIDATED},
    "install": {frozenset({SkillState.VALIDATED}): SkillState.INSTALLED},
    "enable": {
        frozenset({SkillState.INSTALLED, SkillState.DISABLED, SkillState.UPGRADED, SkillState.ROLLED_BACK}): SkillState.ENABLED
    },
    "disable": {
        frozenset({SkillState.ENABLED, SkillState.RELOADED, SkillState.UPGRADED, SkillState.ROLLED_BACK}): SkillState.DISABLED
    },
    "unload": {
        frozenset({SkillState.ENABLED, SkillState.DISABLED, SkillState.RELOADED, SkillState.UPGRADED, SkillState.ROLLED_BACK}): SkillState.UNLOADED
    },
    "reload": {frozenset({SkillState.UNLOADED}): SkillState.RELOADED},
    "upgrade": {
        frozenset({
            SkillState.INSTALLED, SkillState.ENABLED, SkillState.DISABLED, SkillState.UNLOADED,
            SkillState.RELOADED, SkillState.UPGRADED, SkillState.ROLLED_BACK,
        }): SkillState.UPGRADED
    },
    "rollback": {
        frozenset({
            SkillState.ENABLED, SkillState.DISABLED, SkillState.UNLOADED,
            SkillState.RELOADED, SkillState.UPGRADED, SkillState.ROLLED_BACK,
        }): SkillState.ROLLED_BACK
    },
    "remove": {
        frozenset(set(SkillState) - {SkillState.REMOVED}): SkillState.REMOVED
    },
}

_OP_TARGET: dict[str, SkillState] = {op: target for op, mapping in _TRANSITIONS.items() for _, target in mapping.items()}


def assert_transition(current: SkillState, op: str) -> SkillState:
    """Return target state for op from current; raise SkillStateError if invalid."""
    if current == SkillState.REMOVED:
        raise SkillStateError("skill removed — terminal state")
    for sources, target in _TRANSITIONS.get(op, {}).items():
        if current in sources:
            return target
    raise SkillStateError(f"invalid transition: {current.value} -> {op}")


class Skill(BaseModel):
    """Read view of a skill record (matches skills table row)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str
    source: SkillSource
    state: SkillState
    manifest: dict = Field(default_factory=dict)
    history: list[dict] = Field(default_factory=list)
    installed_at: str | None = None
    created_at: str
    updated_at: str

    def is_active(self) -> bool:
        return self.state in _ACTIVE_STATES


def is_installed_state(state: SkillState) -> bool:
    return state in _INSTALLED_STATES
