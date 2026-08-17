"""Harness Coverage builder (M13-P1, TASK-090).

Auto-collect từ code thật (registry/lifecycle/verdict/faults/GOLDEN_SCENARIOS)
+ declared lists có evidence kiểm chứng tồn tại (module → find_spec;
path → anchored backend root, cwd-independent — P1-A v2). KHÔNG quét test
files (test count ≠ coverage). KHÔNG import os/sqlite3/httpx/socket/
requests (INV-020b precedent) — dùng importlib.util + pathlib.
"""

from __future__ import annotations

import importlib.util
import platform
from pathlib import Path

import importlib.metadata
import importlib.util
import platform
from pathlib import Path

from ..certification.golden import GOLDEN_SCENARIOS
from ..execution.contracts import Verdict
from ..lifecycle import TRANSITIONS
from ..registry import HarnessRegistry
from .contracts import (
    CoverageDimension,
    CoverageItem,
    DimensionCoverage,
    HarnessCoverageReport,
    NegativePath,
    NegativePathCoverage,
)

#: backend root (coverage.py → harness → aios_core → src → backend) — anchor
#: path evidence cwd-independent (P1-A v2). KHÔNG import aios_core root
#: (layer rule — arch-health cấm sub-package import root).
BACKEND_ROOT = Path(__file__).resolve().parents[4]


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001 — dev/editable install
        return "unknown"


