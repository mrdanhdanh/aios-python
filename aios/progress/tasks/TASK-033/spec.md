# Spec — TASK-033: H4 Benchmark + Regression Gate (M6)

**Trạng thái**: v1 → critique ×2 → implement | **Nguồn**: orchestrator tự soạn (spec-writer không phản hồi — ghi nhận)

## 1. Mục tiêu

"AIOS phiên bản mới có tốt hơn cũ không?" (PLAN §H4/TASK-033): chạy **100 scenarios**, theo dõi đồng thời **Quality / Cost / Latency / Token / Failure Rate / Policy Violations** (không chỉ score). **Regression Gate (INV-021)**: regression nghiêm trọng → khả năng **block release**.

## 2. Phạm vi

- MỚI: `backend/src/aios_core/harness/benchmark/` — contracts.py, errors.py, runner.py, gate.py, benchmark.py, `__init__.py`
- SỬA (additive): `config.py` (+BenchmarkSettings), `config.yaml`, `runtime_kernel.py` (wiring BenchmarkHarness), `tests/test_architecture.py` (arch INV-021), `tests/test_harness_benchmark.py` (mới)
- KHÔNG MOD `_HARNESS_ALLOWED_AIOS`; không sửa Runtime/Orchestrator

## 3. Thiết kế

### 3.1 contracts.py (leaf)
- `BenchmarkMetric(str, Enum)`: QUALITY, COST, LATENCY, TOKEN, FAILURE_RATE, POLICY_VIOLATIONS (6 metrics — PLAN)
- `RunResult(BaseModel, extra=forbid)`: scenario_id: str, quality: float = 0.0, cost: float = 0.0, latency_ms: float = 0.0, tokens: int = 0, failed: bool = False, policy_violations: int = 0
- `Baseline(BaseModel, extra=forbid)`: version: str = "v0", runs: dict[str, RunResult] = {} (key scenario_id)
- `RegressionRule(BaseModel, extra=forbid)`: metric: BenchmarkMetric, max_delta: float (**%** cho QUALITY/COST/LATENCY/TOKEN — delta tương đối; **pp** cho FAILURE_RATE/POLICY_VIOLATIONS — delta tuyệt đối), note: str = ""
- `RegressionFinding(BaseModel, extra=forbid)`: metric: BenchmarkMetric, baseline_avg: float, new_avg: float, delta: float, regressed: bool, rule_note: str = ""
- `BenchmarkReport(BaseModel, extra=forbid)`: baseline_version, scenarios_total, metrics: dict[str, dict] (aggregate avgs + failure_rate + violations), findings: list[RegressionFinding], gate_passed: bool, summary: str, metrics_count: dict (deterministic counts), reproducible: dict = {} (runner identity)

### 3.2 errors.py — `BenchmarkError(Exception)`, `GateBlockedError(Exception)` (INV-021 block release)

### 3.3 runner.py — BenchmarkRunner (deterministic)
- `BenchmarkRunner(run_fn: Callable[[str], RunResult], *, max_scenarios: int = 100)`
  - `run(scenario_ids: list[str]) -> tuple[list[RunResult], dict]` — chạy từng id qua run_fn (cap max_scenarios slice); aggregate: avg quality/cost/latency_ms/tokens, failure_rate = failed/total, policy_violations = sum
  - KHÔNG timing thật (metrics do run_fn cung cấp — deterministic)
- Aggregate dict keys khớp BenchmarkMetric names

### 3.4 gate.py — RegressionGate (INV-021)
- `RegressionGate(rules: list[RegressionRule])` — default rules nếu rỗng:
  - QUALITY max_delta -5% (giảm >5% → regress)
  - FAILURE_RATE max_delta +0.02 pp (tăng >2pp → regress)
  - POLICY_VIOLATIONS max_delta +0.0 pp (tăng bất kỳ → regress)
