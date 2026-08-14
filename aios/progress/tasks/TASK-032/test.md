# Test — TASK-032 (Evaluation Harness)

## Baseline
- Trước TASK-032: **1299 tests, 95.26%** (commit c543816)
- Sau TASK-032: **1387 tests, 95.27%** (+88 test, mục tiêu ≥1370 ✓, coverage ≥90% ✓)

## Test mới
| File | Số test | Phủ |
|------|---------|-----|
| `tests/test_harness_evaluation.py` | 84 | contracts 12, deterministic 7, semantic 5, LLM 4, human 3, composite 3, engine 7, trajectory 9, suites 10, harness 21, config+wiring 5 |
| `tests/test_architecture.py` (INV-020e-h) | 4 | no kernel/models imports, reproducible literal, Engine+EvaluationError, safe_load |
| Fix: `tests/test_harness_testing.py` | 1 | registry giờ 3 harnesses |

## Kết quả
- `pytest -q` full suite: **1387 passed**, coverage **95.27%**; arch 61 passed

## Ghi chú
- Score.kind cần default (ValidationError khi tạo Score(metric, threshold) — thêm default DETERMINISTIC)
- Aggregate mean: None values bị skip; all-None → Score.value None → INCONCLUSIVE (R2-2)
- INV-020e cho phép StateService (allow-list H1) — chỉ cấm execution/events/graph/planning/models
