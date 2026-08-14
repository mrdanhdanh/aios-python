# Tasks + Review — TASK-033 (Benchmark + Regression Gate)

## Tasks
- [ ] **T1** contracts.py — BenchmarkMetric 6, RunResult, Baseline, RegressionRule/Finding, BenchmarkReport (extra=forbid)
- [ ] **T2** errors.py — BenchmarkError + GateBlockedError(BenchmarkError)
- [ ] **T3** runner.py — BenchmarkRunner(run_fn, max_scenarios): run(ids) → (results, aggregate 6 metrics); cap slice; deterministic
- [ ] **T4** gate.py — RegressionGate(rules | default 3 từ settings): evaluate(new, baseline) → report; subset chung sort; delta % / pp; bảng hướng; baseline==0 → 0; findings rỗng → gate_passed True; can_release
- [ ] **T5** benchmark.py — BenchmarkHarness (id="benchmark"): run (ids + baseline từ config), verify persist TRƯỚC raise GateBlockedError, strict flag, get_report
- [ ] **T6** __init__ + config BenchmarkSettings + config.yaml + wiring register "benchmark"
- [ ] **T7** tests/test_harness_benchmark.py — ≥60 test (AC1..AC10): contracts 8, runner 10, gate 20, harness 15, config/wiring 7
- [ ] **T8** arch tests INV-021a..d
- [ ] **T9** Full suite ≥1450, coverage ≥90%; hồ sơ + LOG/PROGRESS + commit

## Review (tự — đối chiếu code thật)
- H1/H2/H3/H4 patterns đã chứng minh (persist trước raise, registry register) ✓
- Allow-list: benchmark/ cần kernel.services.state + logging + harness intra — ✓ KHÔNG MOD
- External: pydantic/typing/enum/re/datetime/collections — ✓ không thêm
- **Kết luận: APPROVED có điều kiện** — 0 R1; resolve P1/P2/P3 vào implement.
