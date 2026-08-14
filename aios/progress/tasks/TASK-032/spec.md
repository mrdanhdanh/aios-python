# Spec — TASK-032: H4 Evaluation Harness (M6)

**Trạng thái**: v3 (resolve critique ×2) → implement | **Nguồn**: orchestrator tự soạn (spec-writer không phản hồi — ghi nhận)

## 1. Mục tiêu

Test = "có đúng điều kiện không?"; **Evaluation = "chất lượng tốt đến mức nào?"** (PLAN §H4). Đánh giá **output** (score theo metric) và **trajectory** (Decision → Tool → Recovery → Output) theo **Suite** (metrics + thresholds), qua **Evaluation Model**: `Deterministic → Semantic → LLM Judge → Human → Composite` (LLM Judge KHÔNG mặc định). Kết quả **lưu được để tái lập** (INV-020 Evaluation Determinism).

## 2. Phạm vi

- MỚI: `backend/src/aios_core/harness/evaluation/` — contracts.py, errors.py, evaluators.py, trajectory.py, suites.py, evaluation.py, `__init__.py`
- SỬA (additive): `config.py` (+EvaluationSettings), `config.yaml` (+evaluation block), `runtime_kernel.py` (wiring EvaluationHarness), `tests/test_architecture.py` (+arch INV-020), `tests/test_harness_evaluation.py` (mới)
- KHÔNG MOD `_HARNESS_ALLOWED_AIOS`; không sửa Runtime/Orchestrator

## 3. Thiết kế

### 3.1 contracts.py (leaf)
- `EvaluationKind(str, Enum)`: DETERMINISTIC, SEMANTIC, LLM_JUDGE, HUMAN, COMPOSITE
- `Metric(BaseModel, extra=forbid)`: name: str, kind: EvaluationKind = DETERMINISTIC, params: dict = {}, weight: float = 1.0
- `Suite(BaseModel, extra=forbid)`: id: str, dataset: str = "", metrics: list[Metric] = [], thresholds: dict[str, float] = {} (default 0.8 — từ settings)
- `TrajectoryStep(BaseModel, extra=forbid)`: kind: str ("decision"|"tool"|"recovery"|"output"), tool: str|None, ok: bool|None, denied: bool = False, note: str = ""
- `Trajectory(BaseModel, extra=forbid)`: steps: list[TrajectoryStep], final_correct: bool|None, warning: bool = False, marks: dict[str, bool] = {}
- `EvaluationItem(BaseModel, extra=forbid)`: input: str, output: str, expected: str, trajectory: list[TrajectoryStep] = [], score: float|None = None (**P2-02: item-level score cho LLM/Human**) — C1-01
- `Score(BaseModel, extra=forbid)`: metric: str, value: float|None (None = inconclusive), threshold: float, passed: bool = False, kind: EvaluationKind — **aggregate mean per metric (C1-02)**
- `EvaluationResult(BaseModel, extra=forbid)`: suite_id, dataset, scores: list[Score], passed_all: bool, status: EvaluationStatus, trajectory: Trajectory|None (**trajectory item ĐẦU TIÊN có steps — P1-01**), summary: str, metrics: dict (counts — deterministic: items_total/items_passed/metrics_total/metrics_passed/inconclusive — P2-03), reproducible: dict = {} (**INV-020**: model/prompt_version/temperature khi LLM_JUDGE; rỗng khi deterministic — C3-03)
- `EvaluationStatus(str, Enum)`: PASSED, FAILED, INCONCLUSIVE

### 3.2 errors.py — `EvaluationError(Exception)`

### 3.3 evaluators.py — Evaluation Engine (offline deterministic)
- `DeterministicEvaluator.evaluate(metric, input_, output, expected) -> float`:
  - params.kind: `exact` (output == expected → 1.0/0.0), `contains` (expected in output), `regex` (re.search), `numeric_ge` (float(output) >= expected), `bool` (bool(output) == expected), mặc định `exact`
  - lỗi parse → 0.0 (ghi detail qua exception? không — trả 0.0 deterministic)
- `SemanticEvaluator.evaluate(metric, input_, output, expected) -> float`: Jaccard token overlap (offline, không LLM); params.threshold → pass nếu >= threshold (vẫn trả similarity float)
- `LLMJudgeEvaluator`: **stub offline** — `evaluate(...) -> float|None`: score từ **item.score hoặc params.get("score")** (P2-02); không có → None (inconclusive). `reproducible()` → dict {model, prompt_version, temperature} từ params (INV-020) — KHÔNG import aios_core.models
- `HumanEvaluator`: stub — score từ item.score/params.get("score"); không có → None (pending)
- `CompositeEvaluator`: weighted mean từ params.sub_scores (list[dict {metric,value,weight}] — C2-03); không có → None
- `Engine.evaluate(metric, item) -> float|None` — dispatch theo kind (item: dict có input/output/expected/score — C1-01)
- `Engine.score(metric, item, threshold) -> Score` — **threshold mặc định 0.8 nếu không truyền (C1-03)**; value None → passed False (inconclusive)

