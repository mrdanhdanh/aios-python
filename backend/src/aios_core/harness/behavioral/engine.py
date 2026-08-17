"""Behavioral Conformance engine (M13-P0, TASK-089).

Chạy scenario N lần (profile: quick=100/standard=1k/stress=10k/soak=duration)
+ repeat (double-run) + fault-inject + evidence compare (sha256 digest) +
regression gate (chỉ expose). Tái dùng SimulationRunner (deterministic,
không side-effect) + RegressionGate — không tạo hệ thống song song.

Không import sqlite3/httpx/socket/requests/os (INV-020b precedent —
simulation thuần).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

from ..benchmark.contracts import Baseline, RunResult
from ..benchmark.gate import RegressionGate
from ..testing.contracts import Fault, Scenario, SimulationStatus
from ..testing.simulation import SimulationRunner
from .contracts import (
    ConformanceConfig,
    ConformanceIterationSummary,
    ConformanceProfile,
    ConformanceReport,
    ConformanceStatus,
)
from .errors import BehavioralConformanceError

PROFILE_ITERATIONS: dict[ConformanceProfile, int] = {
    ConformanceProfile.QUICK: 100,
    ConformanceProfile.STANDARD: 1000,
    ConformanceProfile.STRESS: 10000,
}


def _digest(outcome: Any) -> str:
    """sha256 của outcome — deterministic (sort_keys + compact separators)."""
    payload = json.dumps(
        outcome.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class BehavioralConformanceEngine:
    """Thuần (không state) — mỗi run() tạo report mới."""

    def __init__(
        self,
        runner: SimulationRunner | None = None,
        *,
        soak_max_iterations: int = 10000,  # cap từ constructor (P2-3 v1)
    ) -> None:
        self._runner = runner or SimulationRunner()
        self._soak_max_iterations = soak_max_iterations

    # -- public --------------------------------------------------------------

    def run(self, config: ConformanceConfig) -> ConformanceReport:
        iterations = self._resolve_iterations(config)
        repeat_samples = min(config.repeat_samples, iterations)  # P1-2 v2
        self._validate_fault_schedule(config, iterations)  # P2-3 v2 fail-fast

        summaries: list[ConformanceIterationSummary] = []
        findings: list[str] = []
        fault_injected_total = 0
        recovery_total = 0
        mismatch_count = 0
        error_count = 0
        repeat_runs = 0
        policy_violations_total = 0
        no_fault_digests: set[str] = set()
        has_no_fault_group = False

        for i in range(1, iterations + 1):
            has_fault = self._iteration_has_fault(config, i)
            scenario = self._scenario_for(config, has_fault)
            outcome = self._runner.run(scenario)
            digest = _digest(outcome)
            repeat_ok: bool | None = None
            if i <= repeat_samples:
                repeat_runs += 1
                replay = self._runner.run(scenario)
                repeat_ok = replay.model_dump() == outcome.model_dump()

            if has_fault:
                fault_injected_total += len(outcome.faults_injected)
                recovery_total += len(outcome.recovery_events)
            else:
                has_no_fault_group = True
                no_fault_digests.add(digest)

            if outcome.status == SimulationStatus.MISMATCH:
                mismatch_count += 1
            elif outcome.status == SimulationStatus.ERROR:
                error_count += 1
            if not outcome.verification.get("no_policy_bypass", True):
                policy_violations_total += 1

            summaries.append(ConformanceIterationSummary(
                index=i,
                status=outcome.status,
                evidence_digest=digest,
                repeat_ok=repeat_ok,
                fault_injected=has_fault,
                recovered=has_fault and len(outcome.recovery_events) > 0,
            ))

        # -- phân tích --------------------------------------------------------
        deterministic = len(no_fault_digests) <= 1  # P3-6 v1: digest nhóm không-fault
        if not has_no_fault_group:
            # R8: mọi iteration đều fault → deterministic vacuous
            findings.append("deterministic vacuous: no fault-free iteration group")
        repeat_consistent = all(
            s.repeat_ok is not False for s in summaries if s.repeat_ok is not None
        ) or repeat_runs == 0
        recovery_rate = (
            recovery_total / fault_injected_total if fault_injected_total else 0.0
        )

        # Hành vi ĐÚNG (P1-1 v1): mọi outcome không-fault phải SUCCESS
        behavior_ok = True
        for s in summaries:
            if not s.fault_injected and s.status != SimulationStatus.SUCCESS:
                behavior_ok = False
                findings.append(
                    f"iteration {s.index}: non-fault outcome status={s.status.value}"
                )

        status = ConformanceStatus.PASS
        if error_count > 0:
            status = ConformanceStatus.ERROR
            findings.append(f"{error_count} iteration(s) ERROR (fault not recovered)")
        elif mismatch_count > 0:
            status = ConformanceStatus.FAIL
            findings.append(f"{mismatch_count} iteration(s) MISMATCH (expectation wrong)")
        elif not behavior_ok:
            status = ConformanceStatus.FAIL
            findings.append("non-fault outcome(s) not SUCCESS")
        elif not deterministic:
            status = ConformanceStatus.FAIL
            findings.append("non-deterministic: evidence digests differ across runs")
        elif not repeat_consistent:
            status = ConformanceStatus.FAIL
            findings.append("repeat mismatch: double-run outcomes differ")

        # -- regression gate (P1-3 v1 + P1-1 v2): chỉ expose ------------------
        gate = None
        if config.baseline is not None:
            run_result = self._aggregate_run_result(
                summaries, config.scenario.id, policy_violations_total
            )
            gate = RegressionGate().evaluate([run_result], config.baseline)
            if gate.gate_passed is False:
                findings.append(f"regression gate blocked: {gate.summary}")

        metrics = {
            "iterations_total": iterations,
            "faults_injected_total": fault_injected_total,
            "recovery_events_total": recovery_total,
            "repeat_runs": repeat_runs,
            "mismatch_count": mismatch_count,
            "error_count": error_count,
            "policy_violations_total": policy_violations_total,
        }
        summary = (
            f"{status.value}: {iterations} iterations, "
            f"deterministic={deterministic}, repeat={repeat_consistent}, "
            f"recovery_rate={recovery_rate:.2f}"
        )
        return ConformanceReport(
            profile=config.profile,
            scenario_id=config.scenario.id,
            iterations_total=iterations,
            status=status,
            deterministic=deterministic,
            repeat_consistent=repeat_consistent,
            fault_recovery_rate=recovery_rate,
            iterations=summaries,
            metrics=metrics,
            findings=findings,
            gate=gate,
            summary=summary,
            reproducible={
                "profile": config.profile.value,
                "scenario_id": config.scenario.id,
                "iterations": iterations,
                "faults": [f.model_dump(mode="json") for f in config.faults],
                "fault_iterations": list(config.fault_iterations),
                "baseline_version": (
                    config.baseline.version if config.baseline else None
                ),
            },
        )

    # -- helpers -------------------------------------------------------------

    def build_baseline(self, report: ConformanceReport, *,
                       version: str = "v1") -> Baseline:
        """P3-4 v1 + P1-1 v2: gộp report → Baseline (dùng cho --save-baseline)."""
        run_result = self._aggregate_run_result(
            report.iterations, report.scenario_id,
            int(report.metrics.get("policy_violations_total", 0)),
        )
        return Baseline(version=version, runs={report.scenario_id: run_result})

    def _resolve_iterations(self, config: ConformanceConfig) -> int:
        if config.iterations is not None:
            return config.iterations  # override thắng soak (P3-3 v1)
        if config.profile == ConformanceProfile.SOAK:
            return self._soak_iterations(config)
        return PROFILE_ITERATIONS[config.profile]

    def _soak_iterations(self, config: ConformanceConfig) -> int:
        """Soak: chạy tối thiểu 1, tối đa soak_max_iterations, dừng khi hết
        duration. duration_s=0 → 1 iteration. Soak v1 = loop-stability test
        (runner thuần không resource/timing — P2-3 v1)."""
        if config.duration_s <= 0:
            return 1
        deadline = time.monotonic() + config.duration_s
        count = 0
        while time.monotonic() < deadline and count < self._soak_max_iterations:
            count += 1
        return max(1, count)

    @staticmethod
    def _validate_fault_schedule(config: ConformanceConfig, iterations: int) -> None:
        """P2-3 v2: fault_iterations out-of-range → fail-fast (không fail im lặng)."""
        for idx in config.fault_iterations:
            if idx > iterations:
                raise BehavioralConformanceError(
                    f"fault_iterations index {idx} > iterations_total {iterations}"
                )

    @staticmethod
    def _iteration_has_fault(config: ConformanceConfig, index: int) -> bool:
        if not config.faults:
            return False
        if config.fault_iterations:
            return index in config.fault_iterations
        return True  # faults áp mọi iteration

    @staticmethod
    def _scenario_for(config: ConformanceConfig, has_fault: bool) -> Scenario:
        faults = config.faults if has_fault else []
        return config.scenario.model_copy(update={"faults": faults})

    @staticmethod
    def _aggregate_run_result(
        summaries: list[ConformanceIterationSummary],
        scenario_id: str,
        policy_violations: int,
    ) -> RunResult:
        """P1-1 v2: gộp N iteration → 1 RunResult/scenario.

        quality = tỷ lệ iteration SUCCESS; failed = có bất kỳ iteration fail;
        policy_violations = số iteration có policy bypass; cost/tokens/latency = 0.
        """
        total = len(summaries)
        success = sum(1 for s in summaries if s.status == SimulationStatus.SUCCESS)
        failed = any(s.status != SimulationStatus.SUCCESS for s in summaries)
        return RunResult(
            scenario_id=scenario_id,
            quality=success / total if total else 0.0,
            cost=0.0,
            latency_ms=0.0,
            tokens=0,
            failed=failed,
            policy_violations=policy_violations,
        )