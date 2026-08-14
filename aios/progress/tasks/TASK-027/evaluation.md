# TASK-027 — Evaluation (Execution Graph)

**Ngày**: 2026-08-15 | **Trạng thái**: DONE ✅

## Đối chiếu tiêu chí chấp nhận (13/13 AC pass — xem test.md)

| AC | Kết quả | Bằng chứng |
|----|---------|------------|
| AC1 Contracts | ✅ | TestContracts (8 test) |
| AC2 Convert | ✅ | TestConverter (5 test) |
| AC3 State machine | ✅ | TestStateMachine (6 test) |
| AC4 PLAN §23 graph | ✅ | TestExecutor order/join/parallelism (4 test) + TestIntegration |
| AC5 Failure policies | ✅ | TestExecutor fail_fast/continue/skip/any/retries (7 test) |
| AC6 Cancel | ✅ | TestExecutor cancel queued/before/idempotent (3 test) |
| AC7 INV-015 | ✅ | 3 tầng build gate + test_inv015_graph_acyclicity_gate (2 literal) + planning_no_graph |
| AC8 Allow-list | ✅ | test_inv_graph_import_allowlist |
| AC9 No God Object | ✅ | test_inv015_graph_no_god_object + contracts_leaf |
| AC10 Additive | ✅ | git diff verify |
| AC11 Wiring | ✅ | test_graph_executor_wired + 1055 pass / 95.09% |
| AC12 Deterministic | ✅ | 2 lần chạy y hệt (trừ latency) |
| AC13 Ranh giới 026/028 | ✅ | graph state persist (READY verified) — 028 đọc được |

## Đánh giá so với PLAN.md §M5-15..19
- **Graph Contract** (§16): ExecutionGraph/GraphNode/GraphEdge (derived)/Dependency/Condition/JoinPolicy/FailurePolicy — đủ, extra=forbid
- **Graph State** (§17): 8 trạng thái PENDING·READY·RUNNING·SUCCEEDED·FAILED·SKIPPED·CANCELLED·BLOCKED — READY persist trong StateService (028 đọc được — test chứng minh)
- **INV-015 Graph Acyclicity** (§22): 3 tầng defense (build validator → converter wrap → executor pre-validate) + AST gate 2 file + behavioral
- **Scheduler Architecture** (§19): graph biết dependency-level (max_parallel trong graph); Resource/Scheduler không đụng (028)
- **Test strategy** (§23): A→B→C và A→B, A→C, B/C→D verified execution order — 2 test đúng tên

## Bài học
1. **arch_scan resolve relative 2-dots từ package 3 cấp sai** — import tuyệt đối cho module sâu (kernel/graph)
2. **`update_state` dùng `**fields`** — không phải dict positional
3. **Worker ghi dict phải pre-init toàn bộ key** (GIL-atomic, không resize) — tránh race deepcopy
4. **Container resolve trước register = "No registration"** — wiring thứ tự quan trọng
5. **Spec test CONTINUE có mâu thuẫn logic** (B dep A fail nhưng mong SUCCEEDED) — critic không bắt, implementer phải tự phát hiện + điều chỉnh + ghi deviation
6. **ThreadPool + barrier test cần wait(timeout)** — tránh test hang vô hạn khi regression

## Đề xuất cho task sau
- **TASK-028 Parallel Scheduler**: đọc graph state (nodes/READY/execution_order) từ StateService + `plan_to_graph(failure_policy=settings.graph.default_failure_policy)` + runner adapter nối real execution (injection point sẵn)
- Observability: metrics (latency_ms, max_concurrent_running) nằm trong GraphResult + state — gắn event/metrics ở task sau

## Kết luận
- [x] ĐẠT spec (13/13 AC)
- [x] INV-015 enforced 3 tầng; additive only
- [x] Deterministic + READY persist verified; coverage 95.09% (toàn suite 1055 pass)
