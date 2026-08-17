# TASK-089 — Tasks breakdown (checklist)

> M13-P0 Behavioral Conformance — spec v3 (17 AC). Dependency: P0 → P1 (TASK-090).

## 1. Mở rộng tối thiểu Fault (P1-2 v1)

- [ ] `harness/testing/contracts.py`: thêm `recoverable: bool = True` vào `Fault` (backward-compatible)
- [ ] `harness/testing/faults.py`: sửa `FaultInjector.next_for` — fault `recoverable=False` trả mọi lần (không check count)
- [ ] Kiểm tra không phá `test_timeout_fault_recovers`/`test_inject_once_then_none`

## 2. Module `harness/behavioral/`

- [ ] `errors.py`: `BehavioralConformanceError(HarnessError)`
- [ ] `contracts.py`: `ConformanceProfile`, `ConformanceStatus`, `ConformanceConfig` (validators: fault_iterations dedup + index>=1 + faults non-empty khi fault_iterations non-empty; iterations>=1), `ConformanceIterationSummary` (repeat_ok: bool|None), `ConformanceReport` (deterministic, repeat_consistent, fault_recovery_rate, iterations, metrics, findings, gate, summary, reproducible)
- [ ] `engine.py`: `PROFILE_ITERATIONS` + `BehavioralConformanceEngine` (runner injectable, soak_max_iterations param) — run(): resolve iterations → loop N lần (scenario copy + fault schedule + outcome + digest + repeat cho ≤ repeat_samples) → phân tích (deterministic/repeat_consistent/recovery_rate/hành vi ĐÚNG/status) → gate aggregation (quality = tỷ lệ SUCCESS, failed, policy_violations) → report
- [ ] `harness.py`: `BehavioralConformanceHarness` (id="behavioral") — run/verify/_persist/get_report (state_service)
- [ ] `__init__.py`: export public API

## 3. Wiring

- [ ] `kernel/runtime_kernel.py`: đăng ký `BehavioralConformanceHarness` (id="behavioral") + truyền StateService

## 4. CLI

- [ ] `workflow/cli.py`: parser group `harness` + subcommand `behavioral` (flags: --profile/--scenario-file/--iterations/--duration/--faults/--fault-iterations/--repeat-samples/--baseline/--save-baseline/--no-strict)
- [ ] Dispatch `if args.command == "harness" and args.harness_command == "behavioral"` → `_harness_behavioral()` (lazy import, json.loads + isinstance list check, exit 0/1, JSON 1 dòng)

## 5. Tests `tests/test_harness_behavioral.py`

- [ ] TestContracts: pydantic defaults + extra="forbid" + validators
- [ ] TestEngine: profile resolution (AC1), soak (AC2), deterministic (AC3), evidence digest (AC4), repeat (AC5), fault mọi iteration + fault_iterations (AC6), gate aggregation (AC7), report fields (AC8), ERROR recoverable=False (AC11), MISMATCH → FAIL (AC13), scenario từ file (AC14), cross-run (AC15)
- [ ] TestHarness: run/verify strict raise → FAILED (AC17a), strict=False → COMPLETED (AC17b), persist + get_report (AC9)
- [ ] TestWiring: RuntimeKernel.create() → registry có behavioral (AC9)
- [ ] TestCLI: `aiagent harness behavioral` PASS exit 0 / FAIL exit 1 / JSON 1 dòng (AC10), --save-baseline (AC16)

## 6. Verify

- [ ] Chạy test file mới: tất cả PASS
- [ ] Chạy full suite: không regression (AC12)
- [ ] `aiagent arch-health`: 0 violations
- [ ] `aiagent doctor`: healthy
- [ ] CLI thật: `aiagent harness behavioral --scenario-file <tmp.yaml> --profile quick` → PASS exit 0

## 7. Docs & DoD

- [ ] Cập nhật PLAN.md §M13 P0: ghi chú deviation gate-as-blocker defer M14 (R7)
- [ ] Cập nhật PROGRESS.md + LOG.md
- [ ] Commit