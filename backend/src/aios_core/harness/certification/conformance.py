"""Certification Suite 1.0 — conformance runner + 5 release gates (M10-F5)."""

from __future__ import annotations

import tempfile
from typing import Any

from .checks import AreaChecks
from .contracts import ConformanceReport, GoldenScenario, PassFail
from .golden import GOLDEN_SCENARIOS


class ConformanceRunner:
    """9 areas + 20 GS + 5 release gates → AIOS 1.0 READY/NOT READY."""

    def __init__(self, kernel: Any | None = None) -> None:
        self.kernel = kernel
        self._ctx: dict[str, Any] = {"tmp_path": tempfile.mkdtemp(prefix="aios-gs-")}
        self._golden_cache: list[tuple[str, bool]] | None = None

    # -- 5 release gates (PLAN §M10-36) ---------------------------------------
    def release_gates(self) -> dict[str, bool]:
        gates: dict[str, bool] = {}
        # Gate A — Architecture: INV violations = 0
        try:
            from ...observability.arch_health import ArchitectureHealth

            scan = ArchitectureHealth().scan()
            gates["gate_a_architecture"] = bool(scan.healthy) and len(scan.violations) == 0
        except Exception:  # noqa: BLE001
            gates["gate_a_architecture"] = False
        # Gate B — Security: critical = 0, high = 0
        try:
            from ...security import SecurityChecker

            report = SecurityChecker().run()
            hard = [i for i in report.failures if i.severity.value in ("critical", "high")]
            gates["gate_b_security"] = not hard
        except Exception:  # noqa: BLE001
            gates["gate_b_security"] = False
        # Gate C — Contract: breaking compatibility = 0
        try:
            from ...contracts.check import ContractChecker

            gates["gate_c_contract"] = ContractChecker().check_all().breaking_count == 0
        except Exception:  # noqa: BLE001
            gates["gate_c_contract"] = False
        # Gate D — Reliability: critical scenario failures = 0 (GS 20/20 + SLO)
        try:
            from ...observability.slo import SloEngine

            engine = SloEngine()
            metrics = engine.metrics_from_runtime(self.kernel) if self.kernel is not None else {}
            slo_ok = engine.check(metrics).release_ready
            gs_ok = all(ok for _, ok in self._golden())
            gates["gate_d_reliability"] = gs_ok and slo_ok
        except Exception:  # noqa: BLE001
            gates["gate_d_reliability"] = False
        # Gate E — Autonomous: policy/budget/kill-switch bypass = 0
        try:
            from ...kernel.kill_switch import KillSwitch

            switch = None
            if self.kernel is not None:
                from ...container import Container

                if isinstance(self.kernel.container, Container):
                    try:
                        switch = self.kernel.container.resolve(KillSwitch)
                    except Exception:  # noqa: BLE001
                        switch = None
            ks_ok = switch is None or not switch.state.emergency
            gates["gate_e_autonomous"] = ks_ok and not slo_fail_any()
        except Exception:  # noqa: BLE001
            gates["gate_e_autonomous"] = False
        return gates

    def _golden(self) -> list[tuple[str, bool]]:
        if self._golden_cache is None:
            results = []
            for gs in GOLDEN_SCENARIOS:
                try:
                    ok = bool(gs.check_fn(self._ctx))
                except Exception:  # noqa: BLE001 — GS fail không crash suite
                    ok = False
                results.append((gs.gs_id, ok))
            self._golden_cache = results
        return self._golden_cache

    def run(self) -> ConformanceReport:
        areas = AreaChecks(self.kernel).run_all()
        golden = self._golden()
        gates = self.release_gates()
        return ConformanceReport(areas=areas, golden=golden, gates=gates)


def slo_fail_any() -> bool:
    """SLO có FAIL nào không (Gate E phụ)?"""
    try:
        from ...observability.slo import SloEngine

        return not SloEngine().check({}).release_ready
    except Exception:  # noqa: BLE001
        return False


def format_conformance(report: ConformanceReport) -> str:
    lines = ["AIOS Conformance 1.0", "=" * 50]
    for area in sorted(report.areas, key=lambda a: a.area):
        sym = "✓" if area.status == PassFail.PASS else "✗"
        lines.append(f"{sym} {area.area:<14} — {area.evidence}")
    lines.append("")
    failed_gs = [gid for gid, ok in report.golden if not ok]
    lines.append(f"Golden Scenarios: {len(report.golden) - len(failed_gs)}/{len(report.golden)} PASS"
                 + (f" (fail: {failed_gs})" if failed_gs else ""))
    lines.append("")
    for gate, ok in report.gates.items():
        lines.append(f"{'✓' if ok else '✗'} {gate}")
    lines.append("")
    if report.ready:
        lines.append("Result: AIOS 1.0 READY")
    else:
        lines.append(f"Result: AIOS 1.0 NOT READY (fail: {report.failures()})")
    return "\n".join(lines)
