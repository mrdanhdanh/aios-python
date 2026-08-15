# TASK-037 — Critique v2

## Vấn đề
- **P2-01**: `EnterpriseManager.route` expose router.

## Resolution
- ✅ facade `route` wrap `RuntimeRouter.select`.
