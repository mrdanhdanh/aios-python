# Spec — TASK-034: H5 Doctor & Readiness (M6)

**Trạng thái**: v1 → critique ×2 → implement | **Nguồn**: orchestrator tự soạn (spec-writer không phản hồi — ghi nhận)

## 1. Mục tiêu

**AIOS Doctor Harness** (PLAN §H5 — nâng cấp `aiagent doctor` thành harness, không tạo Doctor mới hoàn toàn): 13 loại Doctor (Architecture, Runtime, Workflow, Agent, Capability, Tool, Memory, Model, Policy, Registry, Performance, Security, Evidence) — mỗi loại trả `PASS · WARNING · ERROR · UNKNOWN`. **Readiness Score**: overall % + **hard gates** (`Policy violation > 0 → RELEASE BLOCKED` dù overall 99%).

## 2. Phạm vi

- MỚI: `backend/src/aios_core/harness/doctor/` — contracts.py, errors.py, checks.py, doctor.py, readiness.py, `__init__.py`
- SỬA (additive): `config.py` (+DoctorSettings), `config.yaml`, `runtime_kernel.py` (wiring DoctorHarness + ReadinessHarness), `tests/test_architecture.py` (arch), `tests/test_harness_doctor.py` (mới)
- KHÔNG MOD `_HARNESS_ALLOWED_AIOS`; không sửa Runtime/Orchestrator (doctor checks injectable — duck-typed)

## 3. Thiết kế

### 3.1 contracts.py (leaf)
- `DoctorKind(str, Enum)`: ARCHITECTURE, RUNTIME, WORKFLOW, AGENT, CAPABILITY, TOOL, MEMORY, MODEL, POLICY, REGISTRY, PERFORMANCE, SECURITY, EVIDENCE (13 — PLAN)
- `DoctorStatus(str, Enum)`: PASS, WARNING, ERROR, UNKNOWN
- `DoctorResult(BaseModel, extra=forbid)`: kind: DoctorKind, status: DoctorStatus, score: float = 0.0 (0..1), details: list[str] = [], checks_total: int = 0, checks_passed: int = 0
- `HardGate(BaseModel, extra=forbid)`: name: str, passed: bool, detail: str = ""
- `ReadinessReport(BaseModel, extra=forbid)`: dimensions: dict[str, float] (kind→score), overall: float, hard_gates: list[HardGate], ready: bool, summary: str, metrics: dict (counts — deterministic), reproducible: dict = {}

### 3.2 errors.py — `DoctorError(Exception)`, `ReadinessError(DoctorError)`

### 3.3 checks.py — Doctor check registry (deterministic)
- `CheckFn = Callable[[], tuple[DoctorStatus, float, list[str]]]` — (status, score, details)
- `DoctorChecks` — dict kind → CheckFn; `register(kind, fn)`, `run(kind) -> DoctorResult`, `run_all() -> list[DoctorResult]`
- Default checks (nếu chưa register — placeholder deterministic): PASS với score 1.0, checks 0/0 — ghi rõ placeholder
- Check fn có thể raise → ERROR status (bắt exception, deterministic)

### 3.4 doctor.py — DoctorHarness (H1 pattern)
- `DoctorHarness(checks: DoctorChecks, *, state_service=None)` — id="doctor", name="Doctor", version="1.0.0"
- `run(ctx)`: kinds = ctx.config.get("kinds") (list[str]|None → tất cả 13); results = checks.run_all(kinds); ctx.config["_results"] = results; return [r.model_dump()...]
- `verify(ctx, payload)`: **persist TRƯỚC raise** (key "doctor"): {kinds, results summary (status per kind), counts}
  - bất kỳ status ERROR → raise DoctorError (strict flag; strict=False → WARNING)
- `get_results(run_id)` — dict từ state

### 3.5 readiness.py — ReadinessScorer + ReadinessHarness
- `ReadinessScorer(min_overall: float = 0.0, policy_gate: bool = True)`:
  - `score(results: list[DoctorResult], policy_violations: int = 0) -> ReadinessReport`
  - dimensions: kind → score (mean nếu nhiều kết quả cùng kind — không xảy ra; per kind 1 result)
  - overall = mean scores (UNKNOWN → score 0.0 — deterministic; ghi note)
  - hard_gates: [PolicyGate: policy_violations > 0 → fail (**RELEASE BLOCKED** — PLAN), OverallGate: overall < min_overall → fail]
  - ready = overall gate ∧ policy gate
- `ReadinessHarness(checks, scorer, *, state_service=None)` — id="readiness", name="Readiness", version="1.0.0"
  - `run(ctx)`: policy_violations = ctx.config.get("policy_violations", 0); results = checks.run_all(); report = scorer.score(results, policy_violations); ctx.config["_report"] = report; return report.model_dump()
  - `verify(ctx, payload)`: **persist TRƯỚC raise** (key "readiness"): {overall, ready, hard_gates, dimensions, summary}
    - ready False → raise ReadinessError ("RELEASE BLOCKED" — strict; strict=False → WARNING)
  - `get_report(run_id)`

### 3.6 Wiring + config
- `DoctorSettings`: `strict: bool = True`, `min_overall: float = 0.0`, `policy_gate: bool = True`
- config.yaml `doctor:` block
- runtime_kernel: sau benchmark — DoctorHarness + ReadinessHarness với default checks (placeholder deterministic); register "doctor" + "readiness"

### 3.7 Arch tests
- **INV-022a** (doctor/): không import kernel.services.execution|events|resource|scheduler + kernel.graph|orchestrator.planning (checks injectable)
- **INV-022b**: contracts.py chứa literal 13 DoctorKind names (ARCHITECTURE...EVIDENCE — đếm >= 13)
- **INV-022c**: readiness.py chứa literal `RELEASE BLOCKED` (hard gate policy — PLAN) + `policy_violations`
- **INV-022d**: doctor.py/readiness.py chứa `DoctorError(`/`ReadinessError(` + persist trước raise (behavioral)
- Không cần thêm external allow-list (pydantic/typing/enum/datetime/collections có sẵn)

## 4. AC
| AC | Mô tả | Kiểm chứng |
|----|-------|-----------|
| AC1 | Contracts: DoctorKind 13, DoctorStatus 4, DoctorResult, HardGate, ReadinessReport | unit |
| AC2 | DoctorChecks: register/run/run_all; placeholder default PASS; fn raise → ERROR | unit |
| AC3 | DoctorHarness qua H1: run kinds subset + all; ERROR → DoctorError; persist trước raise; get_results | unit + integration |
| AC4 | strict=False → WARNING | unit |
| AC5 | ReadinessScorer: dimensions + overall mean (UNKNOWN → 0.0); metrics counts | unit |
| AC6 | Hard gates: policy_violations > 0 → RELEASE BLOCKED (dù overall cao); min_overall fail | unit |
| AC7 | ready = overall ∧ policy gates; summary đúng | unit |
| AC8 | ReadinessHarness qua H1: run+verify; blocked → ReadinessError; persist trước raise; get_report | unit + integration |
| AC9 | Deterministic repeat (cùng input → cùng report) | unit |
| AC10 | Config + wiring register "doctor" + "readiness" | unit |
| AC11 | Arch INV-022a..d; **tổng ≥1520 tests (baseline 1450 + ≥65), coverage ≥90%** | full suite |

## 5. Không làm
- KHÔNG tự chạy health check thật (checks injectable — v1 placeholder + user inject); KHÔNG CLI/API mới; KHÔNG đụng observability/doctor.py M4 (system doctor cũ — giữ nguyên)
