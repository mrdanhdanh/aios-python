# TASK-035 — E1 Identity & Access (M7)

## Mục tiêu
Đưa identity vào mọi request: `User → Identity → Tenant → Role → Permission → Policy → Execution`. Principal model (user/agent/service/workflow/system) + RBAC + ABAC + delegation với capability attenuation.

## Phạm vi
- `Principal` contract (id, type, tenant_id, roles, attributes, delegated_from, scopes)
- `RBACEngine` (role→permission, wildcard), `ABACEngine` (attribute/resource/env condition, deny-wins)
- `DelegationChain` (composite principal + validate)
- `IdentityEngine.require(principal)` enforce INV-022 (execution phải có Principal)

## Input/Output
- In: request + identity context; Out: authorized decision / Principal
- Fail-closed: thiếu Principal hoặc không có permission → deny/raise

## Tiêu chí chấp nhận (AC)
1. INV-022: `IdentityEngine.require(None)` raise `NoPrincipalError`
2. RBAC resolve role→permission, hỗ trợ wildcard `action:*`/`*:*`
3. ABAC deny rule thắng allow (fail-closed)
4. Delegation chain validate (delegated_from phải nằm trong chain)
5. `authorize()` kết hợp RBAC + ABAC
6. Principal factory: user/agent/service
7. Contract `extra=forbid`
8. Unit test coverage ≥ 90%
