# TASK-027 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (14 + 12 vấn đề resolved) — sẵn sàng review → implement

## Checklist

- [ ] **T1. Contracts** — `kernel/graph/contracts.py`: GraphNodeStatus (8), GraphRunStatus, JoinPolicy, FailurePolicy, Condition, Dependency, GraphNode (join_policy, validator), ExecutionGraph (validator validate_graph_acyclic; edges derived; to_dict), GraphResult (node_reasons — C3-01), `_DagView` + `validate_graph_acyclic` (C1-01 — literal `validate_dag(` trong contracts.py)
- [ ] **T2. Errors** — `errors.py`: GraphError + GraphValidationError + GraphExecutionError
- [ ] **T3. State machine** — `state_machine.py`: TRANSITIONS (PENDING: {READY, RUNNING, SKIPPED, BLOCKED, CANCELLED} — C1-02), can_transition, is_terminal, is_ready (ALL/ANY/root), dead_end_status (SKIPPED/BLOCKED ưu tiên), graph_outcome (4 nhánh)
- [ ] **T4. Converter** — `converter.py`: `plan_to_graph(plan, *, failure_policy=FAIL_FAST)` — GraphNode per PlanNode (giữ thứ tự), Dependency từ depends_on, metadata map, deterministic, GraphValidationError wrap
- [ ] **T5. Executor core** — `executor.py`: `GraphExecutor(state_service, settings)`; execute: pre-validate (**literal `validate_dag(` với _DagView — C2-01 v2**), condition fail-loud, cancel-before-execute, init state (nodes đủ mọi id), wave loop (dead-end → ready sort id asc → PENDING→READY persist → submit; **no-progress guard → GraphExecutionError — C2-04**), worker start-guard (**check flag/status trước attempt đầu — C2-02**), READY→RUNNING do worker (C2-03), retries (check flag mỗi attempt — C2-09), failure policy tại ranh giới wave (FAIL_FAST/SKIP_DEPENDENTS/CONTINUE), max_concurrent_running = max(trước, min(len, max_parallel)) (C2-03 v1), execution_order do main tại submit (C2-03 v2), state write protocol single-key in-place (C2-06 v2), graph_outcome, persist cuối
- [ ] **T6. Cancel** — `cancel(execution_id)`: lock chỉ bảo vệ _cancel_flags (C2-06 v1), trả ngay; in-flight không kill; queued bị chặn bởi worker start-guard
- [ ] **T7. Config + wiring** — `config.py` GraphSettings (max_parallel, default_failure_policy + validator), `config.yaml` block graph, `runtime_kernel.py` wiring (state_service = resolve(StateService) shared instance)
- [ ] **T8. Unit tests** — `tests/test_execution_graph.py`: contracts (8 status, edges derived §16, cycle GraphNode.model_construct → ValidationError — C2-07), state machine (8×8 param, is_ready, dead_end, outcome), converter (A→B→C, §16 4-node, metadata, deterministic, GraphValidationError), executor (order A→B→C, join §23, READY persist — C2-03, parallelism barrier wait(timeout=5) — C2-10, max_concurrent biên — C2-11, FAIL_FAST, CONTINUE, SKIP_DEPENDENTS, Join ANY, cancel queued — C2-02, retries, retry-cancel — C2-09, cancel, state persist namespace — C2-05, condition fail-loud, no-progress guard — C2-04, init validation — C2-07, deterministic)
- [ ] **T9. Arch tests** — `test_architecture.py`: `test_inv_graph_import_allowlist` (datetime — C2-04), `test_inv015_graph_acyclicity_gate` (literal validate_dag trong contracts + executor), `test_inv015_graph_no_god_object`, `test_inv015_planning_no_graph`
- [ ] **T10. Config + wiring tests** — `test_config.py` (block graph + env override), `test_runtime_kernel.py` (resolve GraphExecutor + shared StateService)
- [ ] **T11. Integration** — `test_execution_graph.py`: plan → convert → execute với fake runner (execution_order, state persist), PLAN §23 2 test đúng tên, qua container
- [ ] **T12. Full suite + coverage** — pytest toàn bộ, coverage ≥ 80% cứng (95% mục tiêu); git diff verify additive only
- [ ] **T13. test.md + evaluation.md** — đối chiếu 13 AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
