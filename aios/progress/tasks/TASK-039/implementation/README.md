# TASK-039 — E5 Enterprise Resource Governance (M7) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `enterprise/`
> package (single source of truth), not duplicated here.

## Source of truth
- `backend/src/aios_core/enterprise/governance.py`
- `backend/src/aios_core/enterprise/contracts.py` (Quota, ResourceUsage, CostEstimate)

## Key classes / functions
- `QuotaManager` — per-tenant quota accounting; `can_start`/`check_fairness` enforce **INV-025 Resource Fairness** (raise `QuotaExceeded` when over quota without `override`); `begin`/`end`/`add_tokens`/`add_tool_calls`
- `CostGovernor` — `estimate`/`check_budget`/`charge` + `cheaper_alternative` (route to cheaper model when over budget, combining M5 Model Router + M7 Governance)

## Verification
- `pytest tests/test_enterprise.py` (governance tests) + `tests/test_architecture.py::test_inv025_resource_fairness_quota_gate`
- Architecture invariant: `enterprise/` only imports intra-package + pydantic/stdlib.
