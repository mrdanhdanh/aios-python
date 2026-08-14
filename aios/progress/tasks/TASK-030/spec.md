# TASK-030 — Execution Verification (M6-P11, H2)

**Metadata**: TASK-030 | M6/P11 | 2026-08-15 | v3 (critique-1 + critique-2 resolved) | AIOS Orchestrator
**Tiền đề**: TASK-029 H1 done (HarnessRunner/contracts/lifecycle/evidence — INV-017/018). TASK-030 là H2 — **quan trọng nhất M6** (PLAN §M6-3).
**Module đích**: `backend/src/aios_core/harness/execution/` (subdir H2) + `config.py`/`config.yaml` (MOD additive: block `harness.execution`) + `kernel/runtime_kernel.py` (MOD additive: wiring) + `tests/` (NEW `test_harness_execution.py` + MOD `test_architecture.py`)

## 1. Mục tiêu

Trả lời PLAN §M6-3: ***"Execution thành công ≠ Task thành công"*** — H2 kiểm chứng **post-condition** của execution, không chỉ "không exception". Pipeline:

```
Execution → Collect Evidence → Deterministic Checks → Policy Checks → Tests → Evaluation → Verdict
```

- **Verification Contract**: mỗi Execution có `Preconditions · Execution · Postconditions · Invariants · Evidence` (VD "Viết test cho module config" → PRE: module tồn tại; POST: test file tồn tại + test chạy thành công + coverage ≥ 90%).
- **Verdict**: `PASS · PASS_WITH_WARNING · FAIL · INCONCLUSIVE` — KHÔNG chỉ success=true/false.
- **Evidence Package** (audit/replay): 10 loại theo PLAN — collect từ Runtime (State/Event/Graph/Plan) + tự sinh verdict.json.
- **Replay**: `Production Run → Trace → Replay → Simulation → Debug` — không chạy lại Tool thật.
- **INV-019 Verification Before Verdict**: không PASS chỉ vì execution không exception — enforcement test.

## 2. Phạm vi

**In**:
- `harness/execution/` — NEW subdir: `contracts.py`, `evidence.py`, `pipeline.py`, `replay.py`, `verification.py` (VerificationHarness), `errors.py`, `__init__.py`
- `config.py` — MOD: `ExecutionSettings` (extra=forbid: `evidence_dir_prefix`, `policy_checks_enabled`?) + `Settings.harness.execution`
- `kernel/runtime_kernel.py` — MOD additive: wiring (VerificationHarness + registry register)
- `tests/test_harness_execution.py` — NEW: unit + integration + INV-019
- `tests/test_architecture.py` — MOD: `test_inv019_verification_before_verdict` (AST + behavioral), allow-list mở rộng (harness/execution)

**Out (không làm — tránh scope creep)**:
- KHÔNG sửa `kernel/services/*`, `kernel/events.py`, `kernel/graph/*`, `orchestrator/planning/*`, `harness/*` (H1) — chỉ GỌI public API; git diff sạch
- KHÔNG làm Test Harness (H3 — TASK-031), Evaluation/Benchmark (H4 — TASK-032/033), Doctor (H5 — TASK-034)
- KHÔNG làm Simulation Mode mới (H3) — Replay dùng mock/fake runner caller-injected
- KHÔNG LLM trong verification (deterministic-first; Evaluation = H4 — v1 pipeline chỉ deterministic checks + tests hook)
- KHÔNG emit event mới; KHÔNG API/CLI (task sau)

## 3. Input / Output

