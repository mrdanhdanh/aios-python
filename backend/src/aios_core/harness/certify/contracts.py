"""Certify contracts (M14-P3, TASK-097): apply + rollback + certified baseline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class RemediationStatus(str, Enum):
    PENDING = "pending"
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    CERTIFIED = "certified"
    FAILED = "failed"


class CertifiedBaseline(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    before_version: str
    candidate_version: str
    after_version: str | None = None
    certification_id: str
    rollback_point: str
    timestamp: datetime


class RemediationRecord(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    failure_signature: str
    candidate_description: str
    risk_level: str
    status: RemediationStatus
    baseline: CertifiedBaseline | None = None
    detail: str
    timestamp: datetime


class CertifyReport(BaseModel):  # extra="forbid"
    model_config = ConfigDict(extra="forbid")

    total: int
    applied: int
    rolled_back: int
    certified: int
    failed: int
    records: list[RemediationRecord]
    summary: str
    reproducible: dict
