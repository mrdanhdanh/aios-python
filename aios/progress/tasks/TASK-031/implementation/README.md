# TASK-031 — M6-H3 Test & Simulation — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the
> `harness/testing/` subpackage (single source of truth), not duplicated here.
> Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/harness/testing/contracts.py` — TestLevel 12 + Scenario/ExpectedResult/Fault/SimulationOutcome (extra=forbid) + SimulationStatus 3 state
- `backend/src/aios_core/harness/testing/scenarios.py` — loader dict/json/yaml safe_load + load_many + mode==simulation
- `backend/src/aios_core/harness/testing/faults.py` — `FaultInjector` inject 1 lần + retry/fallback/queued recovery + injected records
- `backend/src/aios_core/harness/testing/simulation.py` — FakeRuntime keyword 7 map + injectable + FakeTool behavior/last_call + `SimulationRunner` (model-first + resource fault node đầu + executed trước attempt + tool_calls mọi attempt cap 100 + policy deny + ERROR khi không recover)
- `backend/src/aios_core/harness/testing/testing.py` — `TestHarness` id=test persist TRƯỚC raise + strict + get_outcome
- `backend/src/aios_core/config.py` — `TestingSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — wiring register "test"

## Key behavior
- Scenario Definition (golden scenario): input + environment(simulation) + expect (intent/agent/policy/capabilities) + verification
- Failure Injection (chaos nhẹ): model timeout / tool failure / resource exhausted → kiểm tra Retry/Fallback/Recovery/Final state
- Simulation Mode: không side effect (FakeRuntime + FakeTool)

## Verification
- `pytest` full suite: **1299 passed, coverage 95.26%, 12/12 AC** (xem `test.md`)