### 3.4 trajectory.py
- `TrajectoryEvaluator.analyze(steps: list[TrajectoryStep]) -> Trajectory`:
  - final_correct = last "output" step ok (nếu có)
  - warning = final_correct ∧ (có step denied hoặc recovery không ok) — **Final Correct / Trajectory Warning** (PLAN VD: gọi sai tool → deny → retry → đúng)
  - marks: {final_correct, trajectory_warning, had_recovery, had_denied, had_failed_tool}
  - metrics counts: steps by kind

### 3.5 suites.py — SuiteLoader (pattern TASK-031 scenarios.py)
- `load(dict|str|Path) -> Suite`; `load_many` (list | `suites:` key); json/yaml **safe_load**; lỗi → `SuiteError`
- Validate: metrics name duy nhất; thresholds chỉ metric đã khai (hoặc cảnh báo — chốt: bỏ qua threshold lạ, deterministic)

### 3.6 evaluation.py — EvaluationHarness (H1 kế thừa, pattern H2/H3)
- `EvaluationHarness(engine, *, state_service=None)` — id="evaluation", name="Evaluation", version="1.0.0"
- `run(ctx)`: suite = ctx.config["suite"] (Suite); items = ctx.config["items"] (list[EvaluationItem] — **P1-02**; cap max_items — C2-06); evaluate từng item → score per metric (mean aggregate — C1-02) + trajectory (analyze từng item; chọn item đầu có steps — P1-01); ctx.config["_result"] = EvaluationResult; return result.model_dump()
- `verify(ctx, payload)`: **persist TRƯỚC raise** (key "evaluation" — pattern H2 AC5): {suite_id, passed_all, status, scores, summary, reproducible, metrics}
  - passed_all False → raise EvaluationError (trừ ctx.config.get("strict", False) False → WARNING); **Suite.metrics rỗng → passed_all False (C2-07)**; score None → passed_all False (AC9)
- `get_result(run_id)` — dict từ state (P3-02)

### 3.7 Wiring + config
- `EvaluationSettings`: `default_threshold: float = 0.8` (C1-03), `strict: bool = True`, `max_items: int = 1000` (cap dataset — C2-06)
- config.yaml `evaluation:` block
- runtime_kernel: sau H3 — `EvaluationHarness(Engine(), state_service=...)` + register "evaluation"

## 4. Invariants (arch tests)
- **INV-020e**: evaluation/ không import `kernel.services.*` + `aios_core.models*` (LLM judge KHÔNG gọi model thật — stub offline)
- **INV-020f**: llm_judge reproducible: evaluators.py chứa literal `reproducible` + `prompt_version` (INV-020 fields)
- **INV-020g**: evaluation.py chứa `EvaluationError(` + `Engine(` (behavioral — fail → raise qua engine)
- **INV-020h**: suites.py dùng `yaml.safe_load` (pattern C2-07)

## 5. AC
| AC | Mô tả | Kiểm chứng |
|----|-------|-----------|
| AC1 | Contracts: EvaluationKind 5, Metric, Suite, Trajectory(Step), Score, EvaluationResult/Status — extra=forbid | unit |
| AC2 | DeterministicEvaluator: exact/contains/regex/numeric_ge/bool + 0.0 khi parse lỗi | unit |
| AC3 | SemanticEvaluator Jaccard deterministic; LLM stub score/None + reproducible; Human stub | unit |
| AC4 | CompositeEvaluator weighted mean | unit |
| AC5 | Engine dispatch + Score (None → inconclusive) | unit |
| AC6 | TrajectoryEvaluator: final_correct, warning (Final Correct/Trajectory Warning), marks, counts | unit |
| AC7 | SuiteLoader: dict/json/yaml safe_load; lỗi → SuiteError; thresholds lạ bỏ qua | unit |
| AC8 | EvaluationHarness qua H1: run+verify pass; strict raise; persist trước raise; get_result | unit + integration |
| AC9 | INCONCLUSIVE score → passed_all False | unit |
| AC10 | Reproducible fields khi LLM_JUDGE (model/prompt_version/temperature); rỗng khi deterministic | unit |
| AC11 | Config + wiring register "evaluation" | unit |
| AC12 | Arch INV-020e..h; **tổng ≥1370 tests (baseline 1299 + ≥70), coverage ≥90%** | full suite |

## 6. Không làm
- KHÔNG LLM thật (judge stub — deterministic v1); KHÔNG benchmark 100 scenarios (TASK-033); KHÔNG regression gate (TASK-033); KHÔNG sửa Runtime/Orchestrator
