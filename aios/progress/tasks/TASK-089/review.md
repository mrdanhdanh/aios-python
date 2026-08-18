# Review — TASK-089 (M13-P0: Behavioral Conformance) — Pre-implementation Review

> Review trước implement — 2026-08-17
> Spec v3 (17 AC — tích hợp resolution critique-1 6 P1/8 P2/9 P3 + critique-2 2 P1/5 P2/10 P3) + tasks.md breakdown.

## Đánh giá tổng quan

Task xây dựng **Behavioral Conformance Engine** — chạy scenario N lần (quick=100/standard=1k/stress=10k/soak=duration) + repeat + fault-inject + evidence compare + regression gate — tái dùng `SimulationRunner`/`FaultInjector`/`RegressionGate`/`HarnessRunner`, mở rộng tối thiểu `Fault.recoverable` (backward-compatible). Module mới `harness/behavioral/` (tránh trùng `certification/conformance.py`), harness id="behavioral", CLI group `harness` mới.

## Kiểm tra spec

- **Mục tiêu khớp PLAN §M13 P0**: Behavioral Conformance ladder (behavioral/temporal/load/soak/failure-recovery) ✅
- **Tái dùng đúng**: SimulationRunner (deterministic, không side-effect), FaultInjector, RegressionGate, HarnessRunner lifecycle, fail-closed INV-035 ✅
- **Không phá kiến trúc**: KHÔNG sửa Runtime/Orchestrator (INV-017..021); KHÔNG thêm invariant (INV-001..035 frozen) ✅
- **2 vòng critique đã resolve**: P1-1 (MISMATCH→PASS false positive), P1-2 (ERROR unreachable → Fault.recoverable), P1-3 (gate chỉ expose + aggregation), P1-4 (repeat ≠ replay_verdict), P1-5 (scenario full object), P1-6 (CLI group harness mới); vòng 2: P1-1 (gate dedup → aggregation), P1-2 (repeat_consistent bool|None) ✅
- **AC đo được**: 17 AC — mỗi AC có cách kiểm chứng cụ thể, không vacuous (AC11/AC13 đã trace qua code thật) ✅

## Điểm cần lưu ý khi implement

1. **R1 (review)**: `FaultInjector.next_for` sửa — phải giữ hành vi cũ cho `recoverable=True` (count-based); test cũ `test_timeout_fault_recovers`/`test_inject_once_then_none` không được phá.
2. **R2 (review)**: `ConformanceConfig.scenario: Scenario` — CLI build dict `scenario.model_dump(mode="json")`; Scenario extra="forbid" — không truyền key thừa.
3. **R3 (review)**: aggregation gate — quality = tỷ lệ iteration SUCCESS (không phải nhị phân 1.0/0.0); dùng chung cho `--save-baseline`.
4. **R4 (review)**: `repeat_samples` cap `min(repeat_samples, iterations)`; `repeat_ok` default None cho iteration không repeat.
5. **R5 (review)**: fail-fast `fault_iterations` index > iterations_total → raise `BehavioralConformanceError`.
6. **R6 (review)**: persist report qua `state_service` (pattern TestHarness) + `get_report(run_id)` — report phải truy xuất được (trust infrastructure).
7. **R7 (review)**: cập nhật PLAN.md §M13 P0 ghi chú deviation gate-as-blocker defer M14.

## Kết luận

- [x] **APPROVED** — spec v3 đủ chặt, tasks.md đủ chi tiết, không còn P1/P2 chưa resolve. Được phép implement.
- Lưu ý: implement theo thứ tự tasks.md; chạy test file mới + full suite + arch-health + doctor trước khi đánh dấu done.