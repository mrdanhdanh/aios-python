"""TASK-042 — Enterprise Operations + Dashboard (E7).

Aggregates tenant-level operational metrics from the audit store and other
enterprise subsystems into a dashboard view (PLAN §9 E7): executions, success
rate, token usage, cost, policy violations, latency. Dimensions follow the
enterprise observability model: tenant · project · user · agent · workflow ·
model · runtime · region.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .contracts import AuditEvent
from .operations import CentralAuditStore


class EnterpriseDashboard:
    """Builds a tenant operational dashboard from audit evidence (INV-027)."""

    def __init__(self, audit: CentralAuditStore) -> None:
        self.audit = audit

    def _by_tenant(self) -> dict[str, list[AuditEvent]]:
        grouped: dict[str, list[AuditEvent]] = defaultdict(list)
        for e in self.audit.list():
            grouped[e.tenant_id or "unknown"].append(e)
        return dict(grouped)

    def tenant_summary(self, tenant_id: str) -> dict[str, Any]:
        events = [e for e in self.audit.list() if (e.tenant_id or "") == tenant_id]
        total = len(events)
        success = sum(1 for e in events if e.result == "success")
        denied = sum(1 for e in events if e.result == "denied")
        violations = sum(1 for e in events if e.action == "policy.violation")
        executions = sum(1 for e in events if e.action == "execution.started")
        success_rate = (success / total) if total else 0.0
        agents = {e.agent_id for e in events if e.agent_id}
        workflows = {e.workflow_id for e in events if e.workflow_id}
        return {
            "tenant_id": tenant_id,
            "total_events": total,
            "executions": executions,
            "success": success,
            "denied": denied,
            "policy_violations": violations,
            "success_rate": round(success_rate, 4),
            "agents": sorted(a for a in agents if a),
            "workflows": sorted(w for w in workflows if w),
        }

    def overview(self) -> dict[str, Any]:
        by_tenant = self._by_tenant()
        return {
            "tenants": {t: self.tenant_summary(t) for t in by_tenant},
            "tenant_count": len(by_tenant),
        }
