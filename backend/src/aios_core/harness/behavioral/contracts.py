"""Behavioral Conformance contracts (M13-P0, TASK-089).

Chứng minh harness hành vi ổn định qua thời gian (temporal determinism),
dưới tải (load), chạy dài (soak) và phục hồi lỗi (failure recovery).
Tái dùng Scenario/SimulationOutcome/SimulationStatus/Fault (testing) +
Baseline/BenchmarkReport (benchmark) — không tạo hệ thống song song.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

from ..benchmark.contracts import Baseline, BenchmarkReport
from ..testing.contracts import Fault, Scenario, SimulationStatus


class ConformanceProfile(str, Enum):
    """Số iteration mặc định theo profile (PLAN §M13 P0)."""

    QUICK = "quick"        # 100 iterations
    STANDARD = "standard"  # 1000 iterations
    STRESS = "stress"      # 10000 iterations
    SOAK = "soak"          # duration-based (giây)


class ConformanceStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"          # MISMATCH / deterministic / repeat fail
    ERROR = "error"        # iteration ERROR (fault không recover / exception)


class ConformanceConfig(BaseModel):
    """Cấu hình một behavioral conformance run.

    scenario: full Scenario (P1-5 v1) — engine không tự resolve từ id.
    fault_iterations: 1-based; chỉ iteration trong list có fault.
    repeat_samples: số iteration đầu chạy double-run (repeat) — cap
    min(repeat_samples, iterations) tại runtime (P1-2 v2).
    """

    model_config = ConfigDict(extra="forbid")

    profile: ConformanceProfile = ConformanceProfile.QUICK
    scenario: Scenario
    iterations: int | None = None     # override profile; thắng soak (P3-3 v1)
    duration_s: float = 0.0           # soak: chạy tối đa duration giây (0 → 1)
    faults: list[Fault] = []          # áp cho mọi iteration (injector mới mỗi lần)
    fault_iterations: list[int] = []  # chỉ inject fault ở iteration này (1-based)
    repeat_samples: int = 3
    baseline: Baseline | None = None  # regression gate baseline (chỉ expose — P1-3 v1)
    strict: bool = True               # verify: status != PASS → raise (P3-5 v1)

    @field_validator("iterations")
    @classmethod
    def _iterations_positive(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("iterations must be >= 1")
        return v

    @field_validator("fault_iterations")
    @classmethod
    def _fault_iterations_valid(cls, v: list[int], info) -> list[int]:
        deduped = sorted(set(v))
        if any(i < 1 for i in deduped):
            raise ValueError("fault_iterations must be 1-based (>= 1)")
        if deduped and not info.data.get("faults"):
            raise ValueError("fault_iterations requires faults to be non-empty")
        return deduped

    @field_validator("repeat_samples")
    @classmethod
    def _repeat_samples_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("repeat_samples must be >= 0")
        return v


class ConformanceIterationSummary(BaseModel):
    """Summary per-iteration — KHÔNG giữ full outcome (P2-6 v1).

    repeat_ok: None = iteration không được repeat (P1-2 v2).
    recovered: False khi không có fault (P3-6 v2).
    """

    model_config = ConfigDict(extra="forbid")

    index: int  # 1-based
    status: SimulationStatus
    evidence_digest: str  # sha256(outcome.model_dump_json())
    repeat_ok: bool | None = None
    fault_injected: bool
    recovered: bool = False


class ConformanceReport(BaseModel):
    """Kết quả behavioral conformance run.

    deterministic: digest nhóm iteration không-fault giống nhau (P3-6 v1).
    repeat_consistent: mọi iteration ĐƯỢC repeat đều repeat_ok=True (P1-2 v2).
    gate: chỉ expose — KHÔNG quyết định status (P1-3 v1 + P1-1 v2).
    """

    model_config = ConfigDict(extra="forbid")

    profile: ConformanceProfile
    scenario_id: str
    iterations_total: int
    status: ConformanceStatus
    deterministic: bool
    repeat_consistent: bool
    fault_recovery_rate: float  # recovered / faults_injected (0 nếu không fault)
    iterations: list[ConformanceIterationSummary] = []
    metrics: dict = {}  # counts only: iterations_total, faults_injected_total,
    # recovery_events_total, repeat_runs, mismatch_count, error_count (P3-7 v2)
    findings: list[str] = []
    gate: BenchmarkReport | None = None
    summary: str = ""
    reproducible: dict = {}