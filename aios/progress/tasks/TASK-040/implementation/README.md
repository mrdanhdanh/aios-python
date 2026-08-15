# TASK-040 — E6 Security & Data Isolation (M7) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `enterprise/`
> package (single source of truth), not duplicated here.

## Source of truth
- `backend/src/aios_core/enterprise/security.py`
- `backend/src/aios_core/enterprise/contracts.py` (CredentialRef, NetworkPolicy, SandboxProfile)

## Key classes / functions
- `CredentialBroker` — scoped, short-lived credential resolution (**INV-024 Credential Isolation**): `_assert_scope` enforces tenant/project/capability before `resolve`; raises `CredentialError`; never returns raw secret (returns scoped token)
- `NetworkPolicyEngine` — default-deny `allow`/`check`
- `SandboxBoundary.require_sandbox` — enforces **INV-028 Sandbox Boundary**: untrusted tools MUST run under a sandbox profile, else raises `SandboxBypassError`

## Verification
- `pytest tests/test_enterprise.py` (security tests) + `tests/test_architecture.py::test_inv024_credential_isolation_scope_check` + `::test_inv028_sandbox_boundary_untrusted`
- Architecture invariant: `enterprise/` only imports intra-package + pydantic/stdlib.
