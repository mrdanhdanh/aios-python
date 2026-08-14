"""Benchmark package (TASK-033, H4)."""

from .contracts import (
    Baseline, BenchmarkMetric, BenchmarkReport, RegressionFinding,
    RegressionRule, RunResult,
)
from .errors import BenchmarkError, GateBlockedError
from .runner import BenchmarkRunner
from .gate import RegressionGate, default_rules
from .benchmark import BenchmarkHarness

__all__ = [
    "Baseline", "BenchmarkMetric", "BenchmarkReport", "RegressionFinding",
    "RegressionRule", "RunResult",
    "BenchmarkError", "GateBlockedError",
    "BenchmarkRunner", "RegressionGate", "default_rules", "BenchmarkHarness",
]
