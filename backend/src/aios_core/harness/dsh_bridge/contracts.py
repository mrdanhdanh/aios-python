"""DSH Bridge contracts (M16, TASK-104..108): dsh integration as independent oracle."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class DSHStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    UNCONFIGURED = "unconfigured"


class InvariantResult(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    invariant_id: str
    name: str
    passed: bool
    detail: str
    source: str  # "dsh" | "aios"


class OracleReport(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    dsh_status: DSHStatus
    invariants_checked: int
    invariants_passed: int
    invariants_failed: int
    results: list[InvariantResult]
    is_truly_independent: bool  # True if dsh is separate process/codebase
    summary: str
    reproducible: dict


class DSHConfig(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    bin_path: str = ""  # path to dsh binary
    version: str = ""   # pinned version
    telemetry_disabled: bool = True  # default off for privacy
