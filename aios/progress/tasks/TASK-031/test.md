# Test — TASK-031 (Test & Simulation)

## Baseline
- Trước TASK-031: **1210 tests, 95.26%** (commit 117fbfe)
- Sau TASK-031: **1299 tests, 95.26%** (+89 test, mục tiêu ≥1290 ✓, coverage ≥90% ✓)

## Test mới
| File | Số test | Phủ |
|------|---------|-----|
| `tests/test_harness_testing.py` | 85 | contracts 11, loader 10, faults 11, runtime/tool 11, runner 20, TestHarness 14, config+wiring 6 |
| `tests/test_architecture.py` (INV-020a-d) | 4 | no kernel impl, no side-effect imports (AST), TestHarness runner+raise, loader safe_load |

## Kết quả
- `pytest -q` full suite: **1299 passed** (0 failed), coverage **95.26%**
- Arch tests: 57 passed (INV-017/018/019/020)

## Ghi chú kỹ thuật
- Fault injector: fault raise TRƯỚC call_fn → tool_calls chỉ ghi attempt thành công (retry)
- `apply` trả tuple (result, recovered) — runner phải unpack
- Node model targets = ["resource","model"] khi đầu — chọn target có fault trước (fix bug chỉ thử target đầu)
- Scenario.input request bắt buộc ở LOADER (model cho phép input {})
- PytestCollectionWarning TestLevel (str Enum có __init__) — vô hại
