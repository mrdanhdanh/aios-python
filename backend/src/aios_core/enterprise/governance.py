"""TASK-039 — Enterprise Resource Governance (E5).

Enforces INV-025 (Resource Fairness): a tenant may not exceed its quota unless
a policy override is present. Implements AI-specific quotas (LLM tokens, tool
calls, sandbox seconds, concurrent executions) and cost governance
(Cost Estimator → Budget Policy → Execution → Actual Cost → Billing, PLAN §7 E5).

Budget decision: ``estimate > budget → DENY`` (or route to cheaper model when a
cheaper alternative is supplied, combining M5 Model Router + M7 Governance).
"""

from __future__ import annotations

import threading
from typing import Any

from .contracts import CostEstimate, Quota, ResourceUsage


class QuotaExceeded(Exception):
    """Raised when a tenant would exceed its quota (INV-025)."""


class BudgetExceeded(Exception):
    """Raised when estimated cost exceeds the tenant budget (PLAN §7 E5)."""


class QuotaManager:
    """Per-tenant quota accounting with fairness enforcement (INV-025)."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._quotas: dict[str, Quota] = {}
        self._usage: dict[str, ResourceUsage] = {}

    def set_quota(self, quota: Quota) -> None:
        with self._lock:
            self._quotas[quota.tenant_id] = quota
            if quota.tenant_id not in self._usage:
                self._usage[quota.tenant_id] = ResourceUsage(tenant_id=quota.tenant_id)

    def get_quota(self, tenant_id: str) -> Quota:
        with self._lock:
            if tenant_id not in self._quotas:
                return Quota(tenant_id=tenant_id)
            return self._quotas[tenant_id]

    def usage(self, tenant_id: str) -> ResourceUsage:
        with self._lock:
            return self._usage.setdefault(tenant_id, ResourceUsage(tenant_id=tenant_id))

    def can_start(self, tenant_id: str, override: bool = False) -> bool:
        """INV-025: deny if over concurrent-execution quota w/o override."""
        if override:
            return True
        with self._lock:
            quota = self._quotas.get(tenant_id, Quota(tenant_id=tenant_id))
            used = self._usage.get(tenant_id, ResourceUsage(tenant_id=tenant_id))
            return used.active_executions < quota.concurrent_executions

    def check_fairness(self, tenant_id: str, override: bool = False) -> None:
        """Raise ``QuotaExceeded`` if the tenant is over quota (INV-025)."""
        if not self.can_start(tenant_id, override=override):
            raise QuotaExceeded(
                f"INV-025: tenant {tenant_id!r} exceeds concurrent execution quota"
            )

    def begin(self, tenant_id: str, override: bool = False) -> None:
        self.check_fairness(tenant_id, override=override)
        with self._lock:
            self.usage(tenant_id).active_executions += 1

    def end(self, tenant_id: str) -> None:
        with self._lock:
            u = self.usage(tenant_id)
            u.active_executions = max(0, u.active_executions - 1)

    def add_tokens(self, tenant_id: str, n: int, override: bool = False) -> None:
        with self._lock:
            quota = self._quotas.get(tenant_id, Quota(tenant_id=tenant_id))
            u = self.usage(tenant_id)
            if not override and u.tokens_today + n > quota.llm_tokens_per_day:
                raise QuotaExceeded(
                    f"INV-025: tenant {tenant_id!r} exceeds token quota"
                )
            u.tokens_today += n

    def add_tool_calls(self, tenant_id: str, n: int, override: bool = False) -> None:
        with self._lock:
            quota = self._quotas.get(tenant_id, Quota(tenant_id=tenant_id))
            u = self.usage(tenant_id)
            if not override and u.tool_calls_today + n > quota.tool_calls_per_day:
                raise QuotaExceeded(
                    f"INV-025: tenant {tenant_id!r} exceeds tool-call quota"
                )
            u.tool_calls_today += n


class CostGovernor:
    """Cost Estimator + Budget Policy gate (PLAN §7 E5)."""

    def __init__(self, budgets: dict[str, float] | None = None) -> None:
        # tenant_id -> daily budget (USD)
        self._budgets: dict[str, float] = dict(budgets or {})
        self._spent: dict[str, float] = {}

    def set_budget(self, tenant_id: str, amount: float) -> None:
        self._budgets[tenant_id] = amount

    def estimate(self, model: str, tokens: int, unit_cost: float) -> CostEstimate:
        amount = round(tokens * unit_cost, 6)
        return CostEstimate(amount=amount, model=model, breakdown={"tokens": float(tokens)})

    def check_budget(self, tenant_id: str, estimate: CostEstimate) -> None:
        budget = self._budgets.get(tenant_id)
        if budget is None:
            return
        spent = self._spent.get(tenant_id, 0.0)
        if spent + estimate.amount > budget:
            raise BudgetExceeded(
                f"estimated ${estimate.amount:.4f} exceeds budget ${budget:.4f} "
                f"for tenant {tenant_id!r}"
            )

    def charge(self, tenant_id: str, estimate: CostEstimate) -> None:
        self._spent[tenant_id] = self._spent.get(tenant_id, 0.0) + estimate.amount

    def cheaper_alternative(
        self, estimate: CostEstimate, alternatives: list[CostEstimate]
    ) -> CostEstimate | None:
        """M5+M7: route to cheaper model if over budget (PLAN §7 E5)."""
        cheaper = [e for e in alternatives if e.amount < estimate.amount]
        if not cheaper:
            return None
        return min(cheaper, key=lambda e: e.amount)
