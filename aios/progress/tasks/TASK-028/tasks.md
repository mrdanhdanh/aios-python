# TASK-028 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (14 + 15 vấn đề resolved) — sẵn sàng review → implement

## Checklist

- [ ] **T1. Contracts** — `kernel/scheduler/contracts.py`: `NodeResourceMetrics` (resource_wait_ms tổng, slots_acquired tổng dưới lock — C2-01), `ScheduledGraphResult` (graph: GraphResult wrap, node_metrics pre-init, queue_time_ms, peak_slots_used, resource_stats) — extra=forbid
- [ ] **T2. Errors** — `errors.py`: SchedulerError + ResourceUnavailableError + ExecutionNodeError
- [ ] **T3. GraphScheduler core** — `scheduler.py`: `__init__` (resource/state duck-typed + executor mặc định `GraphExecutor(state, settings=graph_settings)` — C2-06 v2 + graph_settings C1-02), `schedule()` (pre-init node_metrics → gated runner: acquire_slot_wait → slots_held/peak dưới lock → runner → finally decrement TRƯỚC release — C3-06; ResourceUnavailableError; → executor.execute wrap → metrics → persist scheduler_metrics key riêng), `schedule_plan` (plan_to_graph với failure_policy resolve: None → graph_settings.default_failure_policy convert str→FailurePolicy — C2-01 v2), `cancel` delegate (C2-05)
- [ ] **T4. ExecutionServiceRunner** — `execution_runner.py`: adapter 1-node plan (id `gnode:{node.id}` — C3-03 giữ + ghi giới hạn §7), `self.execution_service.execute(plan, ...)` (C2-04 literal), COMPLETED → result / FAILED → ExecutionNodeError; inner noop default
- [ ] **T5. Config + wiring** — `config.py` SchedulerSettings (resource_wait_timeout_s), `config.yaml` block scheduler, `runtime_kernel.py` wiring (resource/state/executor resolve + **graph_settings=settings.graph — C2-01 v2**)
- [ ] **T6. Unit tests** — `tests/test_parallel_scheduler.py`: contracts, errors, scheduler (single slot serial, parallel bounded inject executor max_parallel=3 — C2-06 v2, queue observability, timeout barrier-poll 0.1s — P3-07, runner raise → release, cancel-while-waiting retries≥1 — C2-04 v2, metrics + slots_acquired==2 retries=1 — P3-08, schedule_plan resolve policy, deterministic ResourceService mới — P3-04), runner (spy 1-node plan, COMPLETED/FAILED, inner/noop, e2e RuntimeKernel 3 node), integration (PLAN §23 2 test đúng tên, INV-016 chain spy sequence, duck-typed stub)
- [ ] **T7. Arch tests** — `test_architecture.py`: `test_inv016_scheduler_import_allowlist` (pin: services.execution CHỈ execution_runner.py — exclude DOTTED — C2-03 v2; execution_plan toàn dir), `test_inv016_scheduler_no_god_object`, `test_inv016_scheduler_no_private_access` (giới hạn v1 — P3-03), `test_inv016_scheduler_call_sites` (literal acquire_slot_wait(/release_slot(/execution_service.execute(), `test_inv016_graph_no_scheduler`, `test_inv016_planning_no_scheduler`
- [ ] **T8. Config + wiring tests** — `test_config.py` (scheduler block + env override + invalid), `test_runtime_kernel.py` (resolve + shared instances + _graph_settings)
- [ ] **T9. Test C1-01 tường minh** — adapter + max_concurrent=1 → node FAILED "resource unavailable", stats running==0, pending==0 (C2-02 v2)
- [ ] **T10. Full suite + coverage** — pytest toàn bộ, coverage ≥ 80% cứng (95% mục tiêu); git diff verify additive only
- [ ] **T11. test.md + evaluation.md** — đối chiếu 12 AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
