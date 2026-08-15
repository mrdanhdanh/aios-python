"""Certification Suite 1.0 — contracts (M10-F5, TASK-073)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict


class CertificationArea(str, Enum):
    ARCHITECTURE = "architecture"
    CONTRACTS = "contracts"
    RUNTIME = "runtime"
    POLICY = "policy"
    SECURITY = "security"
    AUTONOMY = "autonomy"
    HARNESS = "harness"
    ENTERPRISE = "enterprise"
    ECOSYSTEM = "ecosystem"


class PassFail(str, Enum):
    PASS = "pass"
    FAIL = "fail"


@dataclass
class AreaResult:
    area: str
    status: PassFail
    evidence: str = ""


class GoldenScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gs_id: str  # GS-001 .. GS-020
    name: str
    category: str
    check_fn: Callable[[dict[str, Any]], bool]  # deterministic, ctx injectable
    description: str = ""


@dataclass
class ConformanceReport:
    areas: list[AreaResult] = field(default_factory=list)
    golden: list[tuple[str, bool]] = field(default_factory=list)  # (gs_id, pass)
    gates: dict[str, bool] = field(default_factory=dict)

    @property
    def areas_ready(self) -> bool:
        return all(a.status == PassFail.PASS for a in self.areas)

    @property
    def golden_ready(self) -> bool:
        return all(ok for _, ok in self.golden)

    @property
    def gates_ready(self) -> bool:
        return all(self.gates.values())

    @property
    def ready(self) -> bool:
        """AIOS 1.0 READY chỉ khi areas + golden + gates đều PASS (C2-03)."""
        return self.areas_ready and self.golden_ready and self.gates_ready

    def failures(self) -> list[str]:
        fails = [a.area for a in self.areas if a.status == PassFail.FAIL]
        fails += [gid for gid, ok in self.golden if not ok]
        fails += [g for g, ok in self.gates.items() if not ok]
        return fails
