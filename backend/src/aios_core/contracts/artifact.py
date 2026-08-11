"""Artifact contract: typed output produced by workflows/agents/tools."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any

from pydantic import field_validator

from .base import ContractMetadata

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ArtifactType(str, Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    PYTHON_FILE = "python_file"
    PATCH = "patch"
    IMAGE = "image"
    ZIP = "zip"
    TEST_REPORT = "test_report"
    COVERAGE = "coverage"


class ArtifactContract(ContractMetadata):
    """Metadata contract of an artifact.

    Inherits ``checksum``, ``created``/``updated``, ``version`` and contract
    versioning fields from ``ContractMetadata`` (no redeclaration).
    """

    type: ArtifactType
    storage_path: str
    metadata: dict[str, Any] = {}

    @field_validator("checksum")
    @classmethod
    def _validate_checksum(cls, value: str | None) -> str | None:
        if value is not None and not _SHA256_RE.match(value):
            raise ValueError("checksum must be a sha256 hex digest (64 lowercase hex chars)")
        return value

    @field_validator("storage_path")
    @classmethod
    def _validate_storage_path(cls, value: str) -> str:
        if not value:
            raise ValueError("storage_path must not be empty")
        if "\x00" in value:
            raise ValueError("storage_path must not contain NUL characters")
        return value

    def validate(self) -> bool:
        """Return False (not raise) when the contract is invalid."""
        if not self.version:
            return False
        if self.checksum is not None and not _SHA256_RE.match(self.checksum):
            return False
        if not self.storage_path:
            return False
        return True
