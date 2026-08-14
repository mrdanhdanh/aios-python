"""Benchmark runner (TASK-033, H4): deterministic, run_fn injectable."""

from __future__ import annotations

from typing import Callable

from .contracts import RunResult


class BenchmarkRunner:
    """Chạy scenario_ids qua run_fn (duck-typed — không chạy workflow thật)."""

    def __init__(self, run_fn: Callable[[str], RunResult], *,
                 max_scenarios: int = 100) -> None:
        self._run_fn = run_fn
        self._max_scenarios = max_scenarios

    def run(self, scenario_ids: list[str]) -> tuple[list[RunResult], dict]:
        ids = sorted(set(scenario_ids))[: self._max_scenarios]  # deterministic
        results = [self._run_fn(scenario_id) for scenario_id in ids]
        return results, _aggregate(results)


def _aggregate(results: list[RunResult]) -> dict:
    if not results:
        return {"quality": 0.0, "cost": 0.0, "latency": 0.0, "token": 0,
                "failure_rate": 0.0, "policy_violations": 0.0,
                "scenarios": 0}
    total = len(results)
    return {
        "quality": sum(r.quality for r in results) / total,
        "cost": sum(r.cost for r in results) / total,
        "latency": sum(r.latency_ms for r in results) / total,
        "token": sum(r.tokens for r in results) / total,
        "failure_rate": sum(1 for r in results if r.failed) / total,
        "policy_violations": sum(r.policy_violations for r in results) / total,
        "scenarios": total,
    }
