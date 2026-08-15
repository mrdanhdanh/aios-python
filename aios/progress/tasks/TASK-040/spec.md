# TASK-040 — E6 Security & Data Isolation (M7)

## Mục tiêu
`CredentialBroker` (scoped INV-024) + `NetworkPolicyEngine` (default-deny) + `SandboxBoundary` (INV-028). Credential chỉ resolve trong scope tenant/project/capability.

## Phạm vi
- `CredentialRef` contract (id, tenant_id, project_id, capability, scopes, expires_at, secret_ref)
- `CredentialBroker.register/_assert_scope/resolve` raise `CredentialError` nếu scope sai
- `NetworkPolicyEngine.allow` default-deny
- `SandboxBoundary.register_profile/require_sandbox` raise `SandboxBypassError` (INV-028)

## Input/Output
- In: capability + context; Out: scoped credential/token

## Tiêu chí chấp nhận (AC)
1. INV-024: resolve credential ngoài scope → `CredentialError`
2. INV-028: untrusted execution không có sandbox profile → `SandboxBypassError`
3. NetworkPolicy default-deny
4. expires_at enforce
5. Contract `extra=forbid`
6. Test scope gate
7. Test sandbox boundary
