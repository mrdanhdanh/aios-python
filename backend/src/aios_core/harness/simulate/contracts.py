"""Simulation contracts (M14-P2, TASK-096): verify fix in sandbox."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class SimulationResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    ERROR = "error"


class SimulationReport(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    candidate_signature: str
    result: SimulationResult
    checks_passed: int
    checks_total: int
    meta_verify_pass: bool  # Meta-Harness still pass after fix?
    detail: str
    reproducible: dict
