"""Runtime Hardening — Failure Matrix 1.0 (M10-F2, TASK-065).

12 loại failure (PLAN §M10-12) với chuỗi `detect → contain → recover →
resume` — KHÔNG `entire execution lost`. Mọi fault inject qua hook/test
double — KHÔNG sửa kernel/services (R1).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class FailureKind(str, Enum):
    MODEL = "model"
    TOOL = "tool"
    AGENT = "agent"
    PROCESS = "process"
    NETWORK = "network"
    DB = "db"
    PLUGIN = "plugin"
    WORKER_TIMEOUT = "worker_timeout"
    RESOURCE = "resource"
    MEMORY_CORRUPTION = "memory_corruption"
    CHECKPOINT = "checkpoint"
    EVENT_CONSUMER = "event_consumer"


FAILURE_KINDS: tuple[str, ...] = tuple(k.value for k in FailureKind)


class ScenarioStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


@dataclass
class ScenarioOutcome:
    scenario_id: str
    kind: str
    status: ScenarioStatus
    detect: bool = False
    contain: bool = False
    recovered: bool = False
    resumed: bool = False
    error: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class FailureScenario:
    """Một scenario failure: fault → detect → contain → recover → resume.

    ``fault_fn(ctx)``         — inject lỗi (test double/hook, không sửa service)
    ``detect_fn(ctx)``        — phát hiện lỗi → bool (kèm evidence trong ctx)
    ``contain_fn(ctx)``       — cô lập: hệ thống không crash/lan → bool
    ``recover_fn(ctx)``       — phục hồi → bool
    ``resume_fn(ctx)``        — tiếp tục công việc (không chạy lại phần xong) → bool
    """

    scenario_id: str
    kind: str
    target: str
    fault_fn: Callable[[dict[str, Any]], None]
    detect_fn: Callable[[dict[str, Any]], bool]
    contain_fn: Callable[[dict[str, Any]], bool]
    recover_fn: Callable[[dict[str, Any]], bool]
    resume_fn: Callable[[dict[str, Any]], bool]


class FailureMatrix:
    """Registry 12 FailureKind — trùng id → raise."""

    def __init__(self, scenarios: list[FailureScenario] | None = None) -> None:
        self._scenarios: dict[str, FailureScenario] = {}
        for sc in scenarios or []:
            self.register(sc)

    def register(self, scenario: FailureScenario) -> None:
        if scenario.scenario_id in self._scenarios:
            raise ValueError(f"Duplicate scenario id: {scenario.scenario_id}")
        if scenario.kind not in FAILURE_KINDS:
            raise ValueError(f"Unknown FailureKind: {scenario.kind}")
        self._scenarios[scenario.scenario_id] = scenario

    def get(self, scenario_id: str) -> FailureScenario:
        return self._scenarios[scenario_id]

    def all(self) -> list[FailureScenario]:
        return list(self._scenarios.values())

    def kinds_covered(self) -> set[str]:
        return {s.kind for s in self._scenarios.values()}


class HardeningRunner:
    """Chạy scenario — một scenario fail không crash cả suite (R2)."""

    def __init__(self, matrix: FailureMatrix) -> None:
        self.matrix = matrix

    def run(self, scenario: FailureScenario, ctx: dict[str, Any] | None = None) -> ScenarioOutcome:
        ctx = ctx or {}
        outcome = ScenarioOutcome(
            scenario_id=scenario.scenario_id,
            kind=scenario.kind,
            status=ScenarioStatus.PASS,
        )
        try:
            scenario.fault_fn(ctx)
            outcome.detect = scenario.detect_fn(ctx)
            outcome.contain = scenario.contain_fn(ctx)
            outcome.recovered = scenario.recover_fn(ctx)
            outcome.resumed = scenario.resume_fn(ctx)
            ok = outcome.detect and outcome.contain and outcome.recovered and outcome.resumed
            if not ok:
                outcome.status = ScenarioStatus.FAIL
                outcome.error = (
                    f"detect={outcome.detect} contain={outcome.contain} "
                    f"recover={outcome.recovered} resume={outcome.resumed}"
                )
        except Exception as exc:  # noqa: BLE001 — scenario fail không crash suite
            outcome.status = ScenarioStatus.FAIL
            outcome.error = f"{type(exc).__name__}: {exc}"
        return outcome

    def run_all(self, ctx: dict[str, Any] | None = None) -> list[ScenarioOutcome]:
        return [self.run(sc, ctx) for sc in self.matrix.all()]
