"""Diagnose contracts (M14-P0, TASK-094): failure corpus + signature + localization.

Leaf module — imports only pydantic/typing/enum/datetime (INV-017).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class FailureSeverity(str, Enum):
    """Severity mapping: error subclass → severity level."""

    LOW = "low"          # cosmetic, non-blocking (base HarnessError)
    MEDIUM = "medium"    # affects functionality (lifecycle/coverage/readiness)
    HIGH = "high"        # blocks release (meta/release/hook errors)
    CRITICAL = "critical"  # security/integrity violation (reserved)


class FailureRecord(BaseModel):  # extra="forbid"
    """One failure record in the corpus."""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    harness_id: str
    status: str            # HarnessRunStatus.value (FAILED/DIAGNOSED)
    error_type: str        # exception class name
    error_message: str     # normalized (no timestamps/uuids/paths)
    component: str         # localized module (e.g. "harness/meta/engine")
    signature: str         # sha256 fingerprint
    severity: FailureSeverity
    evidence: dict         # subset: {summary, error_type, status, metrics}
    timestamp: datetime


class FailureCorpusReport(BaseModel):  # extra="forbid"
    """Summary of the failure corpus."""

    model_config = ConfigDict(extra="forbid")

    total: int
    by_harness: dict[str, int]
    by_severity: dict[str, int]
    by_component: dict[str, int]
    unique_signatures: int
    recent: list[FailureRecord]  # 10 gần nhất
    reproducible: dict           # {aios_version, python_version}
