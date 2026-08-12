# Evaluation — TASK-012 (M2-P3b: Goal Manager + Task Queue + Permission Broker + Failure Recovery)

> Ngày: 2026-08-13 | Chuỗi: Plan → Spec → Critique ×2 (31 vấn đề resolved) → Review (APPROVED, R1-R6) → Implement → Test → **Evaluate**

## Kết quả test

- **490 passed** (baseline 428 + 62 mới), 0 failed, 5 warnings — `pytest -q` từ `backend/`
- **Coverage toàn bộ: 95.96%** (yêu cầu ≥ 80%) — module `orchestrator/goals/` cao
- Offline-first: 0 gọi model, 0 sleep thật (sleeper stub), không Docker/network

## Đối chiếu 12 AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | Goal CRUD + persist qua phiên + position | ✅ `test_create_goal_with_tasks_and_get`, `test_persist_across_instances` |
| AC2 | Progress + auto-status (completed/failed/paused-block + resume recompute C2-11) | ✅ 5 test |
| AC3 | State machine goal/task + cascade cancel + terminal add_task + mismatch | ✅ 6 test (có `test_cancel_goal_cascades_queue_items`) |
| AC4 | Queue ordering + FIFO + empty + concurrent enqueue (UNIQUE position) | ✅ 4 test |
| AC5 | pause/resume/reorder/clear/persist/recover stale | ✅ 8 test |
| AC6 | Dequeue atomic (UPDATE..RETURNING, không double) | ✅ 3 test |
| AC7 | collect dedupe/sort/ValueError + policy deny | ✅ 4 test |
| AC8 | Approver (deny/allow/raise/no-approver) + audit schema (C2-04) | ✅ 6 test |
| AC9 | Retry + backoff dãy đúng + sleeper stub | ✅ 3 test |
| AC10 | Fallback agent/workflow 1 lần + history + 5 ERROR_OCCURRED | ✅ 4 test |
| AC11 | Events đầy đủ + audit + fail không emit | ✅ 3 test |
| AC12 | Import + factory + toàn bộ pytest + coverage | ✅ `test_build_goal_modules_factory` |

**12/12 AC đạt.**

## Xử lý rủi ro review R1-R6

- R1+R2 (shared DDL `no such table`): ✅ `schema.py` — GoalManager-only vẫn cascade được
- R3 (ask_scopes 5 nhánh): ✅ `test_policy_decision_ask_scopes_field_all_branches` assert cả 5
- R4 (stale recovery parse ISO + event recover): ✅ fromisoformat + QUEUE_UPDATED action="recover"
- R5 (task cascade cancel): ✅ task không terminal → cancelled
- R6 (3 assertion audit): ✅ source==batch.id, audit QUEUE_UPDATED, payload round-trip

## Thay đổi so với kế hoạch (đã ghi LOG)

- `SCHEMA_SQL` tách sang `schema.py` (tránh circular import `__init__` ↔ `goal`)
- Dequeue 1 statement `UPDATE..RETURNING` (C2-05) thay vì 2 bước
- `COALESCE(MAX(position), -1)+1` cho enqueue (item đầu position=0 — MAX trên bảng rỗng trả NULL)
- History recovery theo đúng spec (phase entries, không lặp agent)
- Broker: `resolved` chỉ gọi approver khi có scope ASK

## Bài học mới (bổ sung STATS.md)

1. `INSERT..SELECT COALESCE(MAX(x),0)+1` trên bảng rỗng cho position=1 — dùng `-1` làm base nếu muốn 0-indexed.
2. `EventBus.subscribe(event_type, handler)` — event_type là tham số BẮT BUỘC (None = tất cả); quên → TypeError.
3. `query_audit()` trả `list[Event]` (không phải dict) — đọc `e.type.value`.
4. SQLite `UNIQUE(position)` là immediate — reorder 1 pha đụng constraint; phải 2 pha (dải âm) trong 1 transaction.
5. State machine pending→completed là bất hợp lệ — test phải đi qua chuỗi queued→running.
6. `EventService` không expose bus — factory cần `PolicyService` truyền vào, không tự tạo.

## Kết luận

**TASK-012 ĐẠT — 12/12 AC, 490 test pass, coverage 95.96%, git sạch sau commit.**
