# TASK-043 — Test report

## SDK tests

Command: backend/.venv/Scripts/python -m pytest sdk/python/tests -q với `PYTHONPATH=sdk/python/src`

- **5 passed**
- Bao phủ public import, component validation, capability requirement, DTO round-trip/unknown fields, DAG cycle và injected transport client.

## Backend regression

Đã chạy task `Test: run pytest backend`.

- 1560 tests collected.
- Có 1 failure không liên quan SDK: `tests/test_planning_engine.py::TestEngine::test_deterministic` do `latency_ms` timing thực tế khác nhau (`0` và `1`).
- SDK không sửa backend và không tạo lỗi import/runtime trong backend.
