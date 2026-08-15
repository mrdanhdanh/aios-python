# TASK-036 — E2 Multi-Tenancy (M7)

## Mục tiêu
Mọi data/execution thuộc về 1 tenant. `TenantBoundary` deny-by-default (INV-023). Cung cấp `MemoryNamespace` per-tenant.

## Phạm vi
- `Tenant` model (id, name, tier: development/standard/secure/enterprise)
- `TenantRegistry` (thread-safe register/get/exists/list)
- `TenantBoundary.enforce(tenant_id, resource_tenant)` raise `CrossTenantAccessDenied` default-deny
- `MemoryNamespace` (per-tenant put/get, enforce boundary)

## Input/Output
- In: tenant_id + resource; Out: allow/deny + isolated namespace

## Tiêu chí chấp nhận (AC)
1. INV-023: cross-tenant access → `CrossTenantAccessDenied`
2. Tenant tiers xác định isolation level
3. `MemoryNamespace` không leak giữa tenant
4. Registry thread-safe
5. Contract `extra=forbid`
6. Test deny-by-default path
7. `may_access` boolean helper
