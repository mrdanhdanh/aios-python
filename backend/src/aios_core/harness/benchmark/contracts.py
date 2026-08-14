"""Benchmark contracts (TASK-033, H4): metrics, baseline, regression gate."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class BenchmarkMetric(str, Enum):
    """6 metrics theo dõi đồng thời (PLAN §H4/TASK-033)."""

    QUALITY = "quality"
    COST = "cost"
    LATENCY = "latency"
    TOKEN = "token"
    FAILURE_RATE = "failure_rate"
    POLICY_VIOLATIONS = "policy_violations"


class RunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str
    quality: float = 0.0
    cost: float = 0.0
    latency_ms: float = 0.0
    tokens: int = 0
    failed: bool = False
    policy_violations: int = 0


class Baseline(BaseModel):
    """Kết quả phiên trước — key scenario_id."""

    model_config = ConfigDict(extra="forbid")

    version: str = "v0"
    runs: dict[str, RunResult] = {}


class RegressionRule(BaseModel):
    """max_delta: % (quality/cost/latency/token) hoặc pp (failure_rate/
    policy_violations). Hướng xấu: quality giảm; còn lại tăng."""

    model_config = ConfigDict(extra="forbid")

    metric: BenchmarkMetric
    max_delta: float
    note: str = ""


class RegressionFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: BenchmarkMetric
    baseline_avg: float
    new_avg: float
    delta: float
    regressed: bool = False
    rule_note: str = ""


class BenchmarkReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baseline_version: str = "v0"
    scenarios_total: int = 0
    metrics: dict = {}  # aggregate avgs — deterministic (C2-04)
    findings: list[RegressionFinding] = []
    gate_passed: bool = True  # P1-01: baseline rỗng → không block
    summary: str = ""
    metrics_count: dict = {}  # P3-02: scenarios/findings/regressed
    reproducible: dict = {}  # P3-03: baseline_version
