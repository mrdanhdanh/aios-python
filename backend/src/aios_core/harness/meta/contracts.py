"""Meta-Harness contracts (M13-P2, TASK-091): verify the verifier.

Adversarial cases + oracle (hardcode, independent path — P2-1) + report.
Leaf module — imports only pydantic/typing/enum (INV-017).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class MetaCase(str, Enum):
    """8 adversarial cases (PLAN §M13-7)."""
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    MALFORMED_EVIDENCE = "malformed_evidence"
    BROKEN_VERIFIER = "broken_verifier"
    CORRUPTED_ARTIFACT = "corrupted_artifact"
    REPLAY_MISMATCH = "replay_mismatch"
    SKIPPED_VERIFICATION = "skipped_verification"
    VERIFY_SKIPPED = "verify_skipped"  # case 8 (P2-4)


class MetaOracle(str, Enum):  # P2-4: chuẩn hóa expected_state
    NOT_PASS = "not_pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    TAMPER = "tamper"
    CORRUPT = "corrupt"


class MetaCaseResult(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    case: MetaCase
    verifier_state: str          # Verdict.value | "TAMPER:..." | "corrupt" | "COMPLETED"
    expected_state: MetaOracle   # oracle (hardcode — KHÔNG gọi hàm production) (P2-1)
    fail_closed: bool            # P1-1: Meta ĐẠT mục tiêu adversarial của case
    detail: str


class MetaStatus(str, Enum):
    PASS = "pass"                # mọi case fail_closed=True
    FAIL = "fail"                # có case bỏ lọt (verifier không fail-closed)


class MetaReport(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    cases: list[MetaCaseResult]
    all_fail_closed: bool
    status: MetaStatus
    metrics: dict                # {total, fail_closed, by_case: dict[str,int]} (P3-3)
    summary: str
    reproducible: dict           # {aios_version, python_version, registry_harness_ids} (P3-2)
