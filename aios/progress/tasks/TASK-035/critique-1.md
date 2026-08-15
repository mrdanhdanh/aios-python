# TASK-035 — Critique v1 (tự phản biện)

## Vấn đề phát hiện
- **P1-01**: `require` chỉ check `principal is None` — phải check cả `id`/`tenant_id` rỗng (INV-022 strict).
- **P2-01**: ABAC rule condition signature `(principal, action, resource)` — resource là dict, cần chuẩn hóa key `type`.
- **P2-02**: RBAC wildcard chưa test `*:*`.
- **P3-01**: delegation attenuation chưa thực sự thu hẹp scopes khi `scopes` rỗng.

## Resolution
- ✅ `require` raise nếu `not principal.id or not principal.tenant_id`
- ✅ ABAC evaluate nhận `resource` dict, action match `"*"`.
- ✅ test wildcard `"*:*"` và `"action:*"`.
- ✅ `resolve` áp dụng scoped intersection khi `scopes` có chứa `:`.
