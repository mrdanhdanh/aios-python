# TASK-035 — E1 Identity & Access (M7) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `enterprise/`
> package (single source of truth), not duplicated here.

## Source of truth
- `backend/src/aios_core/enterprise/identity.py`
- `backend/src/aios_core/enterprise/contracts.py` (Principal / PrincipalType / Permission + factories)

## Key classes / functions
- `Principal` (contract, `extra="forbid"`), `PrincipalType` (user/service/agent/workflow/system)
- `RBACEngine` (`define_role`, `resolve` with `action:*` / `*:*` wildcard), `ABACEngine` (`add_rule`, `evaluate` — deny-wins, fail-closed)
- `DelegationChain` (composite principal + capability attenuation, `validate`)
- `IdentityEngine.require(principal)` — enforces **INV-022 Identity First** (raises `NoPrincipalError` when principal missing or lacks `id`/`tenant_id`)

## Verification
- `pytest tests/test_enterprise.py` (identity tests) + `tests/test_architecture.py::test_inv022_identity_first_call_site`
- Architecture invariant: `enterprise/` only imports intra-package + pydantic/stdlib (`test_inv022_enterprise_import_allowlist` / `arch_health` enterprise rule).
