# Evaluation — TASK-033 (Benchmark + Regression Gate, M6-H4)

## Tiêu chí chấp nhận (AC)
| AC | Yêu cầu | Kết quả |
|----|---------|---------|
| AC1 | Contracts: BenchmarkMetric 6, RunResult, Baseline, RegressionRule/Finding, BenchmarkReport | ✅ extra=forbid |
| AC2 | BenchmarkRunner: run_fn injectable, cap 100, aggregate 6 metrics | ✅ |
| AC3 | RegressionGate: default rules (3), % vs pp delta, hướng xấu | ✅ quality/failure_rate/violations |
| AC4 | Subset chung; baseline rỗng → không regress | ✅ P1-01 |
| AC5 | can_release; findings đủ metric | ✅ |
| AC6 | BenchmarkHarness qua H1: gate fail → GateBlockedError; persist trước raise | ✅ INV-021d |
| AC7 | strict=False → WARNING | ✅ |
| AC8 | Baseline version + reproducible | ✅ |
| AC9 | 100 cap; deterministic repeat | ✅ |
| AC10 | Config + wiring register "benchmark" | ✅ |
| AC11 | Arch INV-021a..d; ≥1450 tests; coverage ≥90% | ✅ 1450 tests, 95.31% |

## Critique resolution
- C1-01..03 (delta 0 khi baseline 0; subset sort; bảng hướng) ✓
- C2-01..04 (signature; failure_rate subset; violations per-scenario avg; metrics counts) ✓
- P1-01..02 (baseline rỗng không block; persist trước raise) ✓
- P2-01..03 (3 default rules từ settings; GateBlockedError(BenchmarkError); can_release) ✓

## Metrics
- Tests: 1387 → **1450** (+63); coverage 95.27 → 95.31%
- Module mới: `harness/benchmark/` 6 file (~600 LOC)
- 5 harnesses đăng ký: verification, test, evaluation, benchmark
- Fix: float epsilon boundary; latency_ms timing trong test deterministic cũ (flaky)

## Bài học
1. Float boundary cần epsilon — delta -4.999999999 vs -5.0 ngưỡng
2. Metric "theo dõi" (cost/latency/token) vs metric "gate" (quality/failure_rate/violations) — PLAN yêu cầu theo dõi 6, block theo 3
3. Arch literal phải khớp thực tế implement (type hint thay vì constructor call)

## Kết luận
**TASK-033 HOÀN TẤT** — 11/11 AC, hard gate đầy đủ (spec v2 → critique ×2 → review → implement → test → evaluate).
