"""Release Gate contracts (M13-P3, TASK-092): System Readiness ≠ Harness Trust.

Release Gate là pure combiner — tổ hợp 2 score ĐỘC LẬP (System Readiness
từ HarnessReadinessReport + Harness Trust từ MetaReport) thành 1 verdict.
Leaf module — chỉ import pydantic/typing/enum (INV-017).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ReleaseGateStatus(str, Enum):
    """Verdict cuối trước release."""

    PASS = "pass"        # cả System Readiness + Harness Trust PASS → cho phép
    BLOCKED = "blocked"  # ít nhất 1 score fail → chặn release (fail-closed)


class ReleaseGateReport(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    system_readiness: dict   # {status: str, summary: str} (từ HarnessReadinessReport)
    harness_trust: dict      # {status: str, summary: str} (từ MetaReport)
    both_pass: bool
    status: ReleaseGateStatus
    summary: str
    reproducible: dict       # {aios_version, python_version} (KHÔNG timestamp)