- `evaluate(new: list[RunResult], baseline: Baseline) -> BenchmarkReport`:
  - per metric: baseline_avg vs new_avg (bỏ scenarios không có trong baseline — deterministic subset chung)
  - delta: % cho QUALITY/COST/LATENCY/TOKEN ((new-baseline)/baseline*100, baseline 0 → delta 0), pp cho FAILURE_RATE/POLICY_VIOLATIONS
  - regressed = delta vượt max_delta (hướng xấu: QUALITY giảm; COST/LATENCY/TOKEN/FAILURE_RATE/VIOLATIONS tăng)
  - gate_passed = không finding regressed
- `can_release(report) -> bool`; raise `GateBlockedError` qua BenchmarkHarness (không raise ở gate — gate thuần)

### 3.5 benchmark.py — BenchmarkHarness (H1 pattern)
- `BenchmarkHarness(runner, gate, *, state_service=None)` — id="benchmark", name="Benchmark", version="1.0.0"
- `run(ctx)`: scenario_ids = ctx.config["scenario_ids"] (list[str]); baseline = ctx.config.get("baseline") (Baseline|None → empty); results = runner.run(ids); report = gate.evaluate(results, baseline); ctx.config["_report"] = report; return report.model_dump()
- `verify(ctx, payload)`: **persist TRƯỚC raise** (key "benchmark"): {baseline_version, gate_passed, findings, summary, scenarios_total, metrics}
  - gate_passed False → raise GateBlockedError (**INV-021 — block release**) (strict flag như H2/H3; strict=False → WARNING)
- `get_report(run_id)` — dict từ state

### 3.6 Wiring + config
- `BenchmarkSettings`: `max_scenarios: int = 100`, `strict: bool = True`, `quality_max_delta: float = -5.0`, `failure_rate_max_delta: float = 0.02`
- config.yaml `benchmark:` block
- runtime_kernel: sau H4 — `BenchmarkHarness(BenchmarkRunner(placeholder_run_fn), RegressionGate(default_rules))` — placeholder_run_fn trả RunResult scenario_id với metrics 0 (deterministic); register "benchmark"

### 3.7 Arch tests INV-021
- **INV-021a**: benchmark/ không import kernel.services.execution|events|resource|scheduler + kernel.graph|orchestrator.planning (runner injectable — duck-typed)
- **INV-021b**: gate.py chứa literal `GateBlockedError` capability: benchmark.py chứa `GateBlockedError(` + `RegressionGate(` (behavioral: gate fail → raise block)
- **INV-021c**: benchmark/ không import sqlite3/httpx/socket/requests/os (no side effect — AST, pattern INV-020b)
- **INV-021d**: `_HARNESS_ALLOWED_EXTERNAL` không cần thêm (pydantic/typing/enum/re/datetime/collections có sẵn)

## 4. AC
| AC | Mô tả | Kiểm chứng |
|----|-------|-----------|
| AC1 | Contracts: BenchmarkMetric 6, RunResult, Baseline, RegressionRule/Finding, BenchmarkReport — extra=forbid | unit |
| AC2 | BenchmarkRunner: run qua run_fn, cap max_scenarios, aggregate đủ 6 metrics | unit |
| AC3 | RegressionGate: default rules; % vs pp delta; hướng xấu đúng chiều | unit |
| AC4 | Gate: subset chung (scenario không trong baseline bỏ); baseline rỗng → không regress | unit |
| AC5 | can_release đúng; report findings đủ metric | unit |
| AC6 | BenchmarkHarness qua H1: run+verify pass; gate fail → GateBlockedError; persist trước raise; get_report | unit + integration |
| AC7 | strict=False → WARNING không raise | unit |
| AC8 | Baseline version + reproducible trong report | unit |
| AC9 | 100 scenarios cap; deterministic repeat (cùng input → cùng report) | unit |
| AC10 | Config + wiring register "benchmark" | unit |
| AC11 | Arch INV-021a..d; **tổng ≥1450 tests (baseline 1387 + ≥60), coverage ≥90%** | full suite |

## 5. Không làm
- KHÔNG chạy workflow thật (run_fn injectable); KHÔNG lưu benchmark history DB (baseline truyền qua config); KHÔNG CLI `aiagent harness benchmark` (API sau — TASK-034/đầu ra M6)
