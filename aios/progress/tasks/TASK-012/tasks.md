# TASK-012 — Tasks Breakdown (M2-P3b)

> Ngày: 2026-08-12 | Spec: `spec.md` (approved — critique ×2 resolved) | Chuỗi: Plan → Spec → Critique ×2 → **Tasks** → Review → Implement → Test → Evaluate

## Checklist

### T1 — Kernel mở rộng (additive, backward-compatible)
- [ ] T1.1 `kernel/events.py` `EventType`: thêm 6 giá trị pin — `GOAL_CREATED="goal.created"`, `GOAL_STATUS_CHANGED="goal.status_changed"`, `GOAL_TASK_UPDATED="goal.task_updated"`, `QUEUE_UPDATED="queue.updated"`, `RECOVERY_RETRY="recovery.retry"`, `RECOVERY_FALLBACK="recovery.fallback"`
- [ ] T1.2 `kernel/services/policy.py`: `PolicyDecision` thêm `ask_scopes: list[str] = field(default_factory=list)` (dataclasses.field — C2-06); `evaluate` set đủ ở MỌI nhánh return (deny/token/internet → `[]`, approval → ask_scopes, allow → `[]`)
- [ ] T1.3 `config.py`: thêm `GoalsSettings(db_path="aios/data/goals.db")` + `goals` field; `backend/config.yaml` thêm block

### T2 — `orchestrator/goals/` package (scaffold + errors)
- [ ] T2.1 `goals/__init__.py` (exports + `build_goal_modules(settings, event_service, policy_service, approver=None)`)
- [ ] T2.2 `goals/errors.py`: `GoalError`, `QueueError` (kế thừa `OrchestratorError`)
- [ ] T2.3 Cập nhật `orchestrator/__init__.py` export

### T3 — GoalManager (`goals/goal.py`)
- [ ] T3.1 `GoalStatus`, `TaskStatus`, `Goal`, `GoalTask` (pydantic v2, extra="forbid", position — C2-02)
- [ ] T3.2 `_init_db()`: bảng `goals` + `goal_tasks` (position, CHECK constraints) + index
- [ ] T3.3 `create_goal` (1 transaction: goal + tasks, position 0..n-1), `add_task` (terminal → GoalError), `get_goal` (ORDER BY position), `list_goals(status, limit)`, `progress` (not found → GoalError)
- [ ] T3.4 State machine goal + task (transition hợp lệ; sai → GoalError; mismatch goal/task → GoalError)
- [ ] T3.5 `update_task_status` + recompute progress + auto-status (ACTIVE-only) + cascade cancel (queue items queued→cancelled cùng transaction) + `pause_goal`/`resume_goal` (recompute — C2-11) + `cancel_goal`
- [ ] T3.6 Events (success-only): GOAL_CREATED / GOAL_STATUS_CHANGED / GOAL_TASK_UPDATED qua `event_service.emit`
- [ ] T3.7 SQLite pattern: `with closing(...) as conn, conn:` + busy_timeout=5000 + mkdir parent

### T4 — TaskQueue (`goals/task_queue.py`)
- [ ] T4.1 `QueueItemStatus`, `QueueItem`; `_init_db()` bảng `queue_items` (UNIQUE position, CHECK)
- [ ] T4.2 `enqueue` atomic `INSERT...SELECT COALESCE(MAX(position),0)+1` (không validate goal/task id)
- [ ] T4.3 `dequeue` 1 statement `UPDATE ... WHERE id=(SELECT ...) RETURNING *` (C2-05)
- [ ] T4.4 `pause`/`resume` (transition check; running → QueueError), `reorder` 2 pha + bắt buộc đủ item queued (C2-01), `list_items`, `clear(status)`
- [ ] T4.5 `recover_stale_running(threshold_s=3600)` + gọi trong `__init__`
- [ ] T4.6 Events QUEUE_UPDATED (success-only; bulk: reorder 1 event/item, clear 1 event tổng kèm count)

### T5 — PermissionBroker (`goals/permission_broker.py`)
- [ ] T5.1 `PermissionBatch`, `PermissionBatchDecision` (pydantic v2)
- [ ] T5.2 `collect` (validate scope, dedupe, sort, rỗng → ValueError) + `collect_and_request`
- [ ] T5.3 `request`: evaluate → deny → DENY all; requires_approval → ask_scopes ASK + allow ALLOW (không tự tính lại); special case ask_scopes rỗng → toàn bộ ASK
- [ ] T5.4 Approver: ALLOW/DENY; raise → DENY + ERROR_OCCURRED; ASK → DENY; None + requires_approval → DENY "no approver configured" (C2-12); None + allow → ALLOW
- [ ] T5.5 Events/audit: PERMISSION_REQUESTED (schema khớp policy: service/request_id/scopes/ask_scopes), PERMISSION_GRANTED/DENIED (batch_id trong payload); batch rỗng → ValueError

### T6 — FailureRecovery (`goals/failure_recovery.py`)
- [ ] T6.1 `RecoveryStatus`, `RecoveryResult`; validate config (max_retries/backoff ≥ 0 → ValueError)
- [ ] T6.2 `run`: gốc → retry (backoff min(base*2**i, max), sleeper injectable) → fallback agent → fallback workflow (mỗi bước 1 lần) → report
- [ ] T6.3 Events: ERROR_OCCURRED (mọi lần fail — C2-07), RECOVERY_RETRY, RECOVERY_FALLBACK

### T7 — Test (4 file mới + test_import + test_policy)
- [ ] T7.1 `tests/test_goal_manager.py` — 12 test (AC1-3, AC11-goal, C2-10/11/13)
- [ ] T7.2 `tests/test_task_queue.py` — 13 test (AC4-6, AC11-queue, C1-03/04/16, C2-01/05/08/15)
- [ ] T7.3 `tests/test_permission_broker.py` — 8 test (AC7-8, C1-07/11, C2-04/12/13)
- [ ] T7.4 `tests/test_failure_recovery.py` — 7 test (AC9-10, AC11-recovery, C1-10)
- [ ] T7.5 `tests/test_import.py` cập nhật + `tests/test_policy.py` thêm test `ask_scopes` field (C2-06)
- [ ] T7.6 Chạy `pytest -q` toàn bộ (baseline 428 + mới) + coverage module goals ≥ 80%

### T8 — Đánh giá + commit
- [ ] T8.1 `evaluation.md`: đối chiếu 12 AC
- [ ] T8.2 Cập nhật `PROGRESS.md` (TASK-012 done), `LOG.md`, `STATS.md`
- [ ] T8.3 Commit + working tree sạch

## Ghi chú quy trình
- Hard gate: spec + critique ×2 resolved ✅ → review.md (reviewer) → implement
- Code/commit tiếng Anh; tài liệu tiếng Việt
- Bypass chỉ cho fix nhỏ, ghi `[bypass]` vào LOG.md
