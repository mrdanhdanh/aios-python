# TASK-012 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Goal Manager (state machine, cascade cancel, persist) | `backend/src/aios_core/orchestrator/goals/goal.py` |
| Task Queue (atomic dequeue, reorder 2-pha, recover stale) | `backend/src/aios_core/orchestrator/goals/task_queue.py` |
| Permission Broker (ask_scopes, default-deny) | `backend/src/aios_core/orchestrator/goals/permission_broker.py` |
| Failure Recovery (retry→fallback→report) | `backend/src/aios_core/orchestrator/goals/failure_recovery.py` |
| Shared errors / schema | `backend/src/aios_core/orchestrator/goals/errors.py`, `schema.py` |
| Factory `build_goal_modules` | `backend/src/aios_core/orchestrator/goals/__init__.py` |
| Kernel additive (EventType +6, PolicyDecision.ask_scopes, GoalsSettings) | `backend/src/aios_core/kernel/`, `backend/config.yaml` |
| Tests | `test_goal_manager.py`, `test_task_queue.py`, `test_permission_broker.py`, `test_failure_recovery.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- Task Queue: dequeue = single `UPDATE..RETURNING` (no double-dequeue, no lost update).
- Lifecycle transitions (post M2-review fix): `QUEUED↔PAUSED`, `QUEUED/PAUSED→CANCELLED`,
  `RUNNING→COMPLETED/FAILED/CANCELLED` qua `complete()/fail()/cancel()`.
- Failure Recovery: `max_retries` có giới hạn (no infinite loop), backoff exponential,
  permanent error → không retry, fallback agent lỗi → không fallback về chính nó → report.
