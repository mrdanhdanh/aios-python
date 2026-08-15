# TASK-039 — Critique v1

## Vấn đề
- **P1-01**: quota fairness phải tính per-tenant, không global.
- **P2-01**: `begin`/`end` cập nhật usage, phải thread-safe.

## Resolution
- ✅ quota keyed by tenant_id.
- ✅ Lock quanh usage mutation.
