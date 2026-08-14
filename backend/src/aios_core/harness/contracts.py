"""Harness contracts (TASK-029, H1): run/event/result/artifact/report.

Leaf module — imports only pydantic/typing/datetime/enum/uuid (INV-017:
no kernel imports in contracts).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

#: Windows-invalid path characters (B4): sanitized in safe_run_id().
_INVALID_PATH_CHARS = re.compile(r'[\\/:*?"<>|]')


def safe_run_id(run_id: str) -> str:
    """Path-safe segment for evidence storage (B4 — also blocks '.'/'..' empty)."""
    cleaned = _INVALID_PATH_CHARS.sub("_", run_id)
    cleaned = cleaned.replace("..", "_").strip("._")
    return cleaned or "run"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HarnessRunStatus(str, Enum):
    CREATED = "created"
    PREPARING = "preparing"
    VALIDATING = "validating"
    RUNNING = "running"
    VERIFYING = "verifying"
    COMPLETED = "completed"  # terminal (failure path -> FAILED — C1-02)
    FAILED = "failed"  # NOT terminal (goes to DIAGNOSED)
    DIAGNOSED = "diagnosed"  # terminal


class HarnessRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    harness: str
    target: str
    version: str | None = None
    environment: str = "local"
    started_at: datetime
    status: HarnessRunStatus = HarnessRunStatus.CREATED
    ended_at: datetime | None = None  # set on BOTH success and failure (B6)
    error: str | None = None


class HarnessEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    phase: str
    timestamp: datetime
    level: Literal["info", "warning", "error"] = "info"
    message: str


class HarnessResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    status: HarnessRunStatus
    summary: str
    metrics: dict[str, Any] = {}  # v1: duration_ms + phase_count
    artifacts: list[str] = []  # harness artifact ids (B5)


class HarnessArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str  # DETERMINISTIC f"{run_id}:{kind}" (C2-02)
    run_id: str
    kind: str
    path: str | None = None
    ref: str | None = None  # sha256 checksum (tamper-evident)
    created_at: datetime


class HarnessReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    summary: str
    result: HarnessResult
    artifacts: list[HarnessArtifact] = []
    generated_at: datetime
