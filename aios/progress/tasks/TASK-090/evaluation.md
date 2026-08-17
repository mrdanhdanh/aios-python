# TASK-090 — Evaluation (đối chiếu tiêu chí chấp nhận)

> Ngày: 2026-08-17 | Task: M13-P1 Harness Coverage (Issue #9)
> Spec v3 (19 AC — tích hợp resolution critique-1 3 P1/6 P2/3 P3 + critique-2 2 P1/8 P2/10 P3)

## Đối chiếu AC

| # | AC | Kết quả | Bằng chứng |
|---|----|---------|------------|
| AC1 | CoverageDimension 9 chiều | ✅ | TestContracts.test_dimension_enum_9 |
| AC2 | NegativePath 8 paths | ✅ | TestContracts.test_negative_path_enum_8 |
| AC3 | Component 7 (exclude self) | ✅ | TestCoverage.test_components_7_exclude_self |
| AC4 | Contract 21/State 14/Transition 12/Event 6/Failure 8/Scenario 20/Verification 12/Artifact 2 | ✅ | TestCoverage.test_dimensions_total_positive |
| AC5 | Ratios + KHÔNG status | ✅ | TestCoverage.test_report_ratios |
| AC6 | Negative 6/8 + evidence tồn tại | ✅ | TestCoverage.test_negative_6_of_8 |
| AC7 | Readiness 7 dims + overall 6 active + production 0.0 | ✅ | TestReadiness.test_7_dimensions_and_gates |
| AC8 | Fail-closed: replay 0.5 < 0.75 → NOT_READY | ✅ | TestReadiness.test_fail_closed_not_ready + test_ready_when_replay_covered |
| AC9 | Harness id="coverage" registry + lifecycle + round-trip | ✅ | TestWiring + TestHarness.test_get_report_round_trip |
| AC10 | CLI exit 1 (NOT_READY v1) + JSON document | ✅ | TestCLI.test_cli_not_ready_exit_1 + CLI thật |
| AC11 | Fail-closed: strict → DIAGNOSED/FAILED | ✅ | TestHarness.test_full_runner_execute_diagnosed + _failed_no_diagnose |
| AC12 | Full suite + arch-health + doctor | ✅ | 2207 PASS / 0 FAIL; arch-health 0; doctor healthy |
| AC13 | Determinism + cwd-independent | ✅ | TestCoverage.test_determinism + test_evidence_anchored_cwd_independent |
| AC14 | Metrics counts + summary | ✅ | TestCoverage.test_metrics_and_summary |
| AC15 | Registry rỗng không div0 | ✅ | TestCoverage.test_empty_registry_no_div0 |
| AC16 | CoverageError subclass + đủ 9+8 keys | ✅ | TestCoverage.test_keys_9_and_8 |
| AC17 | Production gate conditional | ✅ | TestReadiness.test_production_gate_conditional |
| AC18 | covered=False → evidence "" | ✅ | TestCoverage.test_negative_6_of_8 |
| AC19 | Param validation (0,1] → ValueError | ✅ | TestReadiness.test_param_validation |

**19/19 AC đạt.**

## Đánh giá hệ thống

- **Coverage model 9 chiều** (PLAN §M13-5b): Component/Contract/State/Transition/Event/Failure-mode/Scenario/Verification-path/Artifact — auto-collect từ code thật (registry/lifecycle/verdict/faults/GOLDEN_SCENARIOS) + declared lists có evidence kiểm chứng ✅
- **Negative-path 8**: 6/8 covered (PASS/FAIL/BLOCKED/VIOLATION/TIMEOUT/EXCEPTION); CORRUPTED_EVIDENCE + REPLAY_MISMATCH = False (fail-closed — TASK-091 sẽ cover) ✅
- **Harness Readiness 7 dims** (PLAN §M13-6): Structural/Contract/Behavioral/Failure/Replay/Scenario/Production + hard gates (replay/production/overall) ✅
- **Fail-closed thật**: v1 NOT_READY (replay 0.5 < 0.75) — trust layer KHÔNG tự chứng nhận READY khi còn negative-path chưa chứng minh ✅
- **4 invariant track**: FAIL-CLOSED (INV-035 — verify raise + NOT_READY) ✅ · INDEPENDENT VERIFICATION (chưa — TASK-091) · PERMISSION BOUNDARY (chưa — M14) · CERTIFIED BASELINE/ROLLBACK (chưa — M14)
- **Không phá kiến trúc**: INV-017 (allow-list + importlib/platform), INV-018 (evidence), INV-035; KHÔNG sửa Runtime/Orchestrator; KHÔNG thêm invariant

## Bài học

1. **Critique 2 vòng bắt lỗi thật**: P1-A (evidence path cwd-dependent — chính trust model lại có evidence không tin cậy), P1-B (AC11 sai trạng thái DIAGNOSED), P1-1 (fail-closed NOT_READY không kích hoạt — READY luôn đạt), P1-3 (self-counting — trust layer tự đếm mình).
2. **Layer rule**: `import aios_core` root từ sub-package bị arch-health chặn — dùng `importlib.metadata` + `Path(__file__).parents[4]` (không import root).
3. **Evidence anchored cwd-independent** là bắt buộc cho trust model — nếu không, report phụ thuộc nơi chạy.
4. **Fail-closed thật** (NOT_READY v1) trung thực hơn "READY với điều kiện" — CLI exit 1 mặc định là tín hiệu rõ ràng cho tới khi TASK-091 cover đủ.

## Đề xuất cải tiến

- TASK-091 (P2): Meta-Harness — cover CORRUPTED_EVIDENCE + REPLAY_MISMATCH → negative 8/8 → READY
- M13.1: production tests thật (production dimension có nguồn evidence)
- M16: dsh làm independent verification oracle — củng cố Replay/Verification-path