# Test — TASK-030 (Execution Verification)

## Baseline
- Trước TASK-030: **1124 tests, 95.20%** (commit b62ac75)
- Sau TASK-030: **1210 tests, 95.26%** (+86 test, mục tiêu ≥1169 ✓, coverage ≥90% ✓)

## Test mới
| File | Số test | Phủ |
|------|---------|-----|
| `tests/test_harness_execution.py` | 80 | contracts 10, evidence 15, run_checks 17, compute_verdict/build_result 14, replay 6, VerificationHarness 14, config+wiring 4 |
| `tests/test_architecture.py` (INV-019) | 6 | no kernel impl, duck-typing, verdict FAIL raise, verdict order, persist-before-raise, verdict.json convention |

## Kết quả
- `pytest -q` full suite: **1210 passed** (0 failed), coverage **95.26%**
- Arch tests: 53 passed (INV-017/018/019)

## Ghi chú kỹ thuật
- `_collect_events` candidates = {ref, ref.removeprefix("graph:")} — graph runs emit execution_id "g1" hoặc "graph:g1"
- `_resolve_state_key` namespace theo dạng ref (graph: → graph; else plan) — bug C1-01 cũ trả "plan" cho mọi key
- Replay critical flag: persisted dict có `critical_evidence` — ưu tiên flag, fallback tái tính
- Test graph verify: `HarnessRunner(..., diagnose_on_failure=False)` để assert FAILED (mặc định DIAGNOSED)
