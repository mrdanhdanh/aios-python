# TASK-090 — Test results (thật)

> Ngày: 2026-08-17 | Task: M13-P1 Harness Coverage (Issue #9)
> Môi trường: Windows, Python venv backend/.venv, pytest + coverage

## Test file mới: `backend/tests/test_harness_coverage.py` — 35 test

| Class | Số test | Nội dung | AC |
|-------|---------|----------|----|
| TestContracts | 8 | CoverageDimension 9, NegativePath 8, extra="forbid", DimensionCoverage ratio, report extra | AC1-2 |
| TestCoverage | 12 | Component 7 exclude self (AC3), dimensions total (AC4: contract 21/state 14/transition 12/event 6/failure 8/scenario 20/verification 12/artifact 2), ratios + no status (AC5), negative 6/8 + evidence check (AC6/18), cwd-independent (AC13), determinism (AC13), empty registry no div0 (AC15), metrics/summary (AC14), keys 9+8 (AC16), reproducible | AC3-6, 13-16, 18 |
| TestReadiness | 7 | 7 dims + overall 6 active (AC7), fail-closed NOT_READY replay 0.5 (AC8), READY khi replay covered (AC8), production gate conditional (AC17), param validation (AC19), reproducible | AC7-8, 17, 19 |
| TestHarness | 9 | id/version, registry, run payload, verify raise + persist (AC11), not-strict, get_report round-trip (AC9), DIAGNOSED/FAILED (AC11) | AC9, 11 |
| TestWiring | 1 | Registry có coverage + 8 harness (AC9) | AC9 |
| TestCLI | 2 | NOT_READY exit 1 + JSON (AC10), min-replay 0.4 → READY exit 0 (AC10) | AC10 |

## Kết quả chạy thật

- **Test file mới: 35/35 PASS** (lần đầu 8 pass + 27 fail do: VerificationHarness signature, `mid=`/`vid=` sai tên tham số, GoldenScenario.gs_id, make_registry thiếu ReadinessHarness, component evidence sai module → sửa → 35/35)
- **Full suite: 2207 PASS / 0 FAIL** (2172 + 35 mới; coverage 92.96% ≥ 80%) — 0 regression (AC12)
- **5 test cũ cần cập nhật** (do thêm harness id="coverage"):
  - `test_architecture.py::test_inv017_harness_import_allowlist` — thêm `importlib` + `platform` vào `_HARNESS_ALLOWED_EXTERNAL`
  - 4 test `test_harness_{benchmark,doctor,evaluation,testing}.py::TestConfigWiring::test_harness_registry_all_m6` — thêm `"coverage"` vào set kỳ vọng (8 harness)
- **arch-health**: `healthy: true, violations: []` (AC12) — đã sửa `import aios_core` root (layer rule) → `importlib.metadata` + `Path(__file__).parents[4]`
- **doctor**: healthy (AC12)
- **CLI thật**: `aiagent harness coverage` → NOT_READY + **exit 1** (fail-closed v1 — AC10); `--min-replay 0.4` → READY + exit 0

## Ghi chú

- Coverage v1 = declared + auto-collect (KHÔNG quét test files — test count ≠ coverage)
- Negative 6/8 (CORRUPTED_EVIDENCE + REPLAY_MISMATCH = False — cần TASK-091)
- Evidence anchored backend root (cwd-independent) — module find_spec / path Path.exists
- Production = 0.0 + excluded overall v1 (chưa có nguồn evidence — M13.1/M16)