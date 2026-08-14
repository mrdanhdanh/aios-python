"""Doctor & Readiness contracts (TASK-034, H5)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class DoctorKind(str, Enum):
    """13 doctor loại (PLAN §H5)."""

    ARCHITECTURE = "architecture"
    RUNTIME = "runtime"
    WORKFLOW = "workflow"
    AGENT = "agent"
    CAPABILITY = "capability"
    TOOL = "tool"
    MEMORY = "memory"
    MODEL = "model"
    POLICY = "policy"
    REGISTRY = "registry"
    PERFORMANCE = "performance"
    SECURITY = "security"
    EVIDENCE = "evidence"


class DoctorStatus(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


class DoctorResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: DoctorKind
    status: DoctorStatus
    score: float = 0.0  # 0..1
    details: list[str] = []
    checks_total: int = 0
    checks_passed: int = 0


class HardGate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    detail: str = ""


class ReadinessReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dimensions: dict[str, float] = {}  # kind → score (chỉ kinds đã chạy — P3-02)
    overall: float = 0.0
    hard_gates: list[HardGate] = []  # policy → overall (P2-02 order)
    ready: bool = False
    summary: str = ""
    metrics: dict = {}  # counts — deterministic
    reproducible: dict = {}
