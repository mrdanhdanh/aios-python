# TASK-089 — M13-P0: Behavioral Conformance (P0) — SPEC v3

> Milestone: M13 Harness Trust & Behavioral Conformance (Issue #9, nhánh `feature/ISSUE-9-m13-harness-trust`)
> Nâng cấp: P0 — Behavioral Conformance — scenario chạy N lần (configurable: quick=100/standard=1k/stress=10k/soak=duration) + repeat + fault-inject + so sánh evidence + regression gate
> Dependency: P0 → P1 (TASK-090) → P2 (TASK-091) → (P3 TASK-092 ∥ P4 TASK-093)
> Trạng thái: `in-progress` (hard gate) — v3 tích hợp resolution critique-1 (6 P1 + 8 P2 + 9 P3) + critique-2 (2 P1 + 5 P2 + 10 P3)

## 1. Mục tiêu

Chứng minh Harness **hành vi ổn định qua thời gian (temporal determinism), dưới tải (load), chạy dài (soak) và phục hồi lỗi (failure recovery)** — bậc thang Behavioral Conformance (PLAN §M13-5):

```
Structural        "Có cơ chế này không?"        (đã có — M6/M10 conformance)
    + Behavioral     "Hành vi đúng dưới kịch bản?"   ← TASK-089
    + Temporal       "Deterministic qua thời gian?"   ← TASK-089 (N lần + repeat)
    + Load           "Ổn định dưới tải?"              ← TASK-089 (stress=10k)
    + Soak           "Không leak/trễ sau chạy dài?"   ← TASK-089 (soak=duration)
    + Failure Recovery "Tự phục hồi đúng cách?"       ← TASK-089 (fault-inject)
```

**Không** tạo hệ thống song song: tái dùng `SimulationRunner` (deterministic, không side-effect), `FaultInjector`, `RegressionGate`, `HarnessRunner` lifecycle, fail-closed (INV-035).

## 2. Phạm vi

**In:**
- Module mới `backend/src/aios_core/harness/behavioral/` (contracts + engine + harness) — **KHÔNG đặt tên `conformance/`** (tránh trùng `harness/certification/conformance.py` — P2-8)
- Mở rộng tối thiểu, backward-compatible: `Fault.recoverable: bool = True` + `FaultInjector.next_for` (P1-2)
- Wiring: đăng ký harness `id="behavioral"` vào `HarnessRegistry` (runtime_kernel.py)
- CLI: `aiagent harness behavioral` (subcommand group `harness` MỚI — pattern mới trong `workflow/cli.py`)
- Tests: `backend/tests/test_harness_behavioral.py`

**Out:**
- P1 Harness Coverage (TASK-090), P2 Meta-Harness (TASK-091), P3 Trust Separation (TASK-092), P4 Docs/ADR (TASK-093)
- KHÔNG sửa Runtime/Orchestrator (INV-017..021 giữ nguyên)
- KHÔNG sửa `SimulationRunner`/`RegressionGate` hiện có (chỉ tái dùng)
- KHÔNG thêm invariant mới (INV-001..035 frozen)
- KHÔNG thêm `ConformanceSettings` vào config.py (P2-4 — config qua CLI)
- `FaultInjector` chỉ mở rộng tối thiểu (P1-2: `Fault.recoverable` + `next_for`) — P3-1

## 3. Thiết kế

### 3.1 Contracts (`harness/behavioral/contracts.py`)

```python
class ConformanceProfile(str, Enum):
    QUICK = "quick"        # 100 iterations
    STANDARD = "standard"  # 1000 iterations
    STRESS = "stress"      # 10000 iterations
    SOAK = "soak"          # duration-based (giây)

class ConformanceStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"          # MISMATCH / deterministic / repeat / gate fail
    ERROR = "error"        # iteration ERROR (fault không recover / exception)

class ConformanceConfig(BaseModel):  # extra="forbid"
    profile: ConformanceProfile = ConformanceProfile.QUICK
    scenario: Scenario                # bắt buộc — full Scenario (P1-5)
    iterations: int | None = None     # override profile; thắng soak (P3-3)
    duration_s: float = 0.0           # soak: chạy tối đa duration giây (0 → 1 iteration)
    faults: list[Fault] = []          # áp cho mọi iteration (injector mới mỗi lần)
    fault_iterations: list[int] = []  # chỉ inject fault ở iteration này (1-based)
    repeat_samples: int = 3           # số iteration đầu chạy repeat (double-run) (P1-4)
    baseline: Baseline | None = None  # regression gate baseline (chỉ expose — P1-3)
    strict: bool = True               # verify: status != PASS → raise (P3-5)

    # field_validator (P2-5):
    # - fault_iterations: dedup + index >= 1; nếu non-empty → faults phải non-empty
    # - iterations: >= 1 nếu cung cấp

class ConformanceIterationSummary(BaseModel):  # extra="forbid" — KHÔNG giữ full outcome (P2-6)
    index: int                       # 1-based
    status: SimulationStatus
    evidence_digest: str             # sha256(outcome.model_dump_json())
    repeat_ok: bool | None = None    # double-run khớp; None = không repeat (P1-2 v2)
    fault_injected: bool
    recovered: bool = False          # không fault → không recover (P3-6 v2)

class ConformanceReport(BaseModel):  # extra="forbid"
    profile: ConformanceProfile
    scenario_id: str
    iterations_total: int
    status: ConformanceStatus
    deterministic: bool              # digest nhóm không-fault giống nhau (P3-6 v1)
    repeat_consistent: bool          # mọi iteration ĐƯỢC repeat đều repeat_ok=True (P1-2 v2)
    fault_recovery_rate: float       # recovered / faults_injected (0 nếu không fault) (P3-9 v1)
    iterations: list[ConformanceIterationSummary] = []  # summary per-iteration (P3-7 v1)
    metrics: dict                    # counts only: iterations_total, faults_injected_total,
                                     # recovery_events_total, repeat_runs, mismatch_count, error_count (P3-7 v2)
    findings: list[str] = []
    gate: BenchmarkReport | None = None   # chỉ expose — KHÔNG quyết định status (P1-3 v1)
    summary: str
    reproducible: dict               # profile, scenario_id, iterations, faults, fault_iterations, baseline version (P3-2 v1)
```

### 3.2 Engine (`harness/behavioral/engine.py`)

```python
PROFILE_ITERATIONS = {QUICK: 100, STANDARD: 1000, STRESS: 10000}

class BehavioralConformanceEngine:
    def __init__(self, runner: SimulationRunner | None = None, *,
                 soak_max_iterations: int = 10000) -> None  # cap từ constructor (P2-3)
    def run(self, config: ConformanceConfig) -> ConformanceReport
```

**Luồng `run()`:**
1. **Resolve iterations**: `config.iterations` override > `PROFILE_ITERATIONS[profile]`; soak → duration-based: chạy tối thiểu 1, tối đa `soak_max_iterations`, dừng khi `time.monotonic() >= deadline` (deadline = start + duration_s; duration_s=0 → 1 iteration). (P3-3 v1: iterations override thắng soak). **Cap `repeat_samples = min(repeat_samples, iterations)`** (P1-2 v2).
2. **Vòng lặp N lần** — mỗi iteration:
   - Build scenario copy: faults theo schedule — `fault_iterations` non-empty → chỉ iteration trong list có fault; ngược lại mọi iteration có fault (injector mới mỗi lần). **Fail-fast**: fault_iterations có index > iterations_total → raise `BehavioralConformanceError` (P2-3 v2).
   - `outcome = runner.run(scenario)` (SimulationRunner — deterministic)
   - `evidence_digest = sha256(outcome.model_dump_json())`
   - **Repeat** (P1-4 v1): chỉ iteration ≤ `repeat_samples` — chạy lại 1 lần nữa cùng scenario → `repeat_ok = replay_outcome.model_dump() == outcome.model_dump()`. Ghi rõ: repeat ≠ `replay_verdict` (tamper detection thuộc TASK-091).
   - Ghi `ConformanceIterationSummary` (KHÔNG giữ full outcome — P2-6 v1)
3. **Phân tích**:
   - `deterministic` (P3-6 v1): digest nhóm iteration không-fault giống nhau. Ghi chú: nếu mọi iteration đều có fault (không có nhóm không-fault) → deterministic=True vacuous (P3-4 v2).
   - `repeat_consistent` (P1-2 v2): mọi iteration **được repeat** (≤ repeat_samples) đều repeat_ok=True
   - `fault_recovery_rate` (P3-9 v1): tổng recovered / tổng fault_injected (chỉ iteration có fault); 0 nếu không fault
   - **Hành vi ĐÚNG (P1-1 v1)**: mọi outcome không-fault phải `status == SUCCESS`; bất kỳ MISMATCH → `FAIL` + finding
   - `status`: có iteration ERROR → ERROR; MISMATCH/deterministic/repeat fail → FAIL; ngược lại PASS
4. **Regression gate (P1-3 v1 + P1-1 v2)**: nếu `config.baseline` → **aggregation N iteration → 1 RunResult/scenario**: `quality` = tỷ lệ iteration SUCCESS, `failed` = có bất kỳ iteration fail, `policy_violations` = số iteration có policy bypass (`0 if outcome.verification.get("no_policy_bypass") else 1`), cost/tokens/latency = 0 → `RegressionGate().evaluate([run_result], baseline)`. Gate **chỉ expose** trong report (finding nếu block) — **KHÔNG quyết định status** (gate-as-blocker thuộc M14 — P2-5 v2). Aggregation dùng chung cho `--save-baseline`.
5. **Report**: summary + reproducible (P3-2 v1) + metrics (counts — P3-7 v2).

### 3.3 Harness (`harness/behavioral/harness.py`)

```python
class BehavioralConformanceHarness(Harness):  # id="behavioral", version="1.0.0"
    def __init__(self, engine: BehavioralConformanceEngine | None = None, *,
                 state_service: StateService | None = None) -> None  # P2-2 v2
    def run(self, ctx: HarnessContext) -> Any
        # ctx.config["config"]: ConformanceConfig (hoặc dict) bắt buộc
        # → engine.run(config) → report.model_dump(mode="json")
    def verify(self, ctx, payload) -> None
        # strict → status != PASS → raise BehavioralConformanceError (fail-closed INV-035)
    def _persist(self, ctx, report, strict) -> None   # pattern TestHarness (P2-2 v2)
    def get_report(self, run_id) -> dict | None       # query lại report (P2-2 v2)
```

`harness/behavioral/errors.py`: `BehavioralConformanceError(HarnessError)` (P3-5 v2).

### 3.4 Wiring (`kernel/runtime_kernel.py`)

Đăng ký `BehavioralConformanceHarness` vào `HarnessRegistry` (id="behavioral") — theo pattern benchmark/doctor hiện có. Engine tạo `SimulationRunner` riêng (default FakeRuntime) — độc lập TestHarness (P3-8 v1). Truyền `container.resolve(StateService)` cho harness (P2-2 v2).

### 3.5 CLI (`workflow/cli.py`) — subcommand group `harness` MỚI (P1-6)

```
aiagent harness behavioral --profile quick|standard|stress|soak
    --scenario-file <yaml|json>    # bắt buộc — scenarios.load() (P1-5)
    --iterations N                 # override profile (thắng soak)
    --duration S                   # soak duration (giây)
    --faults <json>                # list[Fault] — áp mọi iteration (json.loads + try/except → parser.error)
    --fault-iterations <json>      # list[int] — chỉ iteration có fault
    --repeat-samples N             # default 3
    --baseline <file>              # JSON Baseline (chỉ expose)
    --save-baseline <file>         # ghi Baseline từ lần chạy này
    --no-strict                    # set config.strict=False
```

Parser: `sub.add_parser("harness")` + `harness_sub.add_parser("behavioral")`; dispatch `if args.command == "harness" and args.harness_command == "behavioral"` → `_harness_behavioral()` (lazy import). Output: JSON 1 dòng (report) + exit 0 (PASS) / 1 (FAIL/ERROR) — precedent `compat`/`conformance`. `--faults`/`--fault-iterations`: `json.loads` + try/except → `parser.error`; `--faults` phải là list (isinstance check — P3-9 v2). Ghi chú: stress=10k → report JSON ~10k summary entries (vài MB) — chấp nhận được (P3-8 v2).

## 4. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm chứng |
|---|----|-----------------|
| AC1 | Profile resolution đúng: quick=100, standard=1000, stress=10000; `iterations` override hoạt động | Unit test: engine chạy đủ số iteration |
| AC2 | Soak: duration-based — chạy ≥1 iteration, dừng khi hết duration, cap `soak_max_iterations` | Unit test: duration_s nhỏ → iterations ≥1 và ≤ cap |
| AC3 | Deterministic: N lần chạy không fault → digest giống nhau (deterministic=True) | Unit test: 10 iterations → deterministic=True |
| AC4 | Evidence compare: digest sha256 mỗi iteration; digest nhóm không-fault giống nhau | Unit test: digest giống nhau |
| AC5 | Repeat: double-run khớp (repeat_ok=True) cho iteration ≤ repeat_samples; repeat_consistent=True (chỉ xét iteration được repeat) | Unit test: repeat_consistent=True; iteration > repeat_samples có repeat_ok=None (P1-2 v2) |
| AC6 | Fault-inject: faults áp mọi iteration (injector mới mỗi lần) → recovery rate=1.0; `fault_iterations=[k]` → chỉ iteration k có fault, các iteration khác deterministic | Unit test: recovery_rate=1.0; fault_iterations test riêng (P2-7 v1) |
| AC7 | Regression gate: baseline → aggregation N iteration → 1 RunResult → RegressionGate.evaluate; gate expose trong report (finding nếu block) — KHÔNG quyết định status | Unit test: baseline nhân tạo → gate tính đúng (quality = tỷ lệ SUCCESS); status không đổi (P1-1 v2) |
| AC8 | Report: status/summary/reproducible đúng; metrics chỉ counts; iterations summary đủ | Unit test: field assertions |
| AC9 | Harness id="behavioral" đăng ký registry + chạy qua HarnessRunner lifecycle (evidence + report) + report persist (get_report) | Test wiring: RuntimeKernel.create() → registry có behavioral; HarnessRunner.execute → report + evidence; get_report trả report (P2-2 v2) |
| AC10 | CLI `aiagent harness behavioral` chạy được: PASS → exit 0; FAIL/ERROR → exit 1; JSON 1 dòng | Test CLI thật |
| AC11 | Fail-closed (INV-035): iteration ERROR (fault `recoverable=False` không recover) → status ERROR — KHÔNG PASS | Unit test: Fault(recoverable=False) → ERROR (P1-2 v1) |
| AC12 | Full suite không regression + arch-health 0 violations + doctor healthy | Chạy full pytest + arch-health + doctor |
| AC13 | Hành vi ĐÚNG (P1-1 v1): scenario expectation sai → MISMATCH → status FAIL (dù deterministic). **Chỉ dùng mismatch loại intent/agent/policy/required_capabilities** (runner kiểm tra được); negative test (expect.tests_pass=False) chưa được runner hỗ trợ — ngoài scope (P2-4 v2) | Unit test: expect.intent sai → FAIL + finding |
| AC14 | Resolve scenario từ file (P1-5 v1): `scenarios.load()` yaml/json → engine chạy được | Unit test: load yaml → run |
| AC15 | Temporal determinism cross-run (P2-1 v1): chạy engine 2 lần cùng config → report giống hệt (trừ duration/run_id) | Unit test: 2 report bằng nhau |
| AC16 | `--save-baseline` ghi Baseline JSON đúng format (aggregation N iteration → 1 RunResult) (P3-4 v1 + P1-1 v2) | Test CLI: file tồn tại + Baseline parse được |
| AC17 | Verify fail-closed (P2-1 v2): (a) strict=True + report FAIL/ERROR → BehavioralConformanceError raise → HarnessRunStatus.FAILED; (b) strict=False → không raise, run COMPLETED | Test harness: execute với report FAIL → FAILED; --no-strict → COMPLETED |

## 5. Rủi ro & giả định

- **R1**: `SimulationRunner` deterministic — đã có test `test_deterministic_repeat`. Giả định giữ nguyên.
- **R2**: stress=10000 iterations — mỗi iteration thuần (không I/O) nên nhanh; test dùng override nhỏ để không chậm suite.
- **R3**: soak dùng `time.monotonic()` — không phụ thuộc wall clock; test dùng duration_s rất nhỏ. **Soak v1 = loop-stability test** (runner thuần không resource/timing — leak/latency thật thuộc M13.1) (P2-3 v1).
- **R4**: `fault_iterations` 1-based (khớp `ConformanceIterationSummary.index`).
- **R5**: KHÔNG import sqlite3/httpx/socket/requests/os trong module behavioral (INV-020b precedent — simulation thuần).
- **R6**: `Fault.recoverable` mặc định True — backward-compatible, không phá test cũ.
- **R7**: **Deviation PLAN §M13 P0** (P2-5 v2): gate v1 chỉ expose (tính + finding), gate-as-blocker thuộc M14 (Certified Baseline) — cập nhật PLAN.md khi implement.
- **R8**: deterministic vacuous khi mọi iteration đều có fault (không có nhóm không-fault) — ghi chú trong report (P3-4 v2).

## 6. Test strategy

`Unit → Contract → Integration → Architecture → E2E → Regression`:
- Unit: engine (profile/soak/deterministic/evidence/repeat/fault/gate), contracts (pydantic defaults + extra="forbid" + validators)
- Contract: report fields, status enum
- Integration: HarnessRunner.execute full lifecycle + registry wiring
- Architecture: arch-health 0 violations (allow-list nếu cần)
- E2E: CLI thật
- Regression: full suite không giảm