# TASK-033 — M6-H4 Benchmark + Regression Gate — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the
> `harness/benchmark/` subpackage (single source of truth), not duplicated here.
> Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/harness/benchmark/contracts.py` — BenchmarkMetric 6 + RunResult/Baseline/RegressionRule/Finding/BenchmarkReport (extra=forbid)
- `backend/src/aios_core/harness/benchmark/errors.py` — `BenchmarkError` + `GateBlockedError(BenchmarkError)`
- `backend/src/aios_core/harness/benchmark/runner.py` — `BenchmarkRunner` run_fn injectable + cap max_scenarios + aggregate 6 metrics
- `backend/src/aios_core/harness/benchmark/gate.py` — `RegressionGate` 3 default rules (quality/failure_rate/violations) + % vs pp delta + subset chung sort + baseline==0 delta 0 + baseline rỗng không block + epsilon boundary + can_release
- `backend/src/aios_core/harness/benchmark/benchmark.py` — `BenchmarkHarness` id=benchmark persist TRƯỚC raise GateBlockedError (INV-021) + strict + get_report
- `backend/src/aios_core/config.py` — `BenchmarkSettings`
- `backend/src/aios_core/kernel/runtime_kernel.py` — placeholder run_fn deterministic + register "benchmark"

## Key behavior
- Benchmark: "AIOS phiên bản mới có tốt hơn cũ không?" — Quality/Cost/Latency/Token/Failure Rate/Policy Violations (không chỉ score)
- Regression Gate (INV-021): quality giảm → FAIL block release; quality +2% nhưng cost +80% → FAIL tùy policy
- strict=False → WARNING không raise; baseline rỗng → không regress

## Verification
- `pytest` full suite: **1450 passed, coverage 95.31%, 11/11 AC** (xem `test.md`)
