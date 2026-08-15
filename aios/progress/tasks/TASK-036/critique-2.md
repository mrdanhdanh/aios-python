# TASK-036 — Critique v2

## Vấn đề
- **P2-01**: boundary phải dùng từ `EnterpriseManager.enforce_tenant`.
- **P3-01**: docstring tier chưa link INV-023.

## Resolution
- ✅ facade `enforce_tenant` wrap `TenantBoundary.enforce`.
- ✅ docstring cập nhật.
