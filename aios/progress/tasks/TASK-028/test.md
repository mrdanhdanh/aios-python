# TASK-028 — Test Results (Parallel Scheduler)

**Ngày**: 2026-08-15 | **Runner**: pytest (backend/.venv)

## Kết quả tổng
- **Full suite**: `1086 passed, 0 failed` (baseline 1055 → +31 test mới)
- **Coverage**: 95.22% (threshold 80% cứng — pass)
- **Arch tests**: 42/42 pass (gồm 6 test INV-016 mới)

## Test mới (31)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_parallel_scheduler.py` | 23 | contracts (extra=forbid, defaults), errors hierarchy, scheduler (single slot serial, parallel bounded peak==2, queue observability poll, timeout fail 0.1s barrier-poll, runner raise release, cancel-while-waiting retries≥1, metrics, retries slots_acquired==2 P3-08, schedule_plan resolve policy C2-01 v2 + override, deterministic instance mới P3-04), runner (1-node plan, FAILED → ExecutionNodeError, inner/noop), adapter limitation (C1-01: max_concurrent=1 → FAILED "resource unavailable" + stats sạch), integration (PLAN §23 2 test đúng tên, INV-016 chain spy acquire→release→acquire→release, duck-typed stub) |
| `tests/test_architecture.py` | +6 | `test_inv016_scheduler_import_allowlist` (pin services.execution CHỈ execution_runner.py — R1-1), `test_inv016_scheduler_call_sites` (3 literal), `test_inv016_scheduler_no_god_object` (no ThreadPool/def execute), `test_inv016_scheduler_no_private_access` (Name._attr — P3-03), `test_inv016_graph_no_scheduler`, `test_inv016_planning_no_scheduler` |
| `tests/test_config.py` | +1 | scheduler block defaults + env override + invalid negative timeout |
| `tests/test_runtime_kernel.py` | +1 | `test_graph_scheduler_wired` (resolve + shared instances + _graph_settings is settings.graph) |

## Kiểm chứng AC (12/12)
- **AC1** ✅ Contracts extra=forbid; ScheduledGraphResult wrap GraphResult thật
- **AC2** ✅ Resource gating: single slot serial; parallel bounded peak==2 ≤ max_concurrent; queue pending≥1 → 0
- **AC3** ✅ Metrics: resource_wait_ms, queue_time_ms==max, peak_slots_used, resource_stats; slots_acquired==2 retries=1
- **AC4** ✅ Timeout: FAILED reason timeout; FAIL_FAST BLOCKED; running==0; pending==0
- **AC5** ✅ Runner raise → slot released (finally)
- **AC6** ✅ Cancel-while-waiting: retries≥1 → CANCELLED; pending==0; cancel delegate
- **AC7** ✅ schedule_plan: resolve default_failure_policy (str→FailurePolicy); override CONTINUE; cycle → GraphValidationError
- **AC8** ✅ ExecutionServiceRunner: 1-node plan đúng, COMPLETED/FAILED, inner/noop, e2e; C1-01 adapter limitation test (max_concurrent=1 → FAILED "resource unavailable", stats sạch)
- **AC9** ✅ INV-016: allow-list pin + call-sites literal + no god object + no private access + graph/planning không import scheduler + behavioral chain spy + duck-typed stub
- **AC10** ✅ Wiring: shared instances (ResourceService/StateService/GraphExecutor) + graph_settings; 1086 pass / 95.22%
- **AC11** ✅ Deterministic: 2 lần chạy (instance mới) y hệt trừ timing
- **AC12** ✅ PLAN §23: A→B→C + A→B, A→C, B/C→D via scheduler — 2 test đúng tên

## Ghi chú / Deviations
1. **Queue/timeout tests cần max_parallel>1** — max_parallel=1 → mỗi wave 1 node → không bao giờ queue (đúng thiết kế wrap).
2. **FakeExecutionService phải chạy runner dict** như ExecutionService thật (inner được invoke).
3. **ExecutionService constructor** (event_service, policy_service, state_service, resource_service) — không có bus param.
4. **ExecutionResult cần execution_id positional**.
5. **Test C1-01 adapter limitation** dùng EventService thật (event_service=None → crash emit).

## Kết luận
- [x] Tất cả 12 AC pass
- [x] Full suite 1086 pass, coverage 95.22%
- [x] INV-016 enforced (AST 6 test + behavioral 2 test); **M5 HOÀN TẤT**
