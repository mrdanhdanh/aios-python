"""AIOS contracts: versioned component contracts (Contract-First)."""

from .artifact import ArtifactContract, ArtifactType
from .base import (
    Contract,
    ContractCompatibility,
    ContractMetadata,
    ContractVersion,
)
from .compatibility import (
    CompatibilityChecker,
    CompatibilityResult,
)

__all__ = [
    "ArtifactContract",
    "ArtifactType",
    "Contract",
    "ContractCompatibility",
    "ContractMetadata",
    "ContractVersion",
    "CompatibilityChecker",
    "CompatibilityResult",
]
