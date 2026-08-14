# TASK-028 — Evaluation (Parallel Scheduler)

**Ngày**: 2026-08-15 | **Trạng thái**: DONE ✅

## Đối chiếu tiêu chí chấp nhận (12/12 AC pass — xem test.md)

| AC | Kết quả | Bằng chứng |
|----|---------|------------|
| AC1 Contracts | ✅ | TestContracts |
| AC2 Gating | ✅ | TestScheduler serial/bounded/queue |
| AC3 Metrics | ✅ | TestScheduler metrics/retries |
| AC4 Timeout | ✅ | test_timeout_fail |
| AC5 Release | ✅ | test_runner_raise_releases_slot |
| AC6 Cancel | ✅ | test_cancel_while_waiting |
| AC7 schedule_plan | ✅ | resolve/override/cycle |
| AC8 Runner + C1-01 | ✅ | TestExecutionRunner + TestAdapterLimitation |
| AC9 INV-016 | ✅ | 6 arch test + behavioral |
| AC10 Wiring | ✅ | test_graph_scheduler_wired + 1086/95.22% |
| AC11 Deterministic | ✅ | 2 lần chạy instance mới |
| AC12 PLAN §23 | ✅ | 2 test đúng tên via scheduler |

## Đánh giá so với PLAN.md §M5-18..25
- **Parallel Scheduler** (§18): trả lời "Task nào chạy đồng thời?" — dependency (READY từ 027) ∧ resource (ResourceService FIFO slot — F-003)
- **Scheduler Architecture** (§19): 5 vai tách bạch — GraphScheduler (dependency + resource timing) → ResourceService (resource) → ExecutionService (execution) → StateService (state); SchedulerService kỹ thuật không tương tác
- **INV-016 Scheduler Separation** (§22): Scheduler không sở hữu Resource/Execution implementation — AST 6 test (allow-list pin execution_runner, call-sites literal, no private access, no ThreadPool) + behavioral (chain spy + duck-typed stub)
- **Test strategy** (§23): A→B→C + fork-join verified qua scheduler
- **Observability** (§25): queue time, peak slots, resource stats trong ScheduledGraphResult + state scheduler_metrics
- **M5 Flow** (§20): pipeline đầy đủ — Planning (026) → Graph (027) → Scheduler (028) — nối qua `schedule_plan`

## Bài học
1. **max_parallel=1 → queue không bao giờ xảy ra** — test queue/timeout phải cấu hình max_parallel>1 + max_concurrent hữu hạn (cả 2 mới exercise gating)
2. **Double-slot với adapter là hard limitation** (ExecutionService acquire_slot non-blocking nội bộ) — phải test tường minh + document, không "sửa"
3. **Poll thay đo 1 lần** cho queue observability (thread scheduling lag)
4. **wiring graph_settings bắt buộc** để config default_failure_policy có tác dụng thật (C1-02 — critic bắt 2 lần)
5. **Retry nhân đôi (retries+1)²** khi adapter + GraphExecutor outer — document, khuyến nghị retries=0
6. **Cancel-while-waiting**: worker chỉ check flag giữa attempts → retries=0 → FAILED timeout (không CANCELLED) — semantic phải ghi rõ

## Kết luận
- [x] ĐẠT spec (12/12 AC)
- [x] INV-016 enforced đa tầng; additive only
- [x] **M5 Core Intelligence HOÀN TẤT** — 6 task (023..028), 1086 pass, coverage 95.22%, INV-011..016 enforced

## Ghi nhận M5 (toàn milestone)
- TASK-023 Memory Coordinator (INV-011) — 855 pass
- TASK-024 Context Optimizer (INV-012) — 896 pass
- TASK-025 Model Router (INV-013) — 949 pass
- TASK-026 Planning Engine (INV-014) — 1003 pass
- TASK-027 Execution Graph (INV-015) — 1055 pass
- TASK-028 Parallel Scheduler (INV-016) — 1086 pass
