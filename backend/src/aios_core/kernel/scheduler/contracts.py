"""Scheduler contracts (TASK-028): resource-gated scheduling result."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from aios_core.kernel.graph import GraphResult


class NodeResourceMetrics(BaseModel):
    """Per-node resource accounting (queue time — PLAN §25)."""

    model_config = ConfigDict(extra="forbid")

    resource_wait_ms: int = 0  # TOTAL wait time (all attempts — C2-01)
    slots_acquired: int = 0  # TOTAL successful acquires (incl. retries; under lock)


class ScheduledGraphResult(BaseModel):
    """028-owned result — wraps GraphResult (027), adds resource metrics."""

    model_config = ConfigDict(extra="forbid")

    execution_id: str
    graph: GraphResult
    node_metrics: dict[str, NodeResourceMetrics] = {}  # pre-init ALL node ids
    queue_time_ms: int = 0  # max(node_metrics.resource_wait_ms)
    peak_slots_used: int = 0  # peak scheduler-held slots (≠ ResourceService.stats().running)
    resource_stats: dict[str, Any] = {}  # ResourceService.stats() after run
