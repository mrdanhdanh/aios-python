"""Doctor checks (TASK-034, H5): injectable deterministic checks.

CheckFn = Callable[[], tuple[DoctorStatus, float, list[str]]]
— (status, score 0..1, details). Default = placeholder PASS.
"""

from __future__ import annotations

from typing import Callable

from .contracts import DoctorKind, DoctorResult, DoctorStatus

CheckFn = Callable[[], tuple[DoctorStatus, float, list[str]]]


class DoctorChecks:
    """Registry check theo kind — injectable (duck-typed, không chạy thật)."""

    def __init__(self) -> None:
        self._checks: dict[DoctorKind, CheckFn] = {}

    def register(self, kind: DoctorKind, fn: CheckFn) -> None:
        self._checks[kind] = fn

    def run(self, kind: DoctorKind) -> DoctorResult:
        fn = self._checks.get(kind, _placeholder)
        try:
            status, score, details = fn()
            score = max(0.0, min(1.0, float(score)))
            checks_total = 1
            checks_passed = 1 if status == DoctorStatus.PASS else 0
            return DoctorResult(kind=kind, status=status, score=score,
                                details=details, checks_total=checks_total,
                                checks_passed=checks_passed)
        except Exception as exc:  # noqa: BLE001 — C2-02: raise → ERROR
            return DoctorResult(kind=kind, status=DoctorStatus.ERROR, score=0.0,
                                details=[f"check raised: {exc}"],
                                checks_total=1, checks_passed=0)

    def run_all(self, kinds: list[DoctorKind] | None = None) -> list[DoctorResult]:
        """None → tất cả kinds (sorted theo enum order — C2-01)."""
        selected = kinds if kinds is not None else list(DoctorKind)
        return [self.run(kind) for kind in selected]


def _placeholder() -> tuple[DoctorStatus, float, list[str]]:
    """Placeholder deterministic — PASS 1.0 (user inject check thật qua API)."""
    return DoctorStatus.PASS, 1.0, ["placeholder check (no real probe)"]
