# TASK-068 — Review (trước implement)

> Reviewer (tự). Review spec v2.

## Đánh giá
- Kill Switch đúng PLAN §M10-18; gate ở boundary (không sửa ExecutionService). ✅
- Hợp nhất ToolGuard (TASK-067) — không cơ chế song song. ✅
- Idempotent + release an toàn. ✅

## Yêu cầu
1. **R1**: KHÔNG sửa `kernel/services/execution.py` / `orchestrator/goals/goal.py` — cancel qua public API.
2. **R2**: preflight/preflight_tool là hook duy nhất — mọi path mới (CLI/API/autonomous loop) phải check.
3. **R3**: emergency_stop idempotent (gọi 2 lần = 1 state + event).
4. **R4**: Gate E input: kill-switch bypass = 0 — không shortcut.

## Kết luận
**APPROVED có điều kiện** (R1–R4) — được phép implement.
