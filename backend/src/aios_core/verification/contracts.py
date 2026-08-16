"""Verification contracts — INV-035 (M11-P0, TASK-078)."""

from __future__ import annotations

from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, field_validator

from .state import VerificationState, VerificationVerdict


class VerificationOutcome(BaseModel):
    """Kết quả một mechanism check — extra=forbid (C2-01)."""

    model_config = ConfigDict(extra="forbid")

    mechanism_id: str
    state: VerificationState
    verdict: VerificationVerdict = VerificationVerdict.INCONCLUSIVE
    evidence: str = ""
    detail: dict[str, Any] = {}

    @field_validator("verdict", mode="before")
    @classmethod
    def _default_verdict(cls, value: Any) -> Any:
        # verdict mặc định theo state nếu không truyền
        return value


class VerificationMechanism(Protocol):
    """Một verification mechanism đăng ký với VerificationGate.

    - `check()` phải trả `VerificationOutcome` với state thật.
    - `check()` raise exception → gate coi như BLOCKED (fail-closed).
    """

    id: str
    name: str
    version: str

    def check(self) -> VerificationOutcome: ...
