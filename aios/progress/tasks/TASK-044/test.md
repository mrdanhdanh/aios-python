# TASK-044 — Test report

## Plugin + architecture + API tests

- `backend/tests/test_plugins.py` — 20 tests: compat ranges, full lifecycle 10 states, duplicate/invalid transition, upgrade/rollback manifest restore, dependency check (not installed / version gate), dependent block remove/rollback, provides active-only + restart rebuild, events, concurrency (stale view), registry views, manifest strict + roundtrip.
- `backend/tests/test_architecture.py` — 4 m8_* tests mới: import allow-list, reuse skills state machine, compat fail-fast, provides active-only.
- `backend/tests/test_api.py` — wiring (PluginManager + PluginRegistry trong regs) không phá vỡ.

**115 passed** (subset run trước full suite).

## Full backend regression

- **1584 collected** (baseline 1560 + 24 mới).
- 1 failure duy nhất: `test_planning_engine.py::TestEngine::test_deterministic` — flaky timing `latency_ms` 0/1 (đã ghi nhận ở TASK-043; chạy đơn lẻ PASS). Không liên quan plugins/.