- **Input**:
  - `VerificationTask` (contract): `execution_ref: str` (**resolution C1-01: (1) `get_state(ref)` → (2) `get_state(f"graph:{ref}")` → (3) prefix `graph:` tra thẳng → (4) không thấy → evidence partial + INCONCLUSIVE; convention caller = plan.id**), `preconditions/postconditions/invariants: list[Check]`, **`base_dir: str = "."` (C2-04 — cho FILE_EXISTS/CONTAINS)**
  - `Check`: `name`, `kind` (FILE_EXISTS/TEST_RUN/COVERAGE/CONTAINS/CUSTOM), `params` — deterministic declarative
  - **`EvidenceServices` Protocol (C1-04 — duck-typed injectable, KHÔNG import kernel.graph/planning/observability)**: `state: get_state`, `events: query_audit`, `artifacts: store/list` — plan/graph json đọc qua `state.get_state(ref)["plan"|"graph"]`
  - `HarnessRunner` (H1) — verification là 1 Harness
- **Output**:
  - `Verdict`: PASS / PASS_WITH_WARNING / FAIL / INCONCLUSIVE + detail per-check
  - `EvidencePackage` — **v1 (C1-02: lệch PLAN có chủ đích — request.json/normalized-request.json KHÔNG có nguồn trong state)**: `plan.json, execution-graph.json (nếu có), runtime-events.json (C3-03: khác H1 events), tool-results/, test-results/, evaluation.json (nếu có), artifacts/, verdict.json`
  - `VerificationReport` (kế thừa HarnessReport + verdict/checks)

## 4. Yêu cầu chức năng

### YC-1 — Contracts (`contracts.py`, pydantic extra="forbid")
```python
class CheckKind(str, Enum): FILE_EXISTS="file_exists"; TEST_RUN="test_run"; COVERAGE="coverage"; CONTAINS="contains"; CUSTOM="custom"
class Check(BaseModel): name: str; kind: CheckKind; params: dict[str, Any] = {}
class VerificationTask(BaseModel): execution_ref: str; preconditions: list[Check]=[]; postconditions: list[Check]=[]; invariants: list[Check]=[]
class CheckResult(BaseModel): check: Check; passed: bool; detail: str = ""; skipped: bool = False
class Verdict(str, Enum): PASS="pass"; PASS_WITH_WARNING="pass_with_warning"; FAIL="fail"; INCONCLUSIVE="inconclusive"
class VerificationResult(BaseModel): execution_ref: str; verdict: Verdict; check_results: list[CheckResult]; summary: str; metrics: dict[str, Any] = {}
```
- **Test**: extra=forbid; CheckKind sai → ValidationError; Verdict đủ 4 giá trị.

### YC-2 — Evidence collection (`evidence.py`)
- `collect_evidence(task, services) -> dict[str, Any]` — collect qua `EvidenceServices` Protocol (C1-04): plan.json (`state[ref]["plan"]`), execution-graph.json (`state[f"graph:{id}"]["graph"]` nếu có — C1-01 resolution), **runtime-events.json (`query_audit(limit=10000)` + filter `payload.execution_id == resolved_ref` + sort asc — C2-05)**, evaluation.json (nếu có), artifacts refs
- **Critical set v1 (P1-01 v2 — OR theo namespace)**: `(plan.json nếu namespace=plan ∨ execution-graph.json nếu namespace=graph) ∧ runtime-events.json (plan-namespace cần ≥1 event khớp execution_id; graph-namespace chấp nhận [] — executor không emit, P2-02)`; thiếu → INCONCLUSIVE (trừ khi có check FAIL — C2-06); graph/artifacts = optional; **bỏ test-results/ + evaluation.json v1 (không nguồn deterministic — P2-04)**; tool-results/ = `state[ref]["results"]` dump từng node (P2-04); artifacts/ = `ArtifactService.list()` filter metadata
- **Truncation (P2-01)**: `if filtered_count == query_audit(limit=10000)` → `evidence["truncated"]=True` → verdict INCONCLUSIVE (không PASS khi evidence có thể thiếu)
- **Test**: execution có state+events → đủ file; thiếu graph → không crash; thiếu critical → INCONCLUSIVE; deterministic (cùng state → cùng dict trừ timestamps)

