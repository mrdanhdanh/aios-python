"""Performance & Cost — M10-F4 (TASK-075).

Đo latency · throughput · concurrency · storage + Cost/Goal · Cost/Workflow ·
Cost/Agent · Cost/Tool · Cost/Success (PLAN §M10-35). Offline-first: token
estimate injectable; DB rỗng → 0/SKIPPED (không crash).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Performance metrics
# ---------------------------------------------------------------------------

@dataclass
class PerformanceSnapshot:
    avg_workflow_latency_ms: float = 0.0
    avg_tool_latency_ms: float = 0.0
    throughput_per_minute: float = 0.0
    max_concurrency: int = 0
    storage_bytes: int = 0
    workflow_count: int = 0
    tool_count: int = 0


class PerformanceMetrics:
    """Đo từ MetricsService + artifact dir (pure python — không du)."""

    def __init__(
        self,
        metrics_svc: Any | None = None,
        artifact_dir: str = "aios/data/artifacts",
    ) -> None:
        self._metrics = metrics_svc
        self._artifact_dir = artifact_dir

    def snapshot(self) -> PerformanceSnapshot:
        snap = PerformanceSnapshot()
        try:
            if self._metrics is not None:
                summary = self._metrics.summary()
                counts = summary["counts"]
                snap.workflow_count = counts.get("workflow", 0)
                snap.tool_count = counts.get("tool", 0)
                avg_w = summary["avg_duration_ms"]["workflow"]
                avg_t = summary["avg_duration_ms"]["tool"]
                snap.avg_workflow_latency_ms = avg_w or 0.0
                snap.avg_tool_latency_ms = avg_t or 0.0
                # throughput: completed gần đây / 1 phút (estimate từ recent)
                recent = self._metrics.recent(limit=100)
                finished = [r for r in recent if r.get("duration_ms") is not None]
                if finished:
                    window_s = max(
                        (r.get("duration_ms", 0) / 1000.0 for r in finished), default=1.0
                    )
                    snap.throughput_per_minute = round(
                        len(finished) * 60.0 / max(window_s, 0.001), 2
                    )
        except Exception:  # noqa: BLE001 — DB rỗng/thiếu → 0
            pass
        snap.storage_bytes = self._dir_size(self._artifact_dir)
        return snap

    @staticmethod
    def _dir_size(path: str) -> int:
        import os

        total = 0
        try:
            for root, _dirs, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
        except OSError:
            return 0
        return total


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------

class TokenEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str
    tokens_in: int = 0
    tokens_out: int = 0


class CostEstimator:
    """Model cost = tokens/1M × cost_per_1M (ModelCapability) + tool cost."""

    def __init__(
        self,
        capabilities: Callable[[str], Any] | None = None,
        tool_cost_per_call: float = 0.001,
    ) -> None:
        # capabilities(model_id) → ModelCapability (cost fields) — injectable
        self._capabilities = capabilities or (lambda m: None)
        self.tool_cost_per_call = tool_cost_per_call

    def model_cost(self, estimate: TokenEstimate) -> float:
        cap = self._capabilities(estimate.model_id)
        if cap is None:
            return 0.0
        input_cost = (estimate.tokens_in / 1_000_000.0) * cap.input_cost
        output_cost = (estimate.tokens_out / 1_000_000.0) * cap.output_cost
        return round(input_cost + output_cost, 8)

    def tool_cost(self, tool_calls: int) -> float:
        return round(tool_calls * self.tool_cost_per_call, 8)


@dataclass
class CostDashboard:
    cost_per_workflow: dict[str, float] = field(default_factory=dict)
    cost_per_agent: dict[str, float] = field(default_factory=dict)
    cost_per_tool: dict[str, float] = field(default_factory=dict)
    cost_per_goal: dict[str, float] = field(default_factory=dict)
    cost_per_success: float | None = None
    total_cost: float = 0.0


class CostAggregator:
    """Aggregate theo Workflow/Agent/Tool/Success/Goal."""

    def __init__(
        self,
        estimator: CostEstimator,
        token_estimates: list[TokenEstimate] | None = None,
        tool_calls_by_tool: dict[str, int] | None = None,
        workflow_success: dict[str, tuple[int, int]] | None = None,
        goal_workflows: dict[str, list[str]] | None = None,
    ) -> None:
        self.estimator = estimator
        self.token_estimates = token_estimates or []
        self.tool_calls_by_tool = tool_calls_by_tool or {}
        # workflow_name → (success, total)
        self.workflow_success = workflow_success or {}
        self.goal_workflows = goal_workflows or {}

    def build(self) -> CostDashboard:
        dash = CostDashboard()
        model_total = sum(self.estimator.model_cost(t) for t in self.token_estimates)
        # cost per workflow: model tokens theo workflow (estimate gán workflow qua
        # token estimate nếu model_id có dạng "<workflow>:<model>") — v1 đơn giản:
        # gom toàn bộ vào "total"; per-workflow từ workflow_success success cost.
        for wf, (success, total) in self.workflow_success.items():
            dash.cost_per_workflow[wf] = round(
                (model_total * success / max(total, 1)), 8
            )
        tool_total = sum(
            self.estimator.tool_cost(n) for n in self.tool_calls_by_tool.values()
        )
        for tool, calls in self.tool_calls_by_tool.items():
            dash.cost_per_tool[tool] = self.estimator.tool_cost(calls)
        for goal, workflows in self.goal_workflows.items():
            dash.cost_per_goal[goal] = round(
                sum(dash.cost_per_workflow.get(w, 0.0) for w in workflows), 8
            )
        total_success = sum(s for s, _ in self.workflow_success.values())
        dash.total_cost = round(model_total + tool_total, 8)
        if total_success > 0:
            dash.cost_per_success = round(dash.total_cost / total_success, 8)
        return dash
