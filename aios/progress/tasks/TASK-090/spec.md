# TASK-090 — M13-P1: Harness Coverage model (P1) — SPEC v3

> Milestone: M13 Harness Trust & Behavioral Conformance (Issue #9, nhánh `feature/ISSUE-9-m13-harness-trust`)
> Nâng cấp: P1 — Harness Coverage model 9 chiều + Negative-path (8) + Doctor Readiness scoring
> Dependency: P0 (TASK-089 ✅) → P1 → P2 (TASK-091) → (P3 TASK-092 ∥ P4 TASK-093)
> Trạng thái: `in-progress` (hard gate) — v3 tích hợp resolution critique-1 (3 P1/6 P2/3 P3) + critique-2 (2 P1/8 P2/10 P3)

## 1. Mục tiêu

Coverage là **model đa chiều** (PLAN §M13-5b) — KHÔNG quy "test count = coverage". 9 chiều + 8 negative-path → feed **Harness Readiness scoring** (7 dimensions + Overall + Status).

**Quyết định fail-closed (P1-1 v1)**: v1 coverage báo cáo NOT_READY (replay gate 0.5 < 0.75) cho tới khi TASK-091 cover đủ negative-path + replay. Trust layer KHÔNG tự chứng nhận READY khi còn negative-path chưa chứng minh.

## 2. Phạm vi

**In:**
- Module mới `backend/src/aios_core/harness/coverage/` (contracts + coverage builder + readiness scorer + harness + errors)
- Wiring: đăng ký harness `id="coverage"` vào `HarnessRegistry`
- CLI: `aiagent harness coverage` (mở rộng group `harness` — pattern TASK-089)
- Tests: `backend/tests/test_harness_coverage.py`

**Out:**
- P2 Meta-Harness (TASK-091), P3 Trust Separation (TASK-092), P4 Docs/ADR (TASK-093)
- KHÔNG sửa Runtime/Orchestrator (INV-017..021 giữ nguyên)
- KHÔNG quét test files bằng AST/coverage tools (test count ≠ coverage)
- KHÔNG thêm invariant mới (INV-001..035 frozen)

## 3. Thiết kế

### 3.1 Contracts (`harness/coverage/contracts.py`)

```python
class CoverageDimension(str, Enum):
    COMPONENT = "component"; CONTRACT = "contract"; STATE = "state"
    TRANSITION = "transition"; EVENT = "event"; FAILURE_MODE = "failure_mode"
    SCENARIO = "scenario"; VERIFICATION_PATH = "verification_path"
    ARTIFACT = "artifact"                    # 9 chiều

class NegativePath(str, Enum):
    PASS = "pass"; FAIL = "fail"; BLOCKED = "blocked"; VIOLATION = "violation"
    TIMEOUT = "timeout"; EXCEPTION = "exception"
    CORRUPTED_EVIDENCE = "corrupted_evidence"
    REPLAY_MISMATCH = "replay_mismatch"      # 8 paths

class CoverageItem(BaseModel):  # extra="forbid"
    dimension: CoverageDimension
    id: str
    covered: bool
    evidence: str                # module:... (find_spec) hoặc path:... (anchored backend root)

class DimensionCoverage(BaseModel):  # extra="forbid"
    dimension: CoverageDimension
    total: int
    covered: int
    ratio: float                 # covered/total (0 nếu total=0)

class NegativePathCoverage(BaseModel):  # extra="forbid"
    path: NegativePath
    covered: bool
    evidence: str                # covered=True → evidence non-empty + tồn tại; covered=False → "" (AC18)

class HarnessCoverageReport(BaseModel):  # extra="forbid" — KHÔNG có status (P3-2 v1)
    dimensions: dict[str, DimensionCoverage]
    negative_paths: dict[str, NegativePathCoverage]
    overall_ratio: float
    negative_path_ratio: float
    metrics: dict                # counts only
    summary: str
    reproducible: dict           # {aios_version, registry_harness_ids (sorted), python_version} (P3-F v2)
```

### 3.2 Coverage builder (`harness/coverage/coverage.py`)

```python
class HarnessCoverage:
    def __init__(self, registry: HarnessRegistry) -> None
    def build(self) -> HarnessCoverageReport
```

**Evidence quy ước (P1-A v2)**: module evidence ưu tiên (`module:aios_core.harness.X` — `importlib.util.find_spec`); path evidence **anchor backend root** = `Path(aios_core.__file__).resolve().parents[2] / "tests" / ...` — cwd-independent. KHÔNG dùng os (INV-020b).

**Auto-collect (từ code thật):**
- **Component** (7): `HarnessRegistry.list()` **exclude id="coverage"** (P1-3 v1) — verification/test/evaluation/benchmark/doctor/readiness/behavioral; covered=True; evidence `module:aios_core.harness.<sub>` (mỗi harness có test thật)
- **Contract** (21 — P2-2 v1): Check, CheckResult, VerificationTask, Verdict (execution) · Scenario, ExpectedResult, Fault, SimulationOutcome (testing) · GoldenScenario (certification) · ConformanceConfig, ConformanceReport (behavioral) · DoctorResult, ReadinessReport (doctor) · Baseline, RunResult, BenchmarkReport (benchmark) · HarnessRun, HarnessResult, HarnessReport, HarnessArtifact, HarnessEvent (harness) — covered=True; evidence module tương ứng
- **State** (14 — P2-6 v1): HarnessRunStatus (8) + ConformanceStatus (3) + SimulationStatus (3); covered=True
- **Transition** (12 — P3-A v2): `HarnessLifecycle.TRANSITIONS` edges (matrix test 8×8 có thật); covered=True; evidence `module:aios_core.harness.lifecycle`
- **Event** (6 — P2-A v2): phase thật runner emit (`status.value`): preparing/validating/running/verifying/completed/failed; covered=True; evidence `module:aios_core.harness.runner`
- **Failure-mode** (8 — P3-B v2): FaultType (3) + errors (5: HarnessError, HarnessRegistrationError, HarnessNotFoundError, HarnessLifecycleError, HarnessHookError); covered=True; evidence `module:aios_core.harness.testing` + `module:aios_core.harness`
- **Scenario** (20): `GOLDEN_SCENARIOS` (GS-001..GS-020 — conformance chạy thật); covered=True; evidence `module:aios_core.harness.certification`
- **Verification-path** (12 — P3-C v2): Verdict (4) + VerificationState INV-035 (8: pass/fail/error/blocked/unknown/not_executed/missing_evidence/skipped); covered=True; evidence `module:aios_core.harness.execution` + `module:aios_core.verification`. Ghi chú: VerificationVerdict (5) thuộc verification/ layer — KHÔNG tính (loại trừ có lý do)
- **Artifact** (2 — P2-B v2): events/report (runner `_build_evidence` tạo 2 kind thật); covered=True; evidence `module:aios_core.harness.runner`

**Negative-path (v1 — declared, evidence kiểm chứng tồn tại P2-5 v1):**
| Path | covered | Evidence |
|------|---------|----------|
| PASS | True | module:aios_core.harness.testing |
| FAIL | True | module:aios_core.harness.execution |
| BLOCKED | True | module:aios_core.harness.benchmark |
| VIOLATION | True | path:backend/tests/test_architecture.py (anchored — P1-A v2) |
| TIMEOUT | True | module:aios_core.harness.testing |
| EXCEPTION | True | module:aios_core.harness |
| CORRUPTED_EVIDENCE | **False** | "" — cần TASK-091 |
| REPLAY_MISMATCH | **False** | "" — cần TASK-091 |

→ negative_path_ratio v1 = 6/8 = 0.75; kế hoạch tăng ngưỡng lên 1.0 sau TASK-091 (P3-3 v1).

### 3.3 Harness Readiness scorer (`harness/coverage/readiness.py`)

```python
class HarnessReadinessStatus(str, Enum):
    READY = "ready"; NOT_READY = "not_ready"

class HarnessReadinessReport(BaseModel):  # extra="forbid"
    dimensions: dict[str, float]   # 7 dims
    overall: float
    status: HarnessReadinessStatus
    hard_gates: list[HardGate]     # tái dùng doctor/contracts HardGate (P3-G v2)
    summary: str
    metrics: dict
    reproducible: dict

class HarnessReadinessScorer:
    # KHÔNG nhận doctor (P2-3 v1 — reserved M13.1/M16)
    def score(self, coverage: HarnessCoverageReport,
              *, min_overall: float = 0.8,
              min_replay: float = 0.75,
              production_tests_available: bool = False) -> HarnessReadinessReport
    # param ngoài (0,1] → ValueError (AC19 — P2-H v2)
```

**7 dimensions** (deterministic):
| Dimension | Công thức |
|-----------|-----------|
| Structural | mean(component.ratio, contract.ratio) |
| Contract | contract.ratio |
| Behavioral | mean(scenario.ratio, verification_path.ratio) |
| Failure | mean(4 — P3-D v2): failure_mode.ratio, FAIL covered→1.0, EXCEPTION→1.0, TIMEOUT→1.0 |
| Replay | mean(verification_path.ratio, REPLAY_MISMATCH covered→1.0 else 0.0) — coupling có lý do: replay = recompute verdict từ evidence (P3-E v2) |
| Scenario | mean(scenario.ratio, negative_path_ratio) |
| Production | **0.0 bất kể available trong v1** (P2-C v2 — chưa có nguồn evidence; M13.1/M16 sẽ định nghĩa) |

**Hard gates (P1-1 v1 + P1-2 v1 + P2-C v2)**:
- `replay >= min_replay` (0.75): v1 Replay = mean(1.0, 0.0) = **0.5 → NOT_READY** (fail-closed thật)
- `production >= 0.5` — chỉ enforce khi `production_tests_available=True` (future-proofing; v1 luôn NOT_READY nếu bật — CLI help ghi rõ P3-I v2)
- `overall >= min_overall` — overall = mean 6 dims active (production excluded): v1 = (1+1+1+1+0.5+0.875)/6 = **0.896** → pass, nhưng replay gate fail → **NOT_READY**

### 3.4 Harness (`harness/coverage/harness.py`) + errors

```python
# errors.py
class CoverageError(HarnessError): ...

class CoverageHarness(Harness):  # id="coverage", version="1.0.0"
    def __init__(self, registry: HarnessRegistry,
                 scorer: HarnessReadinessScorer | None = None, *,
                 state_service: StateService | None = None) -> None
    def run(self, ctx) -> Any
        # config: min_overall/min_replay/production_tests_available
        # → coverage.build() → scorer.score() → {"coverage": ..., "readiness": ...}
    def verify(self, ctx, payload) -> None
        # strict → status != READY → raise CoverageError (fail-closed INV-035)
    def _persist(self, ctx, payload, strict) -> None  # P2-D v2: update_state(run_id, coverage_report=...)
    def get_report(self, run_id) -> dict | None
```

**Docstring (P3-1 v1)**: "coverage" = Harness Coverage model (độ phủ kiểm chứng) — KHÁC test coverage / ArtifactType.COVERAGE / CheckKind.COVERAGE.

### 3.5 Wiring + CLI

- Wiring: `CoverageHarness(HarnessRegistry (shared), scorer, state_service)` — id="coverage" (đăng ký sau cùng; builder exclude self — không circular, P1-3 v1)
- CLI: `aiagent harness coverage [--min-overall 0.8] [--min-replay 0.75] [--production-tests] [--no-strict]` → **1 JSON document** (indent=2 precedent TASK-089 — P3-H v2) + exit 0 (READY) / 1 (NOT_READY). Help `--production-tests`: "v1 luôn NOT_READY (chưa có nguồn evidence — M13.1/M16)" (P3-I v2)

## 4. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm chứng |
|---|----|-----------------|
| AC1 | CoverageDimension đủ 9 chiều | Unit test |
| AC2 | NegativePath đủ 8 paths | Unit test |
| AC3 | Component: 7 harness (exclude coverage) — **register coverage → build → vẫn 7** (P2-G v2) | Unit test |
| AC4 | Contract 21 + State 14 + Transition 12 + Event 6 + Failure-mode 8 + Scenario 20 + Verification-path 12 + Artifact 2 — total per dimension > 0 | Unit test |
| AC5 | Coverage report: ratio per dimension + overall_ratio; KHÔNG có status field | Unit test |
| AC6 | Negative-path 6/8 covered, evidence non-empty + tồn tại (find_spec/anchored Path.exists); CORRUPTED_EVIDENCE + REPLAY_MISMATCH = False + evidence="" (P2-F v2) | Unit test |
| AC7 | Readiness: 7 dims + overall (6 active) + hard gates; production=0.0 | Unit test |
| AC8 | Fail-closed: default → Replay=0.5 < 0.75 → NOT_READY (dù overall 0.896 ≥ 0.8); READY khi replay ≥ 0.75 + gates OK | Unit test |
| AC9 | Harness id="coverage" registry + lifecycle + persist round-trip (get_report) | Test wiring + harness |
| AC10 | CLI `aiagent harness coverage`: exit 1 (NOT_READY v1) + JSON document đủ coverage+readiness | Test CLI thật |
| AC11 | Fail-closed (INV-035): strict + NOT_READY → CoverageError → HarnessRunStatus.**DIAGNOSED** (default) / FAILED (diagnose_on_failure=False) (P1-B v2) | Test harness cả 2 nhánh |
| AC12 | Full suite không regression + arch-health 0 + doctor healthy | Chạy full pytest + arch-health + doctor |
| AC13 | Determinism: build 2 lần → report giống hệt (cwd-independent — P1-A v2) | Unit test |
| AC14 | metrics counts + summary non-empty | Unit test |
| AC15 | Registry rỗng → ratio 0 không div0 | Unit test |
| AC16 | CoverageError subclass HarnessError + report đủ 9 dimensions + 8 negative keys | Unit test |
| AC17 | Production gate conditional: available=True → production 0.0 < 0.5 → NOT_READY (P2-C v2) | Unit test |
| AC18 | covered=False → evidence == "" (P2-F v2) | Unit test |
| AC19 | min_overall/min_replay ngoài (0,1] → ValueError (P2-H v2) | Unit test |

## 5. Rủi ro & giả định

- **R1**: Coverage v1 = declared + auto-collect từ registry/code contracts — không quét test files (PLAN §M13-5b).
- **R2**: Negative CORRUPTED_EVIDENCE/REPLAY_MISMATCH = False v1 → TASK-091 cover; kế hoạch tăng min_negative_ratio 1.0 sau TASK-091. CLI v1 exit 1 mặc định (NOT_READY — fail-closed thật).
- **R3**: Production = 0.0 + excluded overall v1 (chưa có nguồn evidence) — M13.1/M16 sẽ định nghĩa.
- **R4**: KHÔNG import sqlite3/httpx/socket/requests/os (INV-020b) — evidence check dùng importlib.util + pathlib (anchored backend root).
- **R5**: KHÔNG sửa Runtime/Orchestrator; KHÔNG thêm invariant; 4 invariant track giữ nguyên.
- **R6**: CLI v1 trả exit 1 mặc định — chấp nhận (precedent TASK-089 `--no-strict` "exit vẫn 1"); CI dùng `--no-strict` nếu cần observe.

## 6. Test strategy

`Unit → Contract → Integration → Architecture → E2E → Regression`:
- Unit: coverage builder (từng chiều + negative-path + evidence check anchored), readiness scorer (7 dims + gates + param validation)
- Contract: pydantic defaults + extra="forbid"
- Integration: HarnessRunner.execute (cả 2 nhánh diagnose) + registry wiring
- Architecture: arch-health 0 violations
- E2E: CLI thật
- Regression: full suite không giảm