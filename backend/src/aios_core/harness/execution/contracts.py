"""Execution verification contracts (TASK-030, H2): checks, verdict, task."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict


class CheckKind(str, Enum):
    FILE_EXISTS = "file_exists"
    TEST_RUN = "test_run"
    COVERAGE = "coverage"
    CONTAINS = "contains"
    CUSTOM = "custom"


class Check(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    kind: CheckKind
    params: dict[str, Any] = {}


class VerificationTask(BaseModel):
    """Task to verify: pre/post conditions + invariants around an execution."""

    model_config = ConfigDict(extra="forbid")

    execution_ref: str  # C1-01/P3-08: plan.id convention; graph prefix `graph:` OK
    preconditions: list[Check] = []
    postconditions: list[Check] = []
    invariants: list[Check] = []
    base_dir: str = "."  # C2-04: cho FILE_EXISTS/CONTAINS (khuyến cáo absolute — P3-05)


class CheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check: Check
    passed: bool = False
    detail: str = ""
    skipped: bool = False


class Verdict(str, Enum):
    PASS = "pass"
    PASS_WITH_WARNING = "pass_with_warning"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"


class VerificationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    execution_ref: str
    verdict: Verdict
    check_results: list[CheckResult]
    summary: str
    metrics: dict[str, Any] = {}  # R3-7: deterministic counts only


class EvidenceServices:
    """Duck-typed services (P1-02 v2): KHÔNG import kernel.graph/planning/events.

    Contract (shape): state.get_state(ref) -> dict|None · events.query_audit(
    limit=..., event_type=None) -> list[EventLike] (EventLike có to_dict()) ·
    artifacts.store(contract, bytes) -> contract · artifacts.list(type=None).
    """

    state: Callable[..., Any]
    events: Callable[..., Any]
    artifacts: Callable[..., Any]

    def __init__(self, state: Any, events: Any, artifacts: Any) -> None:
        self.state = state
        self.events = events
        self.artifacts = artifacts
