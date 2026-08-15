"""AIOS Ecosystem subsystem (M8 — TASK-046..TASK-049).

Bundles Registry v2 (discovery), Developer Kit (scaffold), Certification
(Harness gate) and Marketplace (trust chain) — each module independent,
composed via injection, no god object.

Public API:
    from aios_core.ecosystem import (
        EcosystemRegistry, EntryKind, EcosystemEntry, DevKit,
        CertificationEngine, CertLevel, TrustChain, MarketplaceRegistry,
    )
"""

from __future__ import annotations

from .certification import CertLevel, CertReport, CertificationEngine, default_checks
from .contracts import EcosystemEntry, EntryKind, Publisher
from .devkit import DevKit
from .errors import (
    CertificationError,
    DevKitError,
    EcosystemError,
    MarketplaceError,
    RegistryError,
)
from .marketplace import (
    InstallResult,
    MarketplaceRegistry,
    PackageRecord,
    TrustChain,
    canonical_json,
    sign_manifest,
    verify_signature,
)
from .registry import EcosystemRegistry

__all__ = [
    "CertLevel",
    "CertReport",
    "CertificationEngine",
    "CertificationError",
    "DevKit",
    "DevKitError",
    "EcosystemEntry",
    "EcosystemError",
    "EcosystemRegistry",
    "EntryKind",
    "InstallResult",
    "MarketplaceError",
    "MarketplaceRegistry",
    "PackageRecord",
    "Publisher",
    "RegistryError",
    "TrustChain",
    "canonical_json",
    "default_checks",
    "sign_manifest",
    "verify_signature",
]
