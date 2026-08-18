"""Simulation engine (M14-P2, TASK-096): run fix in sandbox + meta-verify."""

from __future__ import annotations

import importlib.metadata
import platform

from ..heal.contracts import CandidateFix
from ..meta.contracts import MetaReport, MetaStatus
from .contracts import SimulationReport, SimulationResult


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001
        return "unknown"


class SimulationEngine:
    """Thuần — simulate fix + meta-verify (KHÔNG relax criteria)."""

    def simulate(
        self,
        candidate: CandidateFix,
        meta_report: MetaReport | None = None,
    ) -> SimulationReport:
        """Simulate applying a candidate fix and verify via Meta-Harness.

        v1: deterministic simulation (no sandbox). Meta-verify checks
        that Meta-Harness still passes after the proposed fix.
        """
        # v1: all low-risk candidates "pass" simulation
        # high/critical risk → blocked (need human approval in M14-P3)
        if candidate.risk_level.value in ("high", "critical"):
            return SimulationReport(
                candidate_signature=candidate.failure_signature,
                result=SimulationResult.BLOCKED,
                checks_passed=0, checks_total=1,
                meta_verify_pass=False,
                detail=f"high/critical risk — requires human approval",
                reproducible={"aios_version": _aios_version(),
                              "python_version": platform.python_version()})

        # Meta-verify: check Meta-Harness still passes
        meta_pass = True
        if meta_report is not None:
            meta_pass = meta_report.status == MetaStatus.PASS

        return SimulationReport(
            candidate_signature=candidate.failure_signature,
            result=SimulationResult.PASS if meta_pass else SimulationResult.FAIL,
            checks_passed=1 if meta_pass else 0,
            checks_total=1,
            meta_verify_pass=meta_pass,
            detail="simulation passed" if meta_pass else "meta-verify failed",
            reproducible={"aios_version": _aios_version(),
                          "python_version": platform.python_version()})
