# TASK-005 — Breakdown checklist

> `[x]` = đã làm XONG VÀ đã verify.

## F1 — Contract changes + Settings
- [ ] F1.1 `PlanNode.timeout_s: int → float` (execution_plan.py) + test thêm case float 0.5
- [ ] F1.2 `EventType.WORKFLOW_CANCELLED` thêm (events.py)
- [ ] F1.3 `ResourcesSettings` (max_tokens, max_concurrent) + config.yaml + test_config
- [ ] F1.4 Chạy lại test TASK-003/004 → không regression

## F2 — Services mới
- [ ] F2.1 `scheduler.py` — SchedulerService (poll, one-shot/interval, skip overlap, hooks)
- [ ] F2.2 `state.py` — StateService (schema plan/nodes/results/started_at, deepcopy fallback)
- [ ] F2.3 `resource.py` — ResourceService (tokens, slots, stats, clamp)
- [ ] F2.4 `execution.py` — ExecutionService (runner contract, topo, retry, timeout, cancel, snapshot/resume, pre-check, try/finally)
- [ ] F2.5 `runtime_kernel.py` (ở kernel/) — RuntimeKernel.create (register_instance + register pattern)
- [ ] F2.6 Export: kernel/__init__ + services/__init__ + test_import

## F3 — Tests + Verify
- [ ] F3.1 test_scheduler (one_shot, interval_n_times, skip_overlap, error_continues, cancel_noop, idempotent, duplicate_name), test_state (set_get_update, deepcopy_independent, fallback_repr, restore), test_resource (tokens_budget, release_clamp, slot_limit, stats), test_execution (topo_order, retry_success, retry_exhausted_fail_fast, timeout_retryable, timeout_zero, cancel_between_nodes, cancel_before_execute_immediate, snapshot_resume, plan_mismatch, policy_deny, approval_required, resource_unavailable, release_on_fail, events_emitted, reason_nonempty), test_runtime_kernel (create_has_all, resolve_all_no_raise, start_stop_idempotent, end_to_end)
- [ ] F3.2 pytest từ backend/ → pass, coverage ≥ 80%; git sạch (AC14)
- [ ] F3.3 Commit code — `M1-P0.5c: ...`
- [ ] F3.4 Ghi test.md + evaluation.md + PROGRESS/LOG/STATS + commit cuối
