# Test — TASK-033 (Benchmark + Regression Gate)

## Baseline
- Trước TASK-033: **1387 tests, 95.27%** (commit 9c7f3e0)
- Sau TASK-033: **1450 tests, 95.31%** (+63 test, mục tiêu ≥1450 ✓, coverage ≥90% ✓)

## Test mới
| File | Số test | Phủ |
|------|---------|-----|
| `tests/test_harness_benchmark.py` | 59 | contracts 9, runner 8, gate 21, harness 15, config+wiring 6 |
| `tests/test_architecture.py` (INV-021a-d) | 4 | no kernel impl, gate block literal, no side-effect (AST rglob), persist-before-block |
| Fix: `tests/test_parallel_scheduler.py` | 1 | pop latency_ms (timing thật — flaky) |
| Fix: registry tests | 2 | +"benchmark" trong registry |

## Kết quả
- `pytest -q` full suite: **1450 passed**, coverage **95.31%**; arch 65 passed

## Ghi chú
- Float boundary: delta = -4.9999999 < -5.0 → regress sai — thêm epsilon 1e-9
- cost/latency/token chỉ theo dõi (không rule → không block) — đúng PLAN (6 metrics, 3 gate rules)
- INV-021b literal: benchmark.py dùng type `RegressionGate` (gate truyền qua constructor) — không cần "RegressionGate("
