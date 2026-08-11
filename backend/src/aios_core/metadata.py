"""AIOS component metadata: id, name, version, author, timestamps, etc."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator

from .healthcheck import HealthStatus

# Official semver regex (https://semver.org) — allows pre-release + build metadata.
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class AiOSMetadata(BaseModel):
    """Standard metadata attached to every AIOS component."""

    id: str
    name: str
    version: str
    author: str
    created: datetime = Field(default_factory=_now_utc)
    updated: datetime = Field(default_factory=_now_utc)
    license: str
    dependencies: list[str] = []
    permissions: list[str] = []
    tags: list[str] = []
    health: HealthStatus | None = None
    checksum: str | None = None  # sha256 — computed by the component when creating an artifact

    @field_validator("version")
    @classmethod
    def _validate_semver(cls, value: str) -> str:
        if not SEMVER_RE.match(value):
            raise ValueError(
                f"Invalid semver: {value!r} (expected X.Y.Z with optional -pre and +build)"
            )
        return value

    def model_post_init(self, __context) -> None:  # noqa: ANN001
        if self.updated < self.created:
            raise ValueError("updated must be >= created")


def make_component_metadata(
    *,
    id: str,
    name: str,
    version: str,
    author: str = "AIOS",
    license: str = "MIT",
    dependencies: list[str] | None = None,
    permissions: list[str] | None = None,
    tags: list[str] | None = None,
    created: datetime | None = None,
) -> AiOSMetadata:
    """Build component metadata with sensible defaults.

    ``checksum`` and ``health`` are always ``None`` — the component itself
    computes/populates them later.
    """
    kwargs: dict = {
        "id": id,
        "name": name,
        "version": version,
        "author": author,
        "license": license,
        "dependencies": dependencies or [],
        "permissions": permissions or [],
        "tags": tags or [],
    }
    if created is not None:
        kwargs["created"] = created
        kwargs["updated"] = created  # starts equal; updated may change later
    return AiOSMetadata(**kwargs)
