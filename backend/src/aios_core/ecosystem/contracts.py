"""Ecosystem shared contracts (TASK-046, M8-E4).

A single ``EcosystemEntry`` captures everything the Ecosystem Registry needs
(identity, metadata, contract, permissions, dependencies, compatibility,
security, capabilities, artifacts, publisher, signature) so discovery does not
have to scan the underlying registries.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from ..metadata import AiOSMetadata
from ..semver import parse_version


class EntryKind(str, Enum):
    AGENT = "agent"
    CAPABILITY = "capability"
    TOOL = "tool"
    SKILL = "skill"
    WORKFLOW = "workflow"
    MODEL = "model"
    PROVIDER = "provider"
    PLUGIN = "plugin"
    INTEGRATION = "integration"
    EXTENSION = "extension"


class Publisher(BaseModel):
    """Who publishes the entry (M8-E6 trust model)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = ""
    signing_key_id: str | None = None  # key fingerprint — never the raw key


class EcosystemEntry(BaseModel):
    """Registry v2 entry (PLAN §M8-E4): identity + full metadata."""

    model_config = ConfigDict(extra="forbid")

    kind: EntryKind
    id: str
    version: str  # semver — validate khi index
    name: str = ""
    description: str = ""
    metadata: dict = Field(default_factory=dict)
    contract_namespace: str = "extension"
    contract_version: str = "1.0"
    permissions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    compatibility: dict = Field(default_factory=dict)  # aios: {min, max}
    security: dict = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    publisher: Publisher | None = None
    signature: str = ""
    metadata_obj: AiOSMetadata | None = None

    @classmethod
    def validate_entry(cls, **kwargs) -> "EcosystemEntry":
        if not kwargs.get("id", "").strip():
            raise ValueError("id must not be empty")
        version = kwargs.get("version", "")
        try:
            parse_version(version)
        except ValueError:
            raise ValueError(f"invalid semver version: {version!r}") from None
        return cls(**kwargs)


__all__ = ["EcosystemEntry", "EntryKind", "Publisher"]
