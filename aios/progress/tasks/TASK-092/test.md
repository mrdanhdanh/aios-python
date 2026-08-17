# TASK-092 — Test results (thật)

> Ngày: 2026-08-18 | Task: M13-P3 Trust Separation (Issue #8)
> Môi trường: Windows, Python venv backend/.venv, pytest + coverage

## Test file mới: `backend/tests/test_harness_release.py` — 20 test

| Class | Số test | Nội dung | AC |
|-------|---------|----------|----|
| TestIndependentScores | 1 | Hai type riêng + enum values | AC1 |
| TestEnginePure | 1 | Pure function, deterministic | AC2 |
| TestGatePass | 1 | Cả 2 PASS → PASS | AC3 |
| TestGateBlockedReadiness | 1 | NOT_READY → BLOCKED (chứng minh readiness một mình không đủ) | AC4 |
| TestGateBlockedTrust | 1 | FAIL → BLOCKED (chứng minh trust một mình không đủ) | AC5 |
| TestReportShape | 2 | Shape 6 fields + no timestamp + extra="forbid" | AC6 |
| TestDeterminism | 1 | evaluate 2 lần → identical | AC11 |
| TestSeparationReal | 1 | 2 path BLOCKED độc lập + summary khác nhau | AC12 |
| TestHarness | 8 | id/name/version, pass, blocked (fake), strict raises, not-strict no raise, strict pass, round-trip, diagnosed, completed | AC7, AC8 |
| TestWiring | 1 | Runtime registry có 10 harness | AC7 |
| TestCLI | 1 | CLI exit 0 (PASS) + JSON | AC9 |

## Kết quả chạy thật

- **Test file mới: 20/20 PASS**
- **Cập nhật 5 test cũ** (thêm "release" → 10 harness):
  - 4 `test_harness_{benchmark,doctor,evaluation,testing}.py::test_harness_registry_all_m6` — set 10
  - `test_harness_coverage.py::test_registry_has_coverage` — assert `len==10`
- **Sửa INV-017**: KHÔNG cần (release chỉ import contracts/ABC/Runner)
- **Full suite: 2254 PASS / 0 FAIL** (coverage 92.92% ≥ 80%) — 0 regression (AC10)
- **arch-health**: `healthy: true, violations: []` (AC10) ✅
- **doctor**: healthy (AC10) ✅
- **CLI thật**: `aiagent harness release` → status pass + **exit 0** (AC9) ✅
- **Release gate output**: system_readiness=ready + harness_trust=pass + both_pass=true → RELEASE PASS

## Ghi chú

- Fake sub-harnesses (_FakeCoverageHarness/_FakeMetaHarness) trả NOT_READY/PASS → test BLOCKED path
- Real coverage harness ALWAYS READY (code constants) → PASS path dùng real registry
- Engine là pure combiner — KHÔNG import readiness scorer/meta engine (chống circular)
- `fail_closed` ở release gate = "nếu bất kỳ score fail → BLOCKED" (fail-closed INV-035)
