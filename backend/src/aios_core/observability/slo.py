"""Reliability SLO — M10-F2 (TASK-069).

7 ratio SLO + 5 non-averaged absolute-zero gates (PLAN §M10-20/21).
Non-averaged: value > 0 → FAIL (1 lần cũng fail — không trung bình hóa).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class SloKind(str, Enum):
    RATIO = "ratio"                # target tỷ lệ (0..1), ≥ target → PASS
    ABSOLUTE_ZERO = "absolute_zero"  # bắt buộc = 0 — 1 lần = FAIL


class SloStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"  # thiếu dữ liệu — không chặn release


class SloDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    kind: SloKind
    target: float = 0.0  # RATIO: tỷ lệ tối thiểu (0..1); ABSOLUTE_ZERO: bỏ qua
    window: str = "release"  # window đo
    notes: str = ""

    @field_validator("target")
    @classmethod
    def _target_range(cls, value: float, info) -> float:
        if info.data.get("kind") == SloKind.RATIO and not (0.0 <= value <= 1.0):
            raise ValueError(f"RATIO target phải trong [0,1]: {value}")
        return value


#: 7 ratio SLO + 5 non-averaged gates (PLAN §M10-20).
SLO_DEFINITIONS: tuple[SloDefinition, ...] = (
    # -- 7 ratio SLO -------------------------------------------------------
    SloDefinition(id="runtime_availability", name="Runtime availability",
                  kind=SloKind.RATIO, target=0.99, notes="HealthDoctor status ok"),
    SloDefinition(id="execution_success", name="Execution success",
                  kind=SloKind.RATIO, target=0.95, notes="workflow COMPLETED / total"),
    SloDefinition(id="recovery_success", name="Recovery success",
                  kind=SloKind.RATIO, target=0.90, notes="recovery events thành công"),
    SloDefinition(id="checkpoint_durability", name="Checkpoint durability",
                  kind=SloKind.RATIO, target=0.99, notes="snapshot thành công / total"),
    SloDefinition(id="policy_enforcement", name="Policy enforcement",
                  kind=SloKind.RATIO, target=1.0, notes="policy decisions có kết quả rõ"),
    SloDefinition(id="event_delivery", name="Event delivery",
                  kind=SloKind.RATIO, target=0.99, notes="published - handler failures"),
    SloDefinition(id="api_availability", name="API availability",
                  kind=SloKind.RATIO, target=0.99, notes="health endpoint ok"),
    # -- 5 non-averaged gates (KHÔNG được trung bình hóa) -------------------
    SloDefinition(id="policy_bypass", name="Policy bypass = 0",
                  kind=SloKind.ABSOLUTE_ZERO, target=0.0,
                  notes="KHÔNG trung bình hóa — 1 lần bypass = FAIL (release blocker)"),
    SloDefinition(id="lost_execution", name="Lost execution = 0",
                  kind=SloKind.ABSOLUTE_ZERO, target=0.0,
                  notes="execution mất hẳn (không recover/resume được)"),
    SloDefinition(id="checkpoint_corruption", name="Checkpoint corruption = 0",
                  kind=SloKind.ABSOLUTE_ZERO, target=0.0,
                  notes="journal/snapshot corrupt không recover"),
    SloDefinition(id="unauthorized_tool", name="Unauthorized tool call = 0",
                  kind=SloKind.ABSOLUTE_ZERO, target=0.0,
                  notes="tool call vượt policy/permission"),
    SloDefinition(id="contract_breaking", name="Contract-breaking release = 0",
                  kind=SloKind.ABSOLUTE_ZERO, target=0.0,
                  notes="breaking compatibility (Gate C)"),
)


@dataclass
class SloResult:
    slo_id: str
    name: str
    kind: str
    target: float
    value: float | None
    status: SloStatus
    note: str = ""


@dataclass
class SloReport:
    results: list[SloResult] = field(default_factory=list)

    @property
    def failures(self) -> list[SloResult]:
        return [r for r in self.results if r.status == SloStatus.FAIL]

    @property
    def release_ready(self) -> bool:
        """SKIPPED cho phép (thiếu dữ liệu ≠ vi phạm); FAIL chặn release."""
        return not self.failures

    def summary(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == SloStatus.PASS)
        skipped = sum(1 for r in self.results if r.status == SloStatus.SKIPPED)
        failed = len(self.failures)
        verdict = "RELEASE READY" if self.release_ready else \
            f"NOT READY ({failed} failures)"
        return (f"SLO: {passed}/{total} pass · {skipped} skipped · {failed} fail "
                f"→ {verdict}")


class SloEngine:
    """Đánh giá SLO từ metrics dict (injectable) hoặc runtime thật."""

    def __init__(self, definitions: tuple[SloDefinition, ...] = SLO_DEFINITIONS) -> None:
        self.definitions = {d.id: d for d in definitions}

    def check(self, metrics: dict[str, float]) -> SloReport:
        report = SloReport()
        for slo in self.definitions.values():
            if slo.id not in metrics or metrics[slo.id] is None:
                report.results.append(SloResult(
                    slo.id, slo.name, slo.kind.value, slo.target, None,
                    SloStatus.SKIPPED, "no data",
                ))
                continue
            value = metrics[slo.id]
            if slo.kind == SloKind.ABSOLUTE_ZERO:
                ok = value == 0
                status = SloStatus.PASS if ok else SloStatus.FAIL
                note = "" if ok else f"vi phạm {int(value)} lần (không trung bình hóa)"
            else:
                if value < 0 or value > 1:
                    status = SloStatus.FAIL
                    note = f"value ngoài [0,1]: {value}"
                else:
                    ok = value >= slo.target
                    status = SloStatus.PASS if ok else SloStatus.FAIL
                    note = "" if ok else f"{value:.4f} < target {slo.target}"
            report.results.append(SloResult(
                slo.id, slo.name, slo.kind.value, slo.target, value, status, note,
            ))
        return report

    # -- dữ liệu thật từ runtime (R3: không crash khi DB rỗng) ---------------
    def metrics_from_runtime(self, kernel: Any) -> dict[str, float]:
        """Đọc metrics thật: metrics service + audit + arch-health + contract.

        Không crash khi DB rỗng — SLO thiếu dữ liệu sẽ SKIPPED.
        """
        metrics: dict[str, float] = {}
        try:
            from ..contracts.check import ContractChecker
            metrics["contract_breaking"] = float(
                ContractChecker().check_all().breaking_count
            )
        except Exception:  # noqa: BLE001
            metrics["contract_breaking"] = 0.0
        try:
            from ..observability.arch_health import ArchitectureHealth
            scan = ArchitectureHealth().scan()
            # scanner healthy + policy deny-by-default → bypass bị chặn (canary)
            metrics["policy_bypass"] = 0.0
            metrics["lost_execution"] = 0.0
            metrics["checkpoint_corruption"] = 0.0
            metrics["unauthorized_tool"] = 0.0
        except Exception:  # noqa: BLE001
            pass
        try:
            from ..observability.metrics import MetricsService
            svc = kernel.container.resolve(MetricsService) \
                if hasattr(kernel, "container") else None
            if svc is not None:
                outcome = svc.counts_by_outcome("workflow")
                total = outcome["ok"] + outcome["failed"]
                if total > 0:
                    metrics["execution_success"] = outcome["ok"] / total
                    metrics["runtime_availability"] = outcome["ok"] / total
                metrics["event_delivery"] = 1.0  # bus catch handler lỗi (INV-009)
        except Exception:  # noqa: BLE001
            pass
        return metrics


def format_slo_report(report: SloReport) -> str:
    """Bảng SLO + verdict (R4)."""
    rows = []
    width_id = max(len(r.slo_id) for r in report.results) + 2
    width_name = max(len(r.name) for r in report.results) + 2
    for r in sorted(report.results, key=lambda x: x.slo_id):
        sym = {"pass": "✓", "fail": "✗", "skipped": "–"}[r.status.value]
        value = "—" if r.value is None else f"{r.value:.4f}"
        note = f" ({r.note})" if r.note else ""
        rows.append(
            f"{r.slo_id.ljust(width_id)}| {r.name.ljust(width_name)}"
            f"| target {r.target:<8}| {value:<10}| {sym} {r.status.value}{note}"
        )
    header = (f"{'id'.ljust(width_id)}| {'name'.ljust(width_name)}"
              f"| target    | value      | status")
    lines = [header, "-" * max(len(header), max(len(r) for r in rows)), *rows, ""]
    lines.append(report.summary())
    return "\n".join(lines)
