# Tasks — TASK-031 (H3 Test & Simulation)

> Spec v3 (critique ×2 resolved). Trạng thái cập nhật theo tiến độ.

- [ ] **T1** contracts.py — TestLevel 12, FaultType, Fault, ExpectedResult, Scenario, SimulationStatus, SimulationOutcome (extra=forbid; P1-02 bỏ BLOCKED; metrics counts-only)
- [ ] **T2** errors.py — ScenarioError/SimulationError/TestError
- [ ] **T3** scenarios.py — ScenarioLoader: load (dict/json/yaml safe_load), load_many (list | `scenarios:` key), lỗi → ScenarioError; validate environment.mode == "simulation" (P2-05)
- [ ] **T4** faults.py — FaultInjector: next_for(target), apply(target, call_fn) — TIMEOUT retry / FAILURE fallback / EXHAUSTED queued-retry; attempts = retries+1; recovery_events; hết attempts → raise
- [ ] **T5** simulation.py — FakeRuntime (intent/agent/policy/capabilities injectable + defaults keyword), FakeTool (behavior dict, run deterministic), SimulationRunner.run: pipeline 5 bước, policy deny (P1-02), node model luôn đầu (C1-02), resource fault tại node đầu (P1-01), executed_nodes trước attempt, tool_calls mọi attempt (P1-03), expectation_matches, verification (P2-03), status
- [ ] **T6** testing.py — TestHarness (id="test", H1 kế thừa): run (scenario từ config, runtime override P2-01), verify persist TRƯỚC raise (key "testing"), strict=False → WARNING (P2-04), get_outcome (P3-05)
- [ ] **T7** __init__.py exports + config TestingSettings (default_retries/strict/simulation_timeout_s) + config.yaml `testing:` + wiring runtime_kernel (register "test")
- [ ] **T8** tests/test_harness_testing.py — ≥80 test (AC1..AC11): contracts 10, loader 10, faults 12, runtime/tool 10, runner 18, harness 15, config/wiring 5
- [ ] **T9** arch tests INV-020a..d (no kernel impl, no side-effect imports, TestHarness literal, +yaml external allow-list)
- [ ] **T10** Full suite: tổng ≥1290 tests, coverage ≥90%; hồ sơ test.md/evaluation.md + LOG/PROGRESS + commit
