# Test — TASK-034 (Doctor & Readiness)

## Baseline
- Trước TASK-034: **1450 tests, 95.31%** (commit b8762f1)
- Sau TASK-034: **1521 tests, 95.35%** (+71 test, mục tiêu ≥1520 ✓, coverage ≥90% ✓)

## Test mới
| File | Số test | Phủ |
|------|---------|-----|
| `tests/test_harness_doctor.py` | 66 | contracts 6, checks 10, DoctorHarness 15, scorer 16, ReadinessHarness 14, config+wiring 5 |
| `tests/test_architecture.py` (INV-022a-d) | 5 | no kernel impl, 13 kinds literal, RELEASE BLOCKED + policy_violations, persist-before-raise (rfind) |
| Fix: registry tests | 3 | +doctor +readiness |

## Kết quả
- `pytest -q` full suite: **1521 passed**, coverage **95.35%**; arch 70 passed

## Ghi chú
- early-return raise (no results) đứng trước persist → arch dùng rfind
- empty results + min_overall 0.0 → ready True (0.0 >= 0.0) — test phải khớp
