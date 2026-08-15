# TASK-042 — Enterprise Operations + Dashboard (M7) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `enterprise/`
> package (single source of truth), not duplicated here.

## Source of truth
- `backend/src/aios_core/enterprise/dashboard.py`
- `backend/src/aios_core/enterprise/__init__.py` (`EnterpriseManager` facade — composes all M7 subsystems, exposes INV-022..INV-029 enforcement methods)
- `backend/src/aios_core/enterprise/operations.py` (`EnterpriseDashboard` consumes `CentralAuditStore`)

## Key classes / functions
- `EnterpriseDashboard` — aggregates tenant operational metrics from audit evidence (executions, success rate, policy violations, agents, workflows) along enterprise observability dimensions
- `EnterpriseManager` — Control-Plane facade wiring all 7 enterprise groups (E1–E7); methods `require_principal` (INV-022), `enforce_tenant` (INV-023), `resolve_credential` (INV-024, records audit), `begin_execution` (INV-025), `acquire_lease` (INV-026), `deny` (INV-027), `require_sandbox` (INV-028), `route` (INV-029)

## Verification
- `pytest tests/test_enterprise.py` (dashboard + manager tests) + `tests/test_architecture.py::test_inv029_control_plane_isolation_router` + `::test_m7_enterprise_no_god_object`
- Architecture invariant: `enterprise/` only imports intra-package + pydantic/stdlib (`test_inv022_enterprise_import_allowlist` / `arch_health` enterprise rule).