### YC-3 — Deterministic checks (`pipeline.py`)
- `run_checks(checks: list[Check], task: VerificationTask, test_runner=None) -> list[CheckResult]` — thực thi từng Check deterministic:
  - FILE_EXISTS: `task.base_dir / params.path` tồn tại
  - CONTAINS: file chứa params.text
  - TEST_RUN / COVERAGE: **runner contract (C2-07): `Callable[[str], tuple[bool, float]]`** — path → (success, line_coverage_pct); **runner None → skipped (không crash)**; COVERAGE: `success and coverage >= params.coverage_min`; TEST_RUN: success
  - CUSTOM: callable injectable
- **Test**: mỗi kind 1 test; file không tồn tại → passed=False; runner None → skipped; deterministic 2 lần

### YC-4 — Verdict logic (`pipeline.py`)
- `compute_verdict(check_results, has_critical_evidence) -> Verdict` — **thứ tự ưu tiên (C2-06): check-derived FAIL > INCONCLUSIVE (thiếu evidence) > PASS**
  1. Postcondition hoặc Invariant FAIL → **FAIL** (INV-019: execution ok nhưng postcondition fail → FAIL)
  2. Precondition FAIL → INCONCLUSIVE (task không thể chạy đúng)
  3. **Postcondition SKIPPED → INCONCLUSIVE (C1-03 — KHÔNG bao giờ PASS khi postcondition không được kiểm chứng; detail "check skipped: ...")**; invariant/precondition skipped → PASS_WITH_WARNING
  4. Không có critical evidence (plan.json/runtime-events.json) → INCONCLUSIVE
  5. Mọi check pass + ≥1 warning → PASS_WITH_WARNING; toàn pass → PASS
- **Test**: 6 nhánh; đặc biệt: (a) execution ok + postcondition fail → FAIL; (b) runner None + postcondition khác pass → INCONCLUSIVE (KHÔNG PASS); (c) postcondition fail + thiếu events → FAIL (không INCONCLUSIVE)

### YC-5 — VerificationHarness (`verification.py` — kế thừa Harness H1)
```python
class VerificationHarness(Harness):
    id = "verification"; name = "Verification"; version = "1.0.0"
    def __init__(self, services: EvidenceServices, test_runner=None): ...
    def run(self, ctx):  # ctx.config chứa VerificationTask → pipeline → VerificationResult
        # C2-01: persist VerificationResult TRƯỚC khi return (state `verification=` + verdict.json qua ArtifactService)
    def verify(self, ctx, payload):  # INV-019: payload.verdict FAIL → raise (sau khi đã persist — C2-01)
```
- EvidencePackage lưu qua H1 evidence — verdict.json luôn tồn tại
- **Test**: run task thành công → PASS; postcondition fail → verify raise (H1 FAILED) NHƯNG `state[run_id]["verification"]["verdict"] == "fail"` + verdict.json trong artifacts (C2-01 AC)

### YC-6 — Replay (`replay.py`)
- `replay(evidence: dict) -> ReplayResult` — **round-trip integrity check (P2-03 v2)**: đọc `verdict.json` (verdict + check_results) từ evidence → tái tính verdict bằng `compute_verdict(check_results, has_critical_evidence)` → `diff` = lệch giữa verdict GHI trong evidence và verdict TÁI TÍNH (phát hiện tamper/thay đổi logic) — KHÔNG chạy lại check trên FS
- `ReplayResult`: `trace_reconstructed: list[dict]` (runtime-events asc, tie-break (timestamp, id) — P3-02), `verdict_replayed: Verdict`, `diff: list[str]`
- **Test**: replay evidence gốc → diff == []; **sửa tay verdict.json (pass→fail nhưng check_results có FAIL) → diff ≠ [] (phát hiện tamper)**; timestamps không tạo diff giả

### YC-7 — Wiring + config (additive)
- `config.py`: `ExecutionSettings(collect_runtime_evidence: bool = True)` (C3-02: chỉ gate collect từ State/Events; runner H1 vẫn luôn tạo events/report — không vi phạm INV-018) + `Settings.harness.execution`
- `runtime_kernel.create()`: dựng `VerificationHarness(services={state, events, artifacts})` + `harness_registry.register(verification_harness)` — sau block H1
- **Test**: resolve registry.get("verification") trả harness; run e2e qua runner H1

