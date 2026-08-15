# TASK-036 — E2 Multi-Tenancy (M7) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `enterprise/`
> package (single source of truth), not duplicated here.

## Source of truth
- `backend/src/aios_core/enterprise/tenancy.py`
- `backend/src/aios_core/enterprise/contracts.py` (Tenant, TenantScope, IsolationTier)

## Key classes / functions
- `TenantRegistry` (thread-safe register/get/exists/list/isolation_tier)
- `TenantBoundary.enforce` / `may_access` — deny-by-default cross-tenant access (**INV-023 Tenant Isolation**); raises `CrossTenantAccessDenied`
- `MemoryNamespace` — per-tenant memory isolation (`memory:<tenant_id>`), owner-only reads
- `TenancyManager` — facade composing registry + boundary + namespaces

## Verification
- `pytest tests/test_enterprise.py` (tenancy tests) + `tests/test_architecture.py::test_inv023_tenant_isolation_deny_default`
- Architecture invariant: `enterprise/` only imports intra-package + pydantic/stdlib.
