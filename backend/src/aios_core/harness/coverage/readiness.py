"""Harness Readiness scorer (M13-P1, TASK-090).

7 dimensions (PLAN §M13-6) deterministic từ coverage + hard gates.
Fail-closed (P1-1 v1): replay gate 0.5 < 0.75 → NOT_READY cho tới khi
TASK-091 cover đủ negative-path + replay.
"""

from __future__ import annotations

from ..doctor.contracts import HardGate
from .contracts import (
    HarnessCoverageReport,
    HarnessReadinessReport,
    HarnessReadinessStatus,
    NegativePath,
)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


class HarnessReadinessScorer:
    """Thuần — score coverage → readiness (deterministic)."""

    def __init__(
        self,
        *,
        min_overall: float = 0.8,
        min_replay: float = 0.75,
        production_tests_available: bool = False,  # P2-C v2: v1 luôn 0.0
    ) -> None:
        for name, value in (("min_overall", min_overall),
                            ("min_replay", min_replay)):
            if not 0.0 < value <= 1.0:  # AC19 (P2-H v2)
                raise ValueError(f"{name} must be in (0, 1], got {value}")
        self._min_overall = min_overall
        self._min_replay = min_replay
        self._production_available = production_tests_available

    def score(self, coverage: HarnessCoverageReport) -> HarnessReadinessReport:
        d = coverage.dimensions
        component = d["component"].ratio
        contract = d["contract"].ratio
        state = d["state"].ratio
        transition = d["transition"].ratio
        event = d["event"].ratio
        failure_mode = d["failure_mode"].ratio
        scenario = d["scenario"].ratio
        verification_path = d["verification_path"].ratio
        artifact = d["artifact"].ratio
        neg = coverage.negative_paths

        def neg_ratio(*paths: NegativePath) -> float:
            covered = sum(1 for p in paths if neg[p.value].covered)
            return covered / len(paths)

        structural = _mean([component, contract])
        behavioral = _mean([scenario, verification_path])
        failure = _mean([failure_mode, neg_ratio(NegativePath.FAIL),
                         neg_ratio(NegativePath.EXCEPTION),
                         neg_ratio(NegativePath.TIMEOUT)])
        replay = _mean([verification_path,
                        neg_ratio(NegativePath.REPLAY_MISMATCH)])
        scenario_dim = _mean([scenario, coverage.negative_path_ratio])
        # P1-2 v1 + P2-C v2: v1 production = 0.0 bất kể available
        # (chưa có nguồn evidence — M13.1/M16 sẽ định nghĩa)
        production = 0.0

        dimensions = {
            "structural": structural,
            "contract": contract,
            "behavioral": behavioral,
            "failure": failure,
            "replay": replay,
            "scenario": scenario_dim,
            "production": production,
        }
        # overall = mean 6 dims active (production excluded v1 — P1-2 v1)
        active = [structural, contract, behavioral, failure, replay,
                  scenario_dim]
        overall = _mean(active)

        gates: list[HardGate] = []
        replay_ok = replay >= self._min_replay
        gates.append(HardGate(
            name="replay",
            passed=replay_ok,
            detail=(f"replay {replay:.3f} >= {self._min_replay}"
                    if replay_ok else
                    f"replay {replay:.3f} < {self._min_replay} "
                    f"(REPLAY_MISMATCH chưa cover — cần TASK-091)")))
        if self._production_available:  # conditional (P1-2 v1)
            production_ok = production >= 0.5
            gates.append(HardGate(
                name="production",
                passed=production_ok,
                detail=f"production {production:.3f} >= 0.5"))
        overall_ok = overall >= self._min_overall
        gates.append(HardGate(
            name="overall",
            passed=overall_ok,
            detail=f"overall {overall:.3f} >= {self._min_overall}"))

        ready = all(g.passed for g in gates)
        summary = (
            f"READY (overall {overall:.1%})" if ready else
            f"NOT READY (overall {overall:.1%}, replay {replay:.2f})"
        )
        return HarnessReadinessReport(
            dimensions=dimensions,
            overall=overall,
            status=HarnessReadinessStatus.READY if ready
            else HarnessReadinessStatus.NOT_READY,
            hard_gates=gates,
            summary=summary,
            metrics={
                "dimensions_active": len(active),
                "hard_gates_total": len(gates),
                "hard_gates_passed": sum(1 for g in gates if g.passed),
                "production_tests_available": self._production_available,
            },
            reproducible={
                "min_overall": self._min_overall,
                "min_replay": self._min_replay,
                "production_tests_available": self._production_available,
                "state_ratio": state,
                "transition_ratio": transition,
                "event_ratio": event,
                "artifact_ratio": artifact,
            },
        )