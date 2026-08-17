# TASK-089 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-17 | Task: M13-P0 Behavioral Conformance (Issue #9)
> Spec v3 (17 AC — tích hợp resolution critique-1 6 P1/8 P2/9 P3 + critique-2 2 P1/5 P2/10 P3)

## Đối chiếu AC

| # | AC | Kết quả | Bằng chứng |
|---|----|---------|------------|
| AC1 | Profile resolution quick=100/std=1k/stress=10k + override | ✅ | TestEngine.test_profile_quick_iterations + test_iterations_override_profile |
| AC2 | Soak duration-based + cap | ✅ | TestEngine.test_soak_duration_based/zero/cap |
| AC3 | Deterministic N lần không fault | ✅ | TestEngine.test_deterministic |
| AC4 | Evidence digest sha256 giống nhau | ✅ | TestEngine.test_evidence_digest_same |
| AC5 | Repeat double-run + repeat_consistent (bool\|None) | ✅ | TestEngine.test_repeat_consistent + test_repeat_samples_cap |
| AC6 | Fault mọi iteration + fault_iterations subset | ✅ | TestEngine.test_fault_recovery_rate_1 + test_fault_iterations_subset |
| AC7 | Gate aggregation + expose (không quyết định status) | ✅ | TestEngine.test_gate_exposed_not_blocking + test_gate_blocked_finding_only |
| AC8 | Report fields + metrics counts | ✅ | TestEngine.test_report_fields |
| AC9 | Harness id="behavioral" registry + lifecycle + persist | ✅ | TestWiring + TestHarness.test_full_runner_execute_pass + test_get_report |
| AC10 | CLI PASS exit 0 / FAIL exit 1 / JSON 1 dòng | ✅ | TestCLI.test_cli_pass_exit_0 + test_cli_fail_exit_1 + CLI thật exit 0 |
| AC11 | Fail-closed: Fault(recoverable=False) → ERROR | ✅ | TestEngine.test_non_recoverable_fault_error |
| AC12 | Full suite không regression + arch-health + doctor | ✅ | 2172 PASS / 0 FAIL; arch-health 0 violations; doctor healthy |
| AC13 | Hành vi ĐÚNG: MISMATCH → FAIL (dù deterministic) | ✅ | TestEngine.test_mismatch_fails |
| AC14 | Resolve scenario từ file yaml/json | ✅ | TestEngine.test_scenario_from_yaml_file + TestCLI.test_cli_missing_scenario_file |
| AC15 | Temporal determinism cross-run | ✅ | TestEngine.test_cross_run_deterministic |
| AC16 | --save-baseline ghi Baseline đúng format | ✅ | TestCLI.test_cli_save_baseline + TestEngine.test_build_baseline |
| AC17 | Verify fail-closed: strict raise → FAILED; not-strict → COMPLETED | ✅ | TestHarness.test_verify_fail_raises_and_persists + test_verify_not_strict_no_raise + test_full_runner_execute_fail_closed |

**17/17 AC đạt.**

## Đánh giá hệ thống

- **Behavioral Conformance ladder (PLAN §M13-5)**: Behavioral (hành vi ĐÚNG — AC13) ✅ · Temporal (N lần + repeat — AC3/5/15) ✅ · Load (stress=10k profile) ✅ · Soak (duration-based loop-stability) ✅ · Failure Recovery (fault-inject + recoverable/non-recoverable — AC6/11) ✅
- **4 invariant track giữ nguyên**: FAIL-CLOSED (verify raise + ERROR không PASS — AC11/17) ✅ · INDEPENDENT VERIFICATION (chưa — thuộc TASK-091) · PERMISSION BOUNDARY (chưa — thuộc M14) · CERTIFIED BASELINE/ROLLBACK (chưa — thuộc M14)
- **Không phá kiến trúc**: INV-017 (allow-list + hashlib), INV-018 (evidence qua HarnessRunner), INV-035 (fail-closed); KHÔNG sửa Runtime/Orchestrator; KHÔNG thêm invariant
- **Tái dùng**: SimulationRunner, FaultInjector (mở rộng tối thiểu recoverable), RegressionGate, HarnessRunner lifecycle, scenarios.load

## Bài học

1. **Critique 2 vòng bắt được lỗi thật**: P1-1 (MISMATCH→PASS false positive), P1-2 (ERROR unreachable — dead code trong SimulationRunner), P1-1 v2 (gate dedup N→1 RunResult), P1-2 v2 (repeat_consistent mâu thuẫn) — nếu không critique, engine sẽ cho PASS sai.
2. **Mở rộng tối thiểu backward-compatible** (Fault.recoverable default True) — không phá test cũ, đúng nguyên tắc "không tạo hệ thống song song".
3. **Gate với runner deterministic là vô nghĩa** — quyết định đúng: chỉ expose, defer blocker cho M14 (khi có nhiều scenario + real metrics).
4. **Soak với runner thuần chỉ là loop-stability** — cần thành thật về giới hạn (M13.1 cho leak/latency thật).

## Đề xuất cải tiến

- TASK-090 (P1): coverage model 9 chiều + negative-path — dùng report behavioral làm input
- TASK-091 (P2): Meta-Harness — repeat/evidence digest là nền cho tamper detection
- M14: gate-as-blocker + certified baseline (nhiều scenario + real metrics)