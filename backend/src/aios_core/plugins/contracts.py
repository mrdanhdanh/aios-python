"""Plugin contracts (TASK-044, M8-E2).

The plugin lifecycle REUSES the Skills Manager 10-state machine from M2/M4
(PLAN §M8-E2): ``PluginState`` is an alias of ``SkillState`` and transitions are
computed by the shared ``assert_transition`` — no second state machine is ever
defined. DISCOVERED / LOADED / RUNNING are observational ``runtime_status``
values only, NOT states of the lifecycle machine.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ..metadata import AiOSMetadata
from ..semver import parse_version
from ..skills.base import SkillState, assert_transition  # reuse — no second machine
from .errors import PluginError, PluginStateError

PluginState = SkillState  # 10-state machine shared with skills (T2-T10)

_PLUGIN_STATES = tuple(s.value for s in SkillState)


class PluginType(str, Enum):
    """Plugin kinds (PLAN §M8-E2): Agent · Capability · Tool · Skill ·
    Workflow · Model Provider · Memory · UI · Integration."""

    AGENT = "agent"
    CAPABILITY = "capability"
    TOOL = "tool"
    SKILL = "skill"
    WORKFLOW = "workflow"
    MODEL_PROVIDER = "model_provider"
    MEMORY = "memory"
    UI = "ui"
    INTEGRATION = "integration"


_ALL_TYPES = tuple(t.value for t in PluginType)


class AiosRange(BaseModel):
    """Compatibility window against the running AIOS version."""

    model_config = ConfigDict(extra="forbid")

    min: str = "0.0.0"
    max: str = "*"  # "2.x" | "2.1.3" | "*"

    @classmethod
    def validate_range(cls, **kwargs) -> "AiosRange":
        obj = cls(**kwargs)
        parse_constraint(obj.min)
        parse_constraint(obj.max)
        return obj


class ProvidedEntry(BaseModel):
    """One unit a plugin provides (PLAN §M8-E2 provides list)."""

    model_config = ConfigDict(extra="forbid")

    kind: PluginType
    id: str  # e.g. "github.search" for a tool, "github.repository" for a capability


class PluginManifest(BaseModel):
    """Plugin manifest (PLAN §M8-E2 example)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str  # semver — validate bằng aios_core.semver
    aios: AiosRange = Field(default_factory=AiosRange)
    plugin_type: PluginType = PluginType.INTEGRATION
    provides: list[ProvidedEntry] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)  # "id" | "id@>=X.Y.Z"
    description: str = ""
    metadata: AiOSMetadata | None = None

    @classmethod
    def validate_manifest(cls, **kwargs) -> "PluginManifest":
        if not kwargs.get("id", "").strip():
            raise ValueError("id must not be empty")
        if not kwargs.get("name", "").strip():
            raise ValueError("name must not be empty")
        version = kwargs.get("version", "")
        try:
            parse_version(version)
        except ValueError:
            raise ValueError(f"invalid semver version: {version!r}") from None
        for dep in kwargs.get("dependencies", []):
            if not dep or not dep.strip():
                raise ValueError("dependency must not be empty")
        for perm in kwargs.get("permissions", []):
            if not perm or not perm.strip():
                raise ValueError("permission must not be empty")
        return cls(**kwargs)


class Plugin(BaseModel):
    """Read view of a plugin record (matches plugins table row)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str
    plugin_type: PluginType
    state: PluginState
    manifest: dict = Field(default_factory=dict)
    history: list[dict] = Field(default_factory=list)
    installed_at: str | None = None
    created_at: str
    updated_at: str


# Re-export for manager/registry (single source of truth).
__all__ = [
    "AiosRange",
    "Plugin",
    "PluginManifest",
    "PluginState",
    "PluginType",
    "ProvidedEntry",
    "assert_transition",
    "_ALL_TYPES",
    "_PLUGIN_STATES",
]
