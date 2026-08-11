"""Base contract types: ContractVersion, Contract ABC, ContractMetadata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel, field_validator

from ..metadata import AiOSMetadata, SEMVER_RE


class ContractCompatibility(str, Enum):
    MAJOR_BREAKING = "major_breaking"
    MINOR_COMPATIBLE = "minor_compatible"


class ContractVersion(BaseModel):
    """Version declaration of a contract (3-fields, semver validated)."""

    contract_version: str
    schema_version: str
    compatibility: ContractCompatibility = ContractCompatibility.MINOR_COMPATIBLE

    @field_validator("contract_version", "schema_version")
    @classmethod
    def _validate_contract_semver(cls, value: str) -> str:
        if not SEMVER_RE.match(value):
            raise ValueError(f"Invalid semver: {value!r}")
        return value


class Contract(ABC):
    """Base interface for all AIOS contracts.

    Note: pydantic v2 clears ``__abstractmethods__`` when a model completes,
    so abstract methods are NOT enforced at instantiation on ``ContractMetadata``
    subclasses. ``validate()`` remains the runtime enforcement point and is
    implemented by concrete contracts (e.g. ``ArtifactContract``).
    """

    @abstractmethod
    def validate(self) -> bool:
        """Validate the contract payload; return False instead of raising."""


class ContractMetadata(AiOSMetadata, Contract):
    """Component metadata extended with contract versioning fields.

    MRO: BaseModel first, ABC second (works with pydantic v2).
    """

    contract_version: str
    schema_version: str
    compatibility: ContractCompatibility = ContractCompatibility.MINOR_COMPATIBLE

    @field_validator("contract_version", "schema_version")
    @classmethod
    def _validate_contract_semver(cls, value: str) -> str:
        if not SEMVER_RE.match(value):
            raise ValueError(f"Invalid semver: {value!r}")
        return value

    @field_validator("version")
    @classmethod
    def _validate_version_meta(cls, value: str) -> str:
        # Redeclared under a different name so it is not shadowed by the
        # contract-version validators above (pydantic v2 keys decorators by
        # method name; a same-named method in a subclass replaces the base one).
        if not SEMVER_RE.match(value):
            raise ValueError(f"Invalid semver: {value!r}")
        return value
