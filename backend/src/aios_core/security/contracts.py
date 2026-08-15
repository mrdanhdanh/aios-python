"""Security Baseline 1.0 — contracts (M10-F3, TASK-070)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class SecuritySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"


class SecurityStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"    # cơ chế tồn tại nhưng flag tắt / chưa enforce đầy đủ
    FAIL = "fail"    # cơ chế thiếu/không hoạt động


class SecurityItem(BaseModel):
    """Kết quả một baseline check."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    severity: SecuritySeverity
    status: SecurityStatus
    evidence: str  # module/literal/config đã kiểm tra — bắt buộc non-empty
    recommendation: str  # bắt buộc non-empty

    @field_validator("evidence", "recommendation")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("evidence/recommendation không được rỗng")
        return value


@dataclass
class SecurityReport:
    items: list[SecurityItem] = field(default_factory=list)

    @property
    def failures(self) -> list[SecurityItem]:
        return [i for i in self.items if i.status == SecurityStatus.FAIL]

    @property
    def blocking(self) -> bool:
        """FAIL severity critical → block (Gate B: critical = 0)."""
        return any(
            i.status == SecurityStatus.FAIL and i.severity == SecuritySeverity.CRITICAL
            for i in self.items
        )

    def summary(self) -> str:
        total = len(self.items)
        passed = sum(1 for i in self.items if i.status == SecurityStatus.PASS)
        warn = sum(1 for i in self.items if i.status == SecurityStatus.WARN)
        failed = len(self.failures)
        verdict = "SECURE" if not self.blocking else "BLOCKED (critical FAIL)"
        return (
            f"Security: {passed}/{total} pass · {warn} warn · {failed} fail "
            f"→ {verdict}"
        )