def _module_ok(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _path_ok(rel: str) -> bool:
    return (BACKEND_ROOT / rel).exists()


def _evidence_ok(evidence: str) -> bool:
    """covered=True → evidence non-empty + tồn tại (P2-5 v1, P1-A v2)."""
    if not evidence:
        return False
    if evidence.startswith("module:"):
        return _module_ok(evidence[len("module:"):])
    if evidence.startswith("path:"):
        return _path_ok(evidence[len("path:"):])
    return False


#: 21 contract classes (P2-2 v1) — id → (module, covered-evidence)
_CONTRACT_ITEMS: tuple[tuple[str, str], ...] = (
    ("Check", "aios_core.harness.execution"),
    ("CheckResult", "aios_core.harness.execution"),
    ("VerificationTask", "aios_core.harness.execution"),
    ("Verdict", "aios_core.harness.execution"),
    ("Scenario", "aios_core.harness.testing"),
    ("ExpectedResult", "aios_core.harness.testing"),
    ("Fault", "aios_core.harness.testing"),
    ("SimulationOutcome", "aios_core.harness.testing"),
    ("GoldenScenario", "aios_core.harness.certification"),
    ("ConformanceConfig", "aios_core.harness.behavioral"),
    ("ConformanceReport", "aios_core.harness.behavioral"),
    ("DoctorResult", "aios_core.harness.doctor"),
    ("ReadinessReport", "aios_core.harness.doctor"),
    ("Baseline", "aios_core.harness.benchmark"),
    ("RunResult", "aios_core.harness.benchmark"),
    ("BenchmarkReport", "aios_core.harness.benchmark"),
    ("HarnessRun", "aios_core.harness"),
    ("HarnessResult", "aios_core.harness"),
    ("HarnessReport", "aios_core.harness"),
    ("HarnessArtifact", "aios_core.harness"),
    ("HarnessEvent", "aios_core.harness"),
)

#: 6 event phases thật runner emit (P2-A v2) — status.value
_EVENT_PHASES = ("preparing", "validating", "running", "verifying",
                 "completed", "failed")

#: 2 artifact kinds thật (P2-B v2) — runner _build_evidence
_ARTIFACT_KINDS = ("events", "report")

#: 8 verification-path items (P2-6 v1 + P3-C v2): Verdict 4 + VerificationState 8
_VERIFICATION_STATES = ("pass", "fail", "error", "blocked", "unknown",
                        "not_executed", "missing_evidence", "skipped")

#: negative-path — TASK-091 (meta) cover CORRUPTED_EVIDENCE + REPLAY_MISMATCH
_NEGATIVE_PATHS: tuple[tuple[NegativePath, bool, str], ...] = (
    (NegativePath.PASS, True, "module:aios_core.harness.testing"),
    (NegativePath.FAIL, True, "module:aios_core.harness.execution"),
    (NegativePath.BLOCKED, True, "module:aios_core.harness.benchmark"),
    (NegativePath.VIOLATION, True, "path:tests/test_architecture.py"),
    (NegativePath.TIMEOUT, True, "module:aios_core.harness.testing"),
    (NegativePath.EXCEPTION, True, "module:aios_core.harness"),
    (NegativePath.CORRUPTED_EVIDENCE, True, "module:aios_core.harness.meta"),
    (NegativePath.REPLAY_MISMATCH, True, "module:aios_core.harness.meta"),
)


#: harness id → module evidence (sub-package thật chứa harness class)
_COMPONENT_MODULES: dict[str, str] = {
    "verification": "aios_core.harness.execution",
    "test": "aios_core.harness.testing",
    "evaluation": "aios_core.harness.evaluation",
    "benchmark": "aios_core.harness.benchmark",
    "doctor": "aios_core.harness.doctor",
    "readiness": "aios_core.harness.doctor",  # ReadinessHarness trong doctor pkg
    "behavioral": "aios_core.harness.behavioral",
    "meta": "aios_core.harness.meta",  # P2-5: TASK-091 meta harness
}


class HarnessCoverage:
    """Thuần — build coverage report từ registry + code contracts."""

    def __init__(self, registry: HarnessRegistry) -> None:
        self._registry = registry

    # -- public --------------------------------------------------------------

    def build(self) -> HarnessCoverageReport:
        items: list[CoverageItem] = []
        items.extend(self._component_items())
        items.extend(self._contract_items())
        items.extend(self._state_items())
        items.extend(self._transition_items())
        items.extend(self._event_items())
        items.extend(self._failure_mode_items())
        items.extend(self._scenario_items())
        items.extend(self._verification_path_items())
        items.extend(self._artifact_items())

        # Fail-closed (P2-5 v1 + P1-A v2): covered=True mà evidence không tồn
        # tại → hạ xuống covered=False (không tự chứng nhận bằng evidence ảo).
        downgraded: list[str] = []
        checked: list[CoverageItem] = []
        for item in items:
            if item.covered and not _evidence_ok(item.evidence):
                downgraded.append(item.id)
                item = item.model_copy(update={"covered": False})
            checked.append(item)
        items = checked

        dimensions: dict[str, DimensionCoverage] = {}
        for dim in CoverageDimension:
            dim_items = [i for i in items if i.dimension == dim]
            covered = sum(1 for i in dim_items if i.covered)
            total = len(dim_items)
            dimensions[dim.value] = DimensionCoverage(
                dimension=dim,
                total=total,
                covered=covered,
                ratio=(covered / total if total else 0.0),  # không div0 (AC15)
            )

        negative_paths: dict[str, NegativePathCoverage] = {}
        for p, cov, ev in _NEGATIVE_PATHS:
            if cov and not _evidence_ok(ev):
                cov = False
                ev = ""
            negative_paths[p.value] = NegativePathCoverage(
                path=p, covered=cov, evidence=ev)
        negative_covered = sum(1 for n in negative_paths.values() if n.covered)
        negative_total = len(negative_paths)

        ratios = [d.ratio for d in dimensions.values()]
        overall = sum(ratios) / len(ratios) if ratios else 0.0
        summary = (
            f"{sum(1 for d in dimensions.values() if d.covered == d.total)}/"
            f"{len(dimensions)} dimensions fully covered, "
            f"negative {negative_covered}/{negative_total}"
        )
        if downgraded:
            summary += " — evidence invalid, downgraded: " + ", ".join(downgraded[:5])
        return HarnessCoverageReport(
            dimensions=dimensions,
            negative_paths=negative_paths,
            overall_ratio=overall,
            negative_path_ratio=(
                negative_covered / negative_total if negative_total else 0.0
            ),
            metrics={
                "items_total": len(items),
                "items_covered": sum(1 for i in items if i.covered),
                "dimensions_total": len(dimensions),
                "negative_paths_total": negative_total,
                "negative_paths_covered": negative_covered,
            },
            summary=summary,
            reproducible={
                "aios_version": _aios_version(),
                "registry_harness_ids": sorted(self._registry.list()),
                "python_version": platform.python_version(),
            },
        )

    # -- collectors ----------------------------------------------------------

    def _component_items(self) -> list[CoverageItem]:
        """7 harness — exclude self id="coverage" (P1-3 v1, P2-G v2)."""
        return [
            CoverageItem(
                dimension=CoverageDimension.COMPONENT,
                id=h_id,
                covered=True,
                evidence=f"module:{_COMPONENT_MODULES.get(h_id, 'aios_core.harness')}",
            )
            for h_id in self._registry.list()
            if h_id != "coverage"
        ]

    @staticmethod
    def _contract_items() -> list[CoverageItem]:
        return [
            CoverageItem(dimension=CoverageDimension.CONTRACT, id=cid,
                         covered=True, evidence=f"module:{mod}")
            for cid, mod in _CONTRACT_ITEMS
        ]

    @staticmethod
    def _state_items() -> list[CoverageItem]:
        """14: HarnessRunStatus 8 + ConformanceStatus 3 + SimulationStatus 3
        (P2-6 v1 — Verdict tách sang verification-path)."""
        from ..behavioral.contracts import ConformanceStatus
        from ..testing.contracts import SimulationStatus

        ids = ([s.value for s in TRANSITIONS]  # 8 HarnessRunStatus keys
               + [s.value for s in ConformanceStatus]
               + [s.value for s in SimulationStatus])
        return [
            CoverageItem(dimension=CoverageDimension.STATE, id=sid,
                         covered=True,
                         evidence="module:aios_core.harness.lifecycle")
            for sid in ids
        ]

    @staticmethod
    def _transition_items() -> list[CoverageItem]:
        """12 edges (P3-A v2) — mỗi edge = f"{src}->{dst}"."""
        edges = [
            f"{src.value}->{dst.value}"
            for src, targets in TRANSITIONS.items()
            for dst in targets
        ]
        return [
            CoverageItem(dimension=CoverageDimension.TRANSITION, id=edge,
                         covered=True,
                         evidence="module:aios_core.harness.lifecycle")
            for edge in edges
        ]

    @staticmethod
    def _event_items() -> list[CoverageItem]:
        return [
            CoverageItem(dimension=CoverageDimension.EVENT, id=phase,
                         covered=True,
                         evidence="module:aios_core.harness.runner")
            for phase in _EVENT_PHASES
        ]

    @staticmethod
    def _failure_mode_items() -> list[CoverageItem]:
        """8 (P3-B v2): FaultType 3 + HarnessError subclasses 5."""
        from ..errors import (
            HarnessError,
            HarnessHookError,
            HarnessLifecycleError,
            HarnessNotFoundError,
            HarnessRegistrationError,
        )
        from ..testing.contracts import FaultType

        ids = [f.value for f in FaultType] + [
            c.__name__ for c in (
                HarnessError, HarnessRegistrationError, HarnessNotFoundError,
                HarnessLifecycleError, HarnessHookError,
            )
        ]
        return [
            CoverageItem(dimension=CoverageDimension.FAILURE_MODE, id=i,
                         covered=True,
                         evidence="module:aios_core.harness")
            for i in ids
        ]

    @staticmethod
    def _scenario_items() -> list[CoverageItem]:
        return [
            CoverageItem(dimension=CoverageDimension.SCENARIO, id=gs.gs_id,
                         covered=True,
                         evidence="module:aios_core.harness.certification")
            for gs in GOLDEN_SCENARIOS
        ]

    @staticmethod
    def _verification_path_items() -> list[CoverageItem]:
        ids = [v.value for v in Verdict] + list(_VERIFICATION_STATES)
        return [
            CoverageItem(dimension=CoverageDimension.VERIFICATION_PATH, id=i,
                         covered=True,
                         evidence="module:aios_core.harness.execution")
            for i in ids
        ]

    @staticmethod
    def _artifact_items() -> list[CoverageItem]:
        return [
            CoverageItem(dimension=CoverageDimension.ARTIFACT, id=kind,
                         covered=True,
                         evidence="module:aios_core.harness.runner")
            for kind in _ARTIFACT_KINDS
        ]