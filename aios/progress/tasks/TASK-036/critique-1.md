# TASK-036 — Critique v1

## Vấn đề
- **P1-01**: `TenantBoundary.enforce` mặc định system tenant (`*`/`system`) phải được allow đặc biệt để kernel hoạt động.
- **P2-01**: `MemoryNamespace` cần lock riêng per-tenant.
- **P3-01**: registry `get` với tenant không tồn tại → raise `TenantNotFoundError`.

## Resolution
- ✅ system tenant bypass boundary (documented).
- ✅ `MemoryNamespace` dùng dict[str, dict] + Lock.
- ✅ `registry.get` raise `TenantNotFoundError`.
