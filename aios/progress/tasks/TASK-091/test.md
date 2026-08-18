# TASK-091 — Test results (thật)

> Ngày: 2026-08-17 | Task: M13-P2 Meta-Harness (Issue #9)
> Môi trường: Windows, Python venv backend/.venv, pytest + coverage

## Test file mới: `backend/tests/test_harness_meta.py` — 27 test

| Class | Số test | Nội dung | AC |
|-------|---------|----------|----|
| TestContracts | 5 | MetaCase enum 8, MetaOracle enum 5, MetaCaseResult extra="forbid", MetaReport extra="forbid", report KHÔNG có timestamp | AC1, AC10 |
| TestEngine | 13 | all 8 fail_closed=True + status PASS, FALSE_POSITIVE→inconclusive (AC2), FALSE_NEGATIVE→fail (AC3), MALFORMED_EVIDENCE→inconclusive (AC4), BROKEN_VERIFIER detected (AC5), CORRUPTED_ARTIFACT (AC6), REPLAY_MISMATCH TAMPER (AC7), SKIPPED_VERIFICATION INV-035 (AC8), VERIFY_SKIPPED detected (AC9), metrics keys (P3-3), reproducible no timestamp (P3-2) | AC2-9, P3-2/3 |
| TestIndependentOracle | 2 | monkeypatch module-level compute_verdict luôn PASS → case 1 fail_closed=False → status FAIL (AC16 scenario b), engine reference pipeline.compute_verdict | AC16 |
| TestHarness | 7 | id/name/version, registry, run payload 8 cases, verify strict PASS (không raise), full runner execute COMPLETED/DIAGNOSED (AC11/AC12), get_report round-trip | AC11, AC12 |
| TestWiring | 1 | RuntimeKernel registry có id="meta" + 9 harness | AC11 |
| TestCLI | 2 | `harness meta` exit 0 + status pass (AC13), `--no-strict` exit 0 | AC13 |

## Cập nhật `backend/tests/test_harness_coverage.py` — 4 test rename + make_registry + 3 test READY

- `make_registry()` thêm `MetaHarness()` → component total 7→8 (P2-1)
- `test_components_7_exclude_self` → `test_components_8_exclude_self` (assert `comp.total == 8`)
- `test_negative_6_of_8` → `test_negative_8_of_8` (assert 8/8, ratio 1.0) (P3-1)
- `test_fail_closed_not_ready` → `test_ready_when_meta_covered` (replay 1.0, overall 1.0, READY) (P3-1)
- `test_metrics_and_summary` → "negative 8/8" (P1-2)
- 7 test Harness/CLI cập nhật NOT_READY → READY (TASK-091 makes coverage READY):
  - `test_run_returns_payload` → status "ready"
  - `test_verify_not_ready_raises` → `test_verify_ready_no_raise` (strict không raise khi ready)
  - `test_get_report_round_trip` → readiness_status "ready"
  - `test_full_runner_execute_diagnosed` → `test_full_runner_execute_completed` (status COMPLETED)
  - `test_full_runner_execute_failed_no_diagnose` → `test_full_runner_execute_completed_no_diagnose` (COMPLETED)
  - `test_registry_has_coverage` → assert `len(reg.list()) == 9` (9 harness runtime)
  - `test_cli_not_ready_exit_1` → `test_cli_ready_exit_0` (rc 0, status ready)

## Kết quả chạy thật

- **Test file mới (meta): 27/27 PASS**
- **Test coverage (cập nhật): 35/35 PASS** (tất cả test cũ + 4 rename + 7 READY update)
- **Sửa INV-017**: engine + harness import `StateService` từ `aios_core.kernel.services.state` (submodule) thay vì `aios_core.kernel.services` (package) — scanner allow-list submodule, không flag vi phạm. `arch-health: healthy true, violations []` ✅
- **4 test registry cập nhật** (do thêm harness id="meta" → 9 harness runtime):
  - `test_harness_{benchmark,doctor,evaluation,testing}.py::TestConfigWiring::test_harness_registry_all_m6` — thêm `"meta"` vào set kỳ vọng
- **Full suite: 2234 PASS / 0 FAIL** (scope run: 2230 + 4 registry update = 2234; coverage 92.96% ≥ 80%) — 0 regression (AC12/AC14)
- **arch-health**: `healthy: true, violations: []` (AC14) ✅
- **doctor**: healthy (AC14) ✅
- **CLI thật**:
  - `aiagent harness meta` → status pass + **exit 0** (AC13)
  - `aiagent harness meta --no-strict` → exit 0 (AC13)
  - `aiagent harness coverage` → status ready + **exit 0** (AC15 — READY)

## Ghi chú

- Oracle hardcode (MetaOracle enum) — engine KHÔNG gọi verifier production để tính expected_state (chống circular P2-1)
- Engine reference `pipeline.compute_verdict` (module-level) → monkeypatch `aios_core.harness.execution.pipeline.compute_verdict` hoạt động (AC16 scenario b đạt)
- `has_critical_evidence(evidence)` gọi TRƯỚC `pipeline.compute_verdict` (P3-5)
- BROKEN_VERIFIER + VERIFY_SKIPPED = scenario (a): Meta PHÁT HIỆN verifier hỏng/skip → fail_closed=True → suite có thể PASS (P1-1 fix)
- Scenario (b) — verifier dưới test không fail-closed → Meta FAIL → đẩy vào AC16 negative test (không nằm trong 8-case live)
- INV-017: import `StateService` từ submodule `aios_core.kernel.services.state` (cho phép); `hashlib`/`importlib.metadata`/`platform` đã trong allow-list từ TASK-089/090