## 5. Yêu cầu kiến trúc

### 5.1 INV-019 — Verification Before Verdict
- Bản chất: không PASS chỉ vì execution không exception — **behavioral**: execution ok + postcondition fail → Verdict FAIL (test)
- AST: `pipeline.py` phải chứa logic verdict — literal `Verdict.FAIL` trong pipeline; `verification.py` verify hook raise khi verdict FAIL (literal `raise` + `Verdict.FAIL`)
- Allow-list `harness/execution/` (**P1-02 v2 — CHỐT duck-typed thuần**): `EvidenceServices` Protocol (đặt contracts.py — P3-01) khai báo `Callable`/`Any`; evidence.py KHÔNG import `kernel.events`/`kernel.services.events`/`kernel.graph`/`orchestrator.planning`; `runtime_kernel.py` (ngoài harness/) là nơi duy nhất import EventService → **KHÔNG MOD `_HARNESS_ALLOWED_AIOS`**; aios allowed giữ nguyên H1: config, logging, kernel.services.state, kernel.services.artifacts, contracts.artifact + intra harness
- Deterministic: checks/vérđict thuần; evidence collect deterministic (trừ timestamps)
- No God Object: pipeline tách module (contracts/evidence/pipeline/replay/verification); verification.py không chứa run_checks/collect_evidence logic (chỉ điều phối)

### 5.2 Additive only
- git diff: `harness/*` (H1) không đổi; `kernel/services/*`, `kernel/events.py`, `kernel/graph/*`, `orchestrator/planning/*` không đổi; chỉ thêm `harness/execution/` + config + wiring + tests

## 6. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — CheckKind/Check/VerificationTask/CheckResult/Verdict/VerificationResult extra=forbid; Verdict 4 giá trị (YC-1)
- [ ] **AC2**: Evidence collect — đủ file có sẵn; thiếu nguồn không crash; deterministic (YC-2)
- [ ] **AC3**: Checks — 5 kinds; file không tồn tại → failed; runner None → skipped; deterministic (YC-3)
- [ ] **AC4**: Verdict logic — 5 nhánh; **INV-019: execution ok + postcondition fail → FAIL** (YC-4)
- [ ] **AC5**: VerificationHarness — run task → PASS; postcondition fail → verify raise (H1 FAILED); evidence đủ (YC-5)
- [ ] **AC6**: Replay — trace khớp; runner None không crash; verdict_replayed khớp (YC-6)
- [ ] **AC7**: Wiring — registry.get("verification") + e2e qua HarnessRunner; config parse (YC-7)
- [ ] **AC8**: INV-019 — behavioral test + AST literal (pipeline Verdict.FAIL + verification verify raise) (§5.1)
- [ ] **AC9**: Allow-list harness/execution pass; additive only (git diff) (§5.2)
- [ ] **AC10**: Full suite pytest pass (**≥ 45 test mới, tổng ≥ 1169 — C3-04**), coverage hard ≥ 90% (mục tiêu ≥ 95%)

## 7. Rủi ro & giả định
- Evidence nguồn không có (graph/plan chưa chạy) → evidence partial → INCONCLUSIVE — giả định rõ
- TEST_RUN/COVERAGE cần runner thật — v1 caller-injected; không có → skipped (không giả PASS)
- Replay không chạy tool thật (simulation tinh thần) — đúng PLAN
- VerificationHarness run FAILED khi verdict FAIL — INV-019 mạnh; caller đọc VerificationResult từ evidence/state

## 8. Expected artifacts
- NEW: `harness/execution/{contracts,evidence,pipeline,replay,verification,errors,__init__}.py`
- MOD: `config.py` (ExecutionSettings), `config.yaml`, `runtime_kernel.py` (wiring + register)
- NEW: `tests/test_harness_execution.py`; MOD: `tests/test_architecture.py`, `tests/test_config.py`, `tests/test_runtime_kernel.py`
