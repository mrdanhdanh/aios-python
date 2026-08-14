# TASK-027 — Test Results (Execution Graph)

**Ngày**: 2026-08-15 | **Runner**: pytest (backend/.venv)

## Kết quả tổng
- **Full suite**: `1055 passed, 0 failed` (baseline 1003 → +52 test mới)
- **Coverage**: 95.09% (threshold 80% cứng — pass)
- **Arch tests**: 36/36 pass (gồm 5 test INV-015/graph mới)

## Test mới (52)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_execution_graph.py` | 44 | contracts (8 status, extra=forbid, negative timeout/self-dep/dup-dep/empty, edges derived §16, cycle build gate C2-07), errors hierarchy, state machine (8×8 param table, terminal, is_ready ALL/ANY/root, dead_end priority, graph_outcome 4 nhánh), converter (chain, §16 4-node, metadata, policy override, cyclic plan → GraphValidationError, deterministic), executor (chain order, join §23, ready persist C2-03, parallelism barrier C2-10, max_concurrent biên C2-11, FAIL_FAST, CONTINUE, SKIP_DEPENDENTS, Join ANY, retries, cancel queued C2-02, cancel trước execute, idempotent, state namespace C2-05, condition fail-loud, no-progress guard C2-04, init validation C2-07, deterministic), integration (plan→convert→execute, PLAN §23 2 test), INV-015 behavioral |
| `tests/test_architecture.py` | +5 | `test_inv_graph_import_allowlist` (concurrent — external), `test_inv015_graph_acyclicity_gate` (literal validate_dag contracts + executor), `test_inv015_planning_no_graph`, `test_inv015_graph_no_god_object`, `test_inv015_contracts_leaf` |
| `tests/test_config.py` | +2 | graph defaults + env override `AIOS_GRAPH__MAX_PARALLEL`; invalid policy/max_parallel → ValidationError |
| `tests/test_runtime_kernel.py` | +1 | `test_graph_executor_wired` (resolve + shared StateService + execute) |

## Kiểm chứng AC (13/13)
- **AC1** ✅ Contracts 8 status + 2/3 policy + edges derived §16 + hierarchy errors
- **AC2** ✅ Convert deterministic (thứ tự plan, ALL/FAIL_FAST default, override, metadata, 2 lần y hệt)
- **AC3** ✅ State machine bảng đầy đủ (8×8 param, is_ready, dead_end ưu tiên BLOCKED > SKIPPED, outcome 4 nhánh)
- **AC4** ✅ PLAN §23: A→B→C order; A→B, A→C, B/C→D order; parallelism barrier max_concurrent==2 + order deterministic
- **AC5** ✅ Failure policies: FAIL_FAST BLOCKED + order [A]; CONTINUE SKIPPED + nhánh độc lập chạy; SKIP_DEPENDENTS transitive; Join ANY; retries 2 fail → SUCCEEDED (3 attempts)
- **AC6** ✅ Cancel: queued không chạy (runner đếm call), CANCELLED, trước execute, idempotent
- **AC7** ✅ INV-015: build gate (GraphNode.model_construct → ValidationError), convert → GraphValidationError, execute pre-validate → GraphValidationError; AST gate 2 literal validate_dag; planning không import graph
- **AC8** ✅ Allow-list pass (external concurrent, datetime; CẤM orchestrator/models/execution/resource/scheduler)
- **AC9** ✅ No God Object: executor chứa GraphStateMachine; state_machine/converter không execute; executor không plan_to_graph; contracts leaf
- **AC10** ✅ Additive only (git diff: 5 MOD + 3 NEW; kernel/services/* không đổi)
- **AC11** ✅ Wiring: resolve + shared StateService (singleton) + execute qua container; config block + env override; 1055 pass / 95.09%
- **AC12** ✅ Deterministic: 2 lần chạy model_dump() (trừ latency) y hệt; submit order không đổi khi completion order khác
- **AC13** ✅ Ranh giới 026/028: không scheduler/resource logic; graph state persist (READY persist verified — 028 đọc được)

## Ghi chú / Deviations
1. **Import absolute trong kernel/graph** — `_resolve_relative` của arch_scan resolve `..dag` (2 dots từ kernel/graph) thành `aios_core.kernel.graph.dag` (sai) → dùng `from aios_core.kernel.dag import ...` (tuyệt đối, scan resolve đúng).
2. **`concurrent.futures` bị tách thành external `concurrent`** — allow-list dùng `concurrent`.
3. **Test CONTINUE điều chỉnh**: spec test gốc mong "B SUCCEEDED" với B dep A fail — mâu thuẫn logic (B dead-end → SKIPPED) → test dùng nhánh độc lập E chạy được + B/C SKIPPED.
4. **`update_state` là `**fields`** — call site `update_state(execution_id, nodes=statuses)`.
5. **Wiring graph phải SAU register services** (StateService phải được register trước khi resolve) — block di chuyển xuống cuối create().
6. **cancel-before-execute không ghi state** (R3-6) — get_state → None.

## Kết luận
- [x] Tất cả 13 AC pass
- [x] Full suite 1055 pass, coverage 95.09%
- [x] INV-015 enforced (behavioral + AST 2 call-site); deterministic + READY persist verified
