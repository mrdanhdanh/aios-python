# TASK-026 — Planning Engine (M5-P9, Phase 3)

**Metadata**: TASK-026 | M5/P9 | 2026-08-15 | v4 (critique ×2 + review resolved) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/orchestrator/planning/` (subpackage mới) + `orchestrator/errors.py` (MOD additive) + `config.py`/`config.yaml` (MOD additive: block `planning`) + `kernel/runtime_kernel.py` (MOD additive: wiring) + `tests/` (NEW `test_planning_engine.py` + MOD `test_architecture.py` + MOD `test_runtime_kernel.py`)

## 1. Mục tiêu

Xây **Planning Engine** — nâng cấp `Planner → ExecutionPlan` (PLAN §11) thành pipeline 7 bước:

```
Goal → Goal Analyzer → Task Decomposer → Dependency Analyzer
     → Capability Resolver → Risk Analyzer → Execution Planner → Execution Graph
```

- Pipeline biến **goal** (request người dùng) thành **ExecutionPlan DAG** (nodes + `depends_on`) sẵn sàng cho Execution Graph (TASK-027) consume.
- Giữ triết lý **offline-first / deterministic-first** (PLAN §13): `Known workflow → Template planning → Rule planning → LLM planning`. Workflow Library có sẵn → KHÔNG gọi LLM; task đơn giản → KHÔNG gọi LLM; chỉ task phức tạp/mở mới gọi Planner LLM (Planner cũ giữ nguyên làm fallback).
- **Plan Validation** (PLAN §14, INV-014): plan phải validate **đủ 8 hạng mục** trước khi trả ra: `Contract · Capability · Permission · Policy · Dependency · Resource · Cycle · Timeout` — VD `T1→T2→T3→T1` → reject (circular dependency).
- **No God Object** (pattern TASK-025 §5.4): 7 module nhỏ + 1 validator, mỗi module 1 trách nhiệm; `PlanningEngine` chỉ điều phối.
- TASK-026 trả lời câu hỏi M5 *"Nên làm những bước nào?"* — đây là đầu vào của TASK-027 *"Các bước phụ thuộc nhau thế nào?"*.

## 2. Phạm vi

**In**:
- `orchestrator/planning/` — NEW subpackage: `contracts.py`, `goal_analyzer.py`, `task_decomposer.py`, `dependency_analyzer.py`, `capability_resolver.py`, `risk_analyzer.py`, `templates.py`, `execution_planner.py`, `validation.py`, `engine.py`, `__init__.py`
- `orchestrator/errors.py` — MOD (additive): thêm `PlanningError(OrchestratorError)`
- `config.py` — MOD (additive): `PlanningSettings` (pydantic `extra="forbid"`, mirror contract) + `Settings.planning: PlanningSettings = PlanningSettings()`
- `config.yaml` — MOD (additive): block `planning` (defaults)
- `kernel/runtime_kernel.py` — MOD (additive): wiring block `register_instance(PlanningEngine, ...)` (cuối `create()`)
- `tests/test_planning_engine.py` — NEW: unit + integration + INV-014 behavioral
- `tests/test_architecture.py` — MOD: `test_inv_planning_import_allowlist` + `test_inv014_planning_gate` + `test_inv014_runtime_no_planning` + `test_inv014_no_god_object` (pattern TASK-025 §5.4)
- `tests/test_runtime_kernel.py` — MOD (additive): resolve `PlanningEngine` (pattern `test_model_router_wired`)

**Out (không làm — tránh scope creep)**:
- **KHÔNG làm Execution Graph contract** (`GraphNode`/`GraphEdge`/`JoinPolicy`/`FailurePolicy`/`GraphState`) — là TASK-027 (PLAN §15–17). Spec này chỉ tạo `ExecutionPlan` DAG (nodes + `depends_on`) — **đủ cho 027 convert sang graph** (ghi rõ mapping tiêu thụ ở §3 Output)
- **KHÔNG làm Parallel Scheduler** — TASK-028; không sửa `ResourceService`/`SchedulerService`
- **KHÔNG sửa `ExecutionService`** (kernel/services/execution.py) — runtime consume plan như hiện tại; INV-007 policy-first giữ nguyên
- **KHÔNG sửa `ExecutionPlan`/`PlanNode`** (kernel/execution_plan.py) — quyết định **tái dùng** (§5.6): Planning Engine là builder mở rộng, không tạo contract v2
- **KHÔNG sửa `Planner`/`PlannerStub` API cũ** (planner.py) — Planner giữ nguyên làm LLM fallback, Planning Engine gọi nó
- **KHÔNG sửa `orchestrator.py` v1** (Decision Pipeline hiện tại) — nối Planning Engine vào flow orchestration là việc của TASK-027/028 (PLAN §20); spec này wiring ở composition root để 027 resolve được
- **KHÔNG import `aios_core.models.*` trong planning/** (INV-005 rule A, kể cả TYPE_CHECKING — bài học TASK-023 C2-01): model/router **inject instance untyped** (pattern `Orchestrator.model` hiện tại — ghi nhận TASK-025 §5.1)
- **KHÔNG tích hợp `orchestrator/goals/`** (GoalManager/TaskQueue — subsystem M2) — Goal Analyzer dùng contract `GoalAnalysis` local, deterministic; nối GoalManager là task sau (ghi giả định §7)
- **KHÔNG gọi `ResourceService.acquire_*` trong validation** — resource check chỉ so sánh ước lượng với `ResourcesSettings` (không side effect chiếm resource)
- **KHÔNG emit event mới** (EventType giữ nguyên); observability "planning latency" (M5 DoD) — số liệu nằm trong `PlanningResult` (return value), gắn metrics ở task sau
- **KHÔNG làm**: multi-tenant, distributed, auto-tuning, LLM decomposition trực tiếp (decomposition luôn deterministic — §YC-3), plan persistence/replay (M5 scope guard PLAN §M5-1)

## 3. Input / Output

- **Input**:
  - `PlanningRequest` (pydantic `extra="forbid"`): `text: str` (goal), `source: str = "cli"`, `context: dict[str, Any] = {}` (free-form: target path, constraints — deterministic fields do analyzer đọc), `policy: str | None = None` (tên routing policy cho LLM path — forward tới `ModelRouter`; None → router default)
  - `WorkflowLibrary` — nguồn known workflow (PLAN §13: có workflow → 0 LLM)
  - `CapabilityRegistry` — nguồn sự thật capability (Capability Resolver + Validation mục capability)
  - `PolicyService` (optional inject) — validation mục policy (deterministic, không side effect ngoài event — giả định §7)
  - `ResourcesSettings` (optional inject) — validation mục resource (budget tokens)
  - `Planner` (optional) + `model` (untyped, `ModelContract`) + `router` (untyped, `ModelRouter`) + **`registry` (untyped, `ModelRegistry` — C1-01: `model = registry.get(router.last_decision.model_name)`; runtime_kernel đã có sẵn `model_registry`)** — LLM planning fallback (PLAN §13); `planner=None` → planning phức tạp trả `PlanningError` "llm planning unavailable" (không silently trả plan rỗng)
  - `PlanningSettings` (config, defaults đủ chạy offline)
- **Output**:
  - `PlanningEngine.plan(request: PlanningRequest) -> PlanningResult`:
    - `plan: ExecutionPlan` (status `READY` — đã qua validation 8 hạng mục), `source: PlanSource` (`workflow|template|rule|llm`), `llm_calls: int` (số lần gọi planner LLM trong request này), `validation: PlanValidationReport` (luôn valid khi trả plan), `needs_approval: bool` (policy yêu cầu human approval — PLAN Decision Pipeline tầng 4), `reasoning: str`, `goal: GoalAnalysis`, `risks: RiskReport`, `latency_ms: int`
    - **Ranh giới TASK-027**: `plan.nodes` (list `PlanNode`: `id/type/name/agent/capabilities/depends_on/timeout_s/retries`) + `plan.required_permissions` + `plan.required_resources` + `plan.estimated_cost/tokens` là **đủ** để 027 dựng `GraphNode`/`GraphEdge` (edge = `depends_on`; join/failure policy mapping ở 027)
  - Invalid plan → **raise `PlanningError`** kèm `report: PlanValidationReport` (mọi issue fatal — §YC-8); **không bao giờ trả plan chưa validate** (INV-014 gate)
  - Property `PlanningEngine.llm_calls` (cumulative, thread-safe) + `reset_calls()` + `last_result` (thread-safe, pattern `ModelRouter.last_decision`) — phục vụ observability/test offline-first

## 4. Yêu cầu chức năng

### YC-1 — Contracts (`orchestrator/planning/contracts.py`, pydantic `extra="forbid"`)
```python
class PlanSource(str, Enum):
    WORKFLOW = "workflow"      # known workflow (PLAN §13 bậc 1)
    TEMPLATE = "template"      # template planning (bậc 2)
    RULE = "rule"              # rule planning (bậc 3)
    LLM = "llm"                # llm planning (bậc 4 — fallback cuối)

class GoalComplexity(str, Enum):
    SIMPLE = "simple"          # 1-2 bước, không cần phân rã
    COMPLEX = "complex"        # cần phân rã deterministic (template/rule)
    OPEN = "open"              # mở, cần LLM

class GoalAnalysis(BaseModel):        # extra="forbid"
    intent: str                        # chuẩn hóa: chat|coding|review|test|doctor|system|skill|upgrade|diagnose
    target: str = ""                   # đối tượng (module/path — trích rule-based)
    complexity: GoalComplexity
    requirements: list[str] = []       # ràng buộc trích được (deterministic)
    matched_workflow: str | None = None  # library.search hit → source workflow
    source: PlanSource

class TaskSpec(BaseModel):            # extra="forbid"
    id: str                            # "T1".."Tn" (đặt số thứ tự deterministic)
    name: str
    type: PlanNodeType                 # reuse kernel.execution_plan.PlanNodeType
    description: str = ""
    capabilities: list[str] = []
    agent: str = ""
    depends_on: list[str] = []
    timeout_s: float = 300.0
    retries: int = 0

class RiskItem(BaseModel):            # extra="forbid"
    level: Literal["low", "medium", "high"]
    kind: str                          # "unknown_capability"|"missing_agent"|"high_cost"|"many_nodes"|"open_goal"
    message: str

class RiskReport(BaseModel):          # extra="forbid"
    items: list[RiskItem] = []         # sorted by (level, kind) — deterministic
    @property
    def highest(self) -> str | None    # "high" > "medium" > "low" > None

class ValidationRule(str, Enum):      # 8 hạng mục PLAN §14
    CONTRACT = "contract"; CAPABILITY = "capability"; PERMISSION = "permission"
    POLICY = "policy"; DEPENDENCY = "dependency"; RESOURCE = "resource"
    CYCLE = "cycle"; TIMEOUT = "timeout"

class PlanValidationIssue(BaseModel): # extra="forbid"
    rule: ValidationRule
    node_id: str = ""                  # "" = plan-level
    message: str
    fatal: bool                        # fatal → reject; non-fatal → report + needs_approval

class PlanValidationReport(BaseModel): # extra="forbid"
    issues: list[PlanValidationIssue] = []   # sorted by (rule, node_id) — deterministic
    @property
    def valid(self) -> bool            # không có issue fatal

class PlanningResult(BaseModel):       # extra="forbid" (plan là ExecutionPlan — pydantic model)
    plan: ExecutionPlan               # C3-02: bắt buộc — không None (invalid → raise)
    source: PlanSource
    llm_calls: int
    validation: PlanValidationReport
    needs_approval: bool = False
    reasoning: str = ""
    goal: GoalAnalysis | None = None
    risks: RiskReport = RiskReport()
    latency_ms: int = 0
```
- `PlanningError(OrchestratorError)` thêm vào `orchestrator/errors.py` (MOD additive): `__init__(self, message: str, report: PlanValidationReport | None = None)` — `report` property để enforcement test assert issue cycle
- **Test**: mọi contract `extra="forbid"` (field thừa → `ValidationError`); `RiskReport.highest` đúng thứ tự ưu tiên; `PlanValidationReport.valid` đúng (1 fatal → False); `ValidationRule` đủ đúng 8 giá trị PLAN §14; `PlanningError` giữ `report`

### YC-2 — Goal Analyzer (deterministic — `goal_analyzer.py`)
- `analyze(request: PlanningRequest, library: WorkflowLibrary) -> GoalAnalysis` — **thuần rule, không LLM, không network**:
  1. Intent mapping deterministic — **keyword table LOCAL trong goal_analyzer (C2-02: KHÔNG import rule_engine — allow-list §5.2)**: `review|analyze|audit` → `review`; `test|write tests` → `test`; `fix|refactor|implement` → `coding`; `medical|doctor|symptom` → `doctor`; fallback → `chat`
  2. Target: trích chuỗi sau intent keyword (regex đơn giản)
  3. Complexity: intent ∈ {chat, system, skill, diagnose} + text ngắn → `SIMPLE`; intent ∈ {review, test, coding} + có target → `COMPLEX`; intent không nhận diện được HOẶC text chứa cờ mở ("analyze the whole project", "propose", "design") → `OPEN`
  4. **Known workflow check (bậc 1 PLAN §13) — token-match LOCAL (C2-03, không phụ thuộc `library.search()` substring)**: tách keywords từ `library.list()` names — **tokenizer (C2-06): `re.split(r"[^a-z0-9]+", name.lower())` cho cả name lẫn text (split mọi ký tự không chữ-số — khớp hyphen/underscore)**; text chứa ≥ 1 token khớp name → `matched_workflow = name` (chọn name khớp nhiều token nhất — tie-break name asc), `source = WORKFLOW`
- **Test**: "Review module authentication và viết test" → intent `review`, target chứa "authentication", complexity `COMPLEX`; "check status" → `SIMPLE`; "Phân tích toàn bộ dự án rồi đề xuất kiến trúc mới" → `OPEN`; library có workflow "crud-generator" + text "Create CRUD API" (fixture description chứa "create crud api" hoặc name token-match) → `matched_workflow == "crud-generator"`, `source == WORKFLOW`; cùng input 2 lần → `model_dump()` y hệt (deterministic)

### YC-3 — Task Decomposer (deterministic — `task_decomposer.py` + `templates.py`)
- `decompose(goal: GoalAnalysis, request: PlanningRequest) -> list[TaskSpec]` — **3 đường, không LLM**:
  1. `goal.source == WORKFLOW` → bỏ qua decomposer (compiler trực tiếp — §YC-7 known-workflow path)
  2. **Template planning** (`templates.py`): `TASK_TEMPLATES: dict[str, TemplateSkeleton]` — skeleton khai báo `intent → steps`; VD §12 template `review`:
     ```python
     TASK_TEMPLATES = {
       "review": TemplateSkeleton(
         intent="review",
         steps=[
           StepSpec(id="T1", name="Analyze module", type=PlanNodeType.LLM,  # C2-04: type trực tiếp (bỏ kind)
                    capabilities=["code_analysis"], depends_on=[]),
           StepSpec(id="T2", name="Scan vulnerabilities", type=PlanNodeType.TASK,
                    capabilities=["code_analysis"], depends_on=["T1"]),
           StepSpec(id="T3", name="Scan missing tests", type=PlanNodeType.TASK,
                    capabilities=["code_analysis"], depends_on=["T1"]),
           StepSpec(id="T4", name="Write tests", type=PlanNodeType.TASK,
                    capabilities=["test_writing"], depends_on=["T2", "T3"]),
           StepSpec(id="T5", name="Run tests", type=PlanNodeType.TOOL,
                    capabilities=["test_run"], depends_on=["T4"]),
           StepSpec(id="T6", name="Report", type=PlanNodeType.TASK,
                    capabilities=["reporting"], depends_on=["T5"]),
         ],
       ),
       # "test" → [T1 Write tests → T2 Run → T3 Report]; "coding" → [T1 Implement → T2 Verify → T3 Report] ...
     }
     ```
     **VD §12 yêu cầu exact**: decompose("review", ...) → đúng 6 node T1..T6 với dependency `T1→{T2,T3}→T4→T5→T6`
  3. **Rule planning (C3-04 — phân biệt TEMPLATE vs RULE)**: `goal.complexity == SIMPLE` → 1 node duy nhất (`T1 <intent>` type theo intent: chat→llm, system→tool...) — không gọi LLM; **template = intent có trong `TASK_TEMPLATES` (→ TEMPLATE); rule = SIMPLE hoặc COMPLEX KHÔNG có template và không OPEN (→ RULE, skeleton tối giản theo intent: vd `test` → [write, run, report])**
  4. `goal.complexity == OPEN` và không template → **trả rỗng** (engine quyết định xuống LLM path §YC-10) — decomposer KHÔNG tự gọi planner (1 trách nhiệm)
- `TemplateSkeleton.register(name, skeleton)` API (additive, thread-safe, pattern `WorkflowLibrary.register`) — mở rộng được mà không đổi code decomposer
- Node id luôn `T<n>` theo thứ tự skeleton (deterministic; không nhảy số)
- **Test**: decompose("review") → đúng 6 node §12 (id, name, capabilities, depends_on, **type exact — C2-04**); "check status" (SIMPLE) → đúng 1 node; intent `test` không template → skeleton rule [T1,T2,T3] (source RULE — C3-04); **intent `review` → source TEMPLATE (phân biệt rõ — C3-04)**; `OPEN` → rỗng; register template mới → decompose dùng được ngay; cùng input 2 lần y hệt

### YC-4 — Dependency Analyzer (deterministic — `dependency_analyzer.py`)
- `analyze(tasks: list[TaskSpec]) -> list[TaskSpec]` — **normalize + verify dependency** (không thêm/sửa cạnh):
  1. Mọi `depends_on` phải trỏ node tồn tại (khác id chính nó) — vi phạm → đánh dấu task bị lỗi (fatal issue ở validator, analyzer chỉ đánh dấu `invalid` flag nội bộ)
  2. Sắp xếp lại tasks theo topological order (stable — dùng `validate_dag` adjacency hoặc Kahn với tie-break id asc) — `TaskSpec` trả về giữ nguyên id nhưng thứ tự topo để planner build đúng
  3. KHÔNG thêm cạnh (VD §12 dependency do template/rule khai báo — analyzer chỉ verify + order)
- **Test**: VD §12 6 node → topo order hợp lệ (T1 trước T2/T3, T4 sau T2/T3, T6 cuối), id giữ nguyên; node depends_on chính nó → flag invalid; depends_on unknown id → flag invalid; 2 lần chạy y hệt

### YC-5 — Capability Resolver (deterministic — `capability_resolver.py`)
- `resolve(tasks: list[TaskSpec], capabilities: CapabilityRegistry) -> tuple[list[TaskSpec], RiskReport]`:
  1. Mỗi `task.capabilities[i]` phải ∈ `capabilities.list()` — không có → **issue fatal** (`ValidationRule.CAPABILITY`) + risk `high/unknown_capability`; task có capabilities rỗng → chấp nhận (không yêu cầu gì)
  2. `task.agent` trống nhưng plan-level agent đã biết (từ goal.intent map: review→coder, test→coder, chat→general — mapping deterministic local) → điền agent
  3. Risk: capability tồn tại nhưng `capabilities.tools_for(cap)` rỗng → risk `medium` "capability has no tools"
- **Test**: registry có {code_analysis, test_writing, test_run, reporting} → 6 node review resolve sạch, không issue; task yêu cầu capability "unknown_cap" → issue fatal + risk high; agent điền đúng theo intent; tool rỗng → risk medium; deterministic 2 lần

### YC-6 — Risk Analyzer (deterministic — `risk_analyzer.py`)
- `analyze(goal: GoalAnalysis, tasks: list[TaskSpec], settings: PlanningSettings) -> RiskReport` — thuần hàm (C2-03 v2: bỏ plan_hint; **estimated_tokens tính từ tasks type count — công thức 2000/200, nguồn duy nhất**):
  - `OPEN` goal (không có matched workflow/template) → risk `high/open_goal`
  - số node > `settings.max_nodes // 2` → risk `medium/many_nodes`
  - `estimated_tokens` (ước lượng sơ bộ: node LLM ~ 2000 tokens/node, khác ~ 200) vượt `settings.warn_token_threshold` → risk `medium/high_cost`
  - mọi task có agent trống sau resolver → risk `medium/missing_agent`
- Sort items theo (level, kind) — deterministic
- **Test**: VD §12 (6 node, 1 LLM node) → **assert exact `items == []` (C3-01 — 6 node < max/2, tokens thấp, agent đủ, không OPEN)**; OPEN goal → high/open_goal đúng; 20 node → medium/many_nodes; deterministic 2 lần

### YC-7 — Execution Planner (builder — `execution_planner.py`)
- `build(tasks: list[TaskSpec], goal: GoalAnalysis, settings: PlanningSettings) -> ExecutionPlan`:
  1. **Known workflow path**: `goal.matched_workflow` → lấy `WorkflowDefinition` từ library → convert nodes (`WorkflowNode` → `PlanNode`: id/type/name/agent/capabilities/depends_on/timeout_s/**retries — C2-06: `node.retries if not None else definition.retries`**; `WorkflowNode.timeout_s=None` → dùng `definition.timeout_s`) + `required_permissions = definition.permissions` + `required_resources = definition.resources` — **0 LLM**
  2. **Template/rule path**: `TaskSpec` → `PlanNode` (id/type/name/agent/capabilities/depends_on/timeout_s/retries)
  3. Điền plan-level: **`id = f"plan:{source}:{intent}"` deterministic; `request_ref = request.text[:200]`; `created_at = ""` (v1 — deterministic, C2-01)**; `required_permissions` từ union task agent cần (mapping deterministic: coder→[filesystem], doctor→[filesystem], general→[]) — hoặc rỗng nếu không map được; `required_resources` từ settings (max_tokens) — chỉ metadata, không chiếm resource; `estimated_cost`: 0.0 khi không có LLM node (offline — deterministic); `estimated_tokens = 2000 * #llm_node + 200 * #khác`; **planner tạo `DRAFT`, validator pass → engine set `READY`**
  4. Node count > `settings.max_nodes` → raise `PlanningError("too many nodes")` (trước khi build — bảo vệ)
- **Test**: known workflow (WorkflowDefinition 3 node) → plan nodes/depends_on/permissions/resources map đúng, `estimated_tokens` tính đúng; template path → plan 6 node §12; status DRAFT trước validate; > max_nodes → PlanningError

### YC-8 — Plan Validator — INV-014 (8 hạng mục — `validation.py`)
- `validate(plan: ExecutionPlan, ctx: ValidationContext) -> PlanValidationReport` — `ValidationContext(capabilities: CapabilityRegistry, policy: PolicyService | None, resources: ResourcesSettings | None, settings: PlanningSettings)`:
  1. **Contract**: `ExecutionPlan.model_validate(plan.model_dump())` (extra forbid) — lỗi pydantic → fatal `contract` (node_id = id node lỗi nếu xác định được, ngược lại "")
  2. **Capability**: mọi `node.capabilities ⊆ capabilities.list()` — unknown → fatal `capability` (node_id cụ thể)
  3. **Permission**: mọi `plan.required_permissions ∈ {s.value for s in PermissionScope}` — ngoài → fatal `permission`; scope hợp lệ → tiếp mục Policy
  4. **Policy (C1-02 — khớp PolicyService thật)**: `policy.evaluate(PolicyRequest(scopes=[PermissionScope(s) for s in plan.required_permissions], tokens=plan.estimated_tokens or None))`:
     - `decision.requires_approval == True` → **non-fatal** issue `policy` + `needs_approval=True` (Human Approval — PLAN tầng 4; service thật trả `approved=True` ở nhánh này — ghi chú)
     - `decision.approved == False` và `requires_approval == False` (deny/token budget) → **fatal** `policy` (message = decision.reason)
     - `policy is None` (chưa inject) → non-fatal issue `policy` "policy service unavailable" (wiring phải inject — giả định §7)
  4b. **Resolve capability lạ (C2-11 v2)**: engine raise sớm khi resolver gặp capability lạ — **test YC-5 assert trên return resolver ĐƠN VỊ (RiskReport trả về), không qua engine**
  5. **Dependency**: mọi `depends_on` ∈ node ids + không self-dep — sai → fatal `dependency` (node_id)
  6. **Resource**: `plan.estimated_tokens` (nếu > 0) ≤ `resources.max_tokens` (nếu set) — vượt → fatal `resource`; `resources is None` → bỏ qua (non-fatal note không cần)
  7. **Cycle**: `validate_dag(plan.nodes)` — `ValueError` → fatal `cycle` (node_id = node báo cycle) — **VD `T1→T2→T3→T1` → fatal cycle → reject** (đúng PLAN §14)
  8. **Timeout**: mọi node `min_timeout_s ≤ node.timeout_s ≤ max_timeout_s` (`PlanningSettings`; PlanNode đã chặn âm ở contract) — vi phạm → fatal `timeout`
  - Issues sort theo (rule, node_id) — deterministic; report.valid = không fatal
- **Engine gate (C1-03 — gán trách nhiệm bắt ValidationError từ build)**: `ExecutionPlanner.build` (hoặc engine wrap build) `try/except ValidationError` (từ ExecutionPlan._validate_plan: unique id/unknown depends_on/cycle) → parse node_id từ message (regex) → `raise PlanningError(msg, report)` với issue `cycle`/`dependency`/`contract`; **validator mục 1/5/7 (contract/dependency/cycle) giữ defense-in-depth — test qua `model_construct()` (bypass model validator) để inject plan lỗi**; sau build, `validate()` bắt buộc chạy (INV-014 — enforcement §5.1); fatal → `raise PlanningError(msg, report)`; valid → plan.status = `READY`, trả `PlanningResult(validation=report, needs_approval=...)`
- **Test (behavioral — PLAN §14/§23)**: 8 hạng mục mỗi cái 1 test: contract lỗi (node thừa field → fatal contract); capability unknown → fatal; permission scope lạ → fatal; policy deny scope → fatal + reason; policy requires_approval → non-fatal + needs_approval=True; dependency self/unknown → fatal; resource estimated_tokens > budget → fatal; **cycle T1→T2→T3→T1 → `PlanningError` với `report.issues` có issue rule=cycle, fatal=True**; timeout 0.5s (< min) → fatal; timeout 7200 (> max) → fatal; plan hợp lệ → report.valid=True + plan.status == READY; report issues sorted deterministic

### YC-9 — Offline-first ladder + đếm LLM calls (engine — `engine.py`)
- `PlanningEngine.plan(request) -> PlanningResult` — pipeline điều phối:
  1. `GoalAnalyzer.analyze` → `goal`
  2. `goal.source == WORKFLOW` → skip decomposer/analyzer/resolver/risk (compile trực tiếp — §YC-7.1) → validate → trả `PlanningResult(source=WORKFLOW, llm_calls=0)`
  3. `TaskDecomposer.decompose` → tasks rỗng (OPEN, không template) → **LLM path** §YC-10; tasks không rỗng → tiếp
  4. `DependencyAnalyzer.analyze` → `CapabilityResolver.resolve` (issue fatal → raise sớm với report) → `RiskAnalyzer.analyze` → `ExecutionPlanner.build` → `PlanValidator.validate` → gate
  5. `self._llm_calls` (cumulative counter — **semantics: số lần pipeline phụ thuộc LLM; tăng NGAY SAU gọi `planner.plan()` KỂ CẢ error path — C2-08**) + `reset_calls()` + `last_result` (thread-safe, lock pattern `ModelRouter`)
  6. `latency_ms` đo wall-clock (monotonic) — return value cho observability (M5 DoD), không emit event
- `source`/`llm_calls` theo bậc PLAN §13: workflow → (WORKFLOW, 0); template → (TEMPLATE, 0); rule → (RULE, 0); LLM → (LLM, 1)
- **Test (PLAN §23 — offline-first)**: library có "crud-generator" + text "Create CRUD API" → `llm_calls == 0`, `source == WORKFLOW`, `planner.calls == 0` (mock model không bị gọi); text template "Review module authentication và viết test" → (TEMPLATE, 0); "check status" → (RULE, 0); text OPEN → (LLM, ≥1) + plan vẫn là DAG hợp lệ; `engine.llm_calls` cumulative + `reset_calls()`; 2 lần chạy cùng input (không LLM path) → `PlanningResult.model_dump()` y hệt (deterministic — PLAN §23)

### YC-10 — LLM planning fallback (qua Planner cũ — additive)
- `engine._plan_with_llm(request, goal) -> GoalAnalysis + TaskSpec list`:
  1. Chọn model: `router` injected → `router.select(RouteRequest(policy=request.policy))` (deterministic, 0 LLM — TASK-025) → **`model = registry.get(router.last_decision.model_name)` (C1-01 — registry inject untyped; `model_name is None` → `raise PlanningError("no model available")`; **wrap `RouterError/ModelError` → `PlanningError("no model available: ...")` — C2-08 v2**)**; `router is None` → dùng `model` inject; **`model is None and router is None` → `raise PlanningError("no model available")` (C2-10 v2)**
  2. `planner.plan(request.text, model, library)` → `PlanResult` (Planner CŨ — không đổi API)
  3. `plan.error` → `raise PlanningError(f"llm planning failed: {reasoning}")`
  4. Thành công → **decomposition vẫn deterministic** (PLAN §13 tinh thần): `PlanResult.intent` + `workflow_names[0]` → map intent → template/rule skeleton (vd intent "coding" → coding template); **normalize intent (C2-05 v2): `medical → doctor`, intent ngoài bảng → `chat`**; intent chat + không workflow → plan 1 node `chat` (type LLM) — KHÔNG để LLM sinh DAG (v1: LLM chỉ chọn intent/workflow — giả định §7); **generic fallback cố định: intent không template → RULE skeleton `[T1 <intent> (type=LLM), T2 Report (type=TASK, depends_on=[T1])]` (2 node — C2-05 v2)**; **workflow_names[0] không tồn tại trong library → bỏ qua, map theo intent (C2-09 v2); tồn tại → source=LLM, llm_calls=1, compile từ workflow definition**
  5. `self._llm_calls += 1` **sau khi gọi planner.plan (kể cả error path — C2-08)**; source = LLM
- `planner is None` + goal OPEN → `raise PlanningError("llm planning unavailable")` (không trả plan rỗng silently)
- **Test**: planner stub trả intent "coding" → plan node coding template (3 node), llm_calls == 1; PlanResult error → PlanningError (llm_calls == 1 — C2-08); planner None + OPEN → PlanningError; router inject (fake — RouteDecision model_name "mock") → `router.select` được gọi đúng 1 lần, planner nhận model từ `registry.get`; `engine.llm_calls` tăng đúng; planner.calls == 1 khi model ok (2 counter song song — semantics khác nhau)

### YC-11 — Wiring + config (additive)
- `config.py` MOD:
  ```python
  class PlanningSettings(BaseModel):
      model_config = ConfigDict(extra="forbid")
      max_nodes: int = 32
      default_timeout_s: float = 300.0
      min_timeout_s: float = 1.0
      max_timeout_s: float = 3600.0
      warn_token_threshold: int = 20_000
  class Settings(BaseModel):
      ...
      planning: PlanningSettings = PlanningSettings()
  ```
- `config.yaml` MOD (additive block):
  ```yaml
  planning:
    max_nodes: 32
    default_timeout_s: 300.0
    min_timeout_s: 1.0
    max_timeout_s: 3600.0
    warn_token_threshold: 20000
  ```
- `runtime_kernel.create()` — additive block CUỐI (sau model router, trước return) — **MỘT block duy nhất (R2-1 review — block trùng đã gộp)**:
  ```python
  # Planning engine (TASK-026): offline-first pipeline (workflow → template → rule → LLM).
  from ..capabilities.registry import CapabilityRegistry
  from ..orchestrator.planner import Planner
  from ..orchestrator.planning import PlanningEngine
  from ..workflow.library import WorkflowLibrary

  planning_engine = PlanningEngine(
      library=WorkflowLibrary(),
      capabilities=CapabilityRegistry(),
      policy=PolicyService(bus),            # cùng default policy — không side effect
      resources=resources_settings,
      planner=Planner(),
      router=model_router,                  # untyped inject (INV-005 rule A — orchestrator không import models)
      model=None,                           # None → router quyết định khi LLM path (R2-1)
      registry=model_registry,              # BẮT BUỘC (C2-01 v2): LLM path `model = registry.get(...)`
      settings=settings.planning,           # đã là PlanningSettings — không dựng lại (R2-1)
  )
  container.register_instance(PlanningEngine, planning_engine)
  ```
      settings=settings.planning,
  )
  container.register_instance(PlanningEngine, planning_engine)
  ```
  - KHÔNG sửa block đăng ký services (123–129) — additive; `WorkflowLibrary()`/`CapabilityRegistry()` rỗng (known workflow/capability đăng ký qua SystemCatalog/orchestrator wiring ở task sau — giả định §7)
  - Note: nếu container đã có `WorkflowLibrary`/`CapabilityRegistry` (future wiring) → resolve thay vì dựng mới (implementation quyết định resolve-or-create — ghi chú)
- **Test** (integration): `RuntimeKernel.create().container.resolve(PlanningEngine)` trả instance; `plan("check status")` chạy được offline → `source == RULE`, `llm_calls == 0`, plan.plan.status == READY; Settings parse config.yaml block planning (pattern test_config); env override `AIOS_PLANNING__MAX_NODES=16` (pydantic-settings — scalar; ghi chú dict nested như TASK-025 C2-03)

### YC-12 — Integration end-to-end (engine ↔ library ↔ capabilities ↔ policy ↔ router)
- Dựng đầy đủ: WorkflowLibrary (1 workflow "crud-generator" 3 node), CapabilityRegistry (4 capability review + tool bind), PolicyService (default), ResourcesSettings(max_tokens=5000), Planner + model mock
- **Test**: (a) "Create CRUD API" → source WORKFLOW, plan 3 node map đúng definition, `llm_calls == 0`, `mock.calls == 0`; (b) "Review module authentication và viết test" → 6 node §12, capabilities resolve đúng, plan READY; (c) workflow có dependency cycle (definition cycle — validate_dag chặn ở WorkflowDefinition rồi, dùng template override: template viết sai depends_on T3→T1) → PlanningError cycle; (d) OPEN goal + planner stub → LLM path plan hợp lệ; (e) policy deny filesystem — dựng `PolicyService(bus, Policy(deny_scopes=["filesystem"]))` (C2-07 — không có set_policy API) → fatal policy issue reason đúng; (f) cùng input chạy 2 lần → model_dump y hệt (deterministic)

## 5. Yêu cầu kiến trúc

### 5.1 INV-014 — Plan Validation (behavioral + AST enforcement)
Bản chất: *"Execution Plan phải validate trước execution"* — plan ra khỏi Planning Engine phải đã qua validator 8 hạng mục:

1. **Behavioral** (`test_inv014_plan_validation_gate` trong `test_planning_engine.py`):
   - Mọi `PlanningEngine.plan()` trả `PlanningResult.plan` đều có `validation.valid == True` và `plan.status == READY` (tham số hóa: workflow/template/rule/llm path)
   - Cycle `T1→T2→T3→T1` → `PlanningError` (không bao giờ trả plan vòng)
   - 8 hạng mục mỗi cái có test riêng (§YC-8)
2. **AST hỗ trợ** (`test_architecture.py`):
   - `test_inv014_planning_gate` — `engine.py` PHẢI chứa call-site `self._validator.validate(` (pattern `test_inv007_policy_first_hard`) — plan không thể thoát validator mà không sửa source
   - `test_inv014_runtime_no_planning` — `kernel/services/execution.py` (và `scheduler.py`, `state.py`, `resource.py`) KHÔNG import `aios_core.orchestrator.planning` — Runtime không tự plan (chiều intelligence → runtime, không đảo) — `dir_imports(AIOS / "kernel" / "services", ["aios_core.orchestrator.planning"]) == []`
   - `test_inv014_validation_has_8_rules` — `validation.py` source chứa đủ 8 tên hạng mục (`ValidationRule.CONTRACT`...`TIMEOUT` tham chiếu qua source text, pattern `test_inv009_event_driven`) — chống regression bỏ sót hạng mục

### 5.2 Allow-list import `orchestrator/planning/` (test mới `test_inv_planning_import_allowlist` — **loop từng file trong planning/, pattern `test_inv_tools_import_allowlist` (C2-12 v2: `collect_imports` nhận 1 module)**)
- **Ghi chú (C2-02 v2)**: INV-005 rule A KHÔNG đệ quy (`dir_imports` dùng `glob("*.py")`) — KHÔNG quét `orchestrator/planning/`; enforcement = allow-list test MỚI này (không sửa dir_imports trong 026)
- **Ghi chú import depth (C2-07 v2)**: planning/ nằm `orchestrator/planning/` — import package khác dùng 3 dots: `from ...capabilities.registry import CapabilityRegistry` (không phải 2 dots)
- **aios_core allowed**: `aios_core.kernel.execution_plan` (PlanNode/ExecutionPlan/PlanNodeType — QUYẾT ĐỊNH tái dùng §5.6), `aios_core.kernel.dag` (validate_dag), `aios_core.kernel.services.permissions` (PermissionScope), `aios_core.kernel.services.policy` (PolicyService/PolicyRequest/PolicyDecision), `aios_core.workflow.library` (WorkflowLibrary), `aios_core.workflow.definition` (WorkflowDefinition), `aios_core.capabilities.registry` (CapabilityRegistry), `aios_core.orchestrator.planner` (Planner/PlanResult — LLM fallback), `aios_core.orchestrator.errors` (PlanningError) + intra-package `aios_core.orchestrator.planning.*` (loại trừ trong scan)
- **CẤM (kể cả TYPE_CHECKING — bài học TASK-023 C2-01)**: `aios_core.models.*` (INV-005 rule A — model/router inject instance; rule B planner allow-list tự chặn `planning → models`), `aios_core.memory`, `aios_core.context`, `aios_core.knowledge`, `aios_core.tools`, `aios_core.agents`, `aios_core.contracts` (INV-006), **`aios_core.kernel.services.{execution,state,resource,scheduler}`** (Runtime chỉ consume plan; resource check qua `ResourcesSettings` — không chiếm resource), `aios_core.kernel.runtime_kernel` (cycle), `aios_core.orchestrator.orchestrator` (v1 không đổi), `aios_core.orchestrator.goals` (GoalManager subsystem riêng — giả định §7)
- **external allowed**: `pydantic`, `typing`, `enum`, `dataclasses`, `re`, `time`, `threading` (lock), `abc` (nếu dùng abstract analyzer), **`logging` (R2-2 — chuẩn logging của repo)**
- **aios_core allowed thêm (R2-2)**: `aios_core.logging` (get_logger — pattern kernel/services)
- Scan toàn dir `orchestrator/planning/*.py` qua `collect_imports`, loại trừ `startswith("aios_core.orchestrator.planning")`
- **INV-005 rule A không cần sửa**: rule A cấm `orchestrator → aios_core.models` — planning/ nằm trong orchestrator/ nên tự bị quét; planner.py exempt giữ nguyên (không thêm exemption cho planning — planning không import models)

### 5.3 Deterministic first (PLAN §13, §23)
- Goal Analyzer / Task Decomposer / Dependency Analyzer / Capability Resolver / Risk Analyzer / Execution Planner / Validator: **thuần rule, không LLM, không random, không network** (không gọi `model.is_available()` — bài học TASK-025 §2 Out)
- LLM planning chỉ là fallback cuối (bậc 4); decomposition LUÔN deterministic kể cả sau LLM (LLM chỉ chọn intent/workflow — §YC-10)
- Tie-break đầy đủ: `RiskReport.items` sorted (level, kind); `PlanValidationReport.issues` sorted (rule, node_id); node id `T<n>` theo thứ tự skeleton; cùng input + cùng registry → `model_dump()` y hệt (test)
- `llm_calls` semantics tường minh: số lần pipeline phụ thuộc LLM (gọi `planner.plan`) — KHÁC `Planner.calls` (đếm `model.chat` thật); 2 counter song song, test phủ cả 2

### 5.4 No God Object (PLAN §11 — 7 bước + validator; pattern TASK-025 §5.4)
- Dependency DAG (mỗi module 1 trách nhiệm, chiều đi xuống):
```
contracts.py  templates.py              (leaf — không import aios khác ngoài kernel.execution_plan cho PlanNodeType/TaskSpec)
   ↑               ↑
goal_analyzer.py ──→ {contracts, workflow.library}          # intent/complexity/workflow match
task_decomposer.py → {contracts, templates}                  # skeleton → TaskSpec (3 đường, không LLM)
dependency_analyzer.py → {contracts, kernel.dag}             # topo order + verify
capability_resolver.py → {contracts, capabilities.registry}  # map + risk unknown
risk_analyzer.py → contracts                                  # thuần hàm
execution_planner.py → {contracts, kernel.execution_plan, workflow.definition}  # build ExecutionPlan
validation.py → {contracts, kernel.execution_plan, kernel.dag,
                 kernel.services.permissions, kernel.services.policy}            # 8 hạng mục INV-014
engine.py → 6 analyzer + validation + {orchestrator.planner} # CHỈ điều phối + LLM fallback
```
- **Arch assert `test_inv014_no_god_object` — scan chuỗi CỤ THỂ (C2-04 v2, không phụ thuộc diễn giải)**: (a) `engine.py` import ĐỦ 7 module (GoalAnalyzer, TaskDecomposer, DependencyAnalyzer, CapabilityResolver, RiskAnalyzer, ExecutionPlanner, PlanValidator — qua `collect_imports`); (b) analyzer/validator KHÔNG import `engine` (không đảo chiều); (c1) `goal_analyzer.py` không chứa `decompose(`; (c2) `goal_analyzer.py` không chứa `TASK_TEMPLATES`; (c3) `task_decomposer.py` không chứa chuỗi keyword-intent mapping (regex `"review\|analyze\|audit"`-style — bảng keyword chỉ ở goal_analyzer); (c4) `engine.py` không chứa `ValidationRule.`; (c5) `validation.py` không chứa `decompose(`; (c6) `engine.py` không chứa `def analyze(` (logic analyzer nằm trong module analyzer)

### 5.5 Additive only
- `git diff` sau implement: `kernel/execution_plan.py`, `kernel/dag.py`, `orchestrator/planner.py`, `orchestrator/orchestrator.py`, `orchestrator/workflow_matcher.py`, `kernel/services/execution.py`, `workflow/*`, `capabilities/*`, `models/*` **không đổi**
- MOD (chỉ THÊM, không đổi hành vi cũ): `orchestrator/errors.py` (thêm `PlanningError`), `config.py` (thêm `PlanningSettings` + field `planning`), `config.yaml` (block planning), `runtime_kernel.py` (block wiring cuối), `tests/*` (additive)
- Planner/PlannerStub API cũ hoạt động y hệt (test cũ pass không sửa)

### 5.6 Vị trí package + quan hệ ExecutionPlan (quyết định mở — cho critic phản biện)
- **Đề xuất: subpackage `aios_core/orchestrator/planning/` (11 file)** — KHÔNG đặt top-level `planning/`, KHÔNG đơn file `planning.py`:
  1. Planning = Control Plane (orchestration) — PLAN phân tầng; planner.py đã ở `orchestrator/` → cùng chỗ, gọi `Planner` trực tiếp không import ngược
  2. INV-005 rule A tự bao phủ: planning/ nằm trong orchestrator/ → cấm models tự nhiên, không cần sửa invariant/rule (top-level planning/ cần allow-list riêng + exemption phức tạp hơn)
  3. Pattern M5 đồng nhất: memory/ (023), context/ (024), models/router/ (025), orchestrator/planning/ (026) — mỗi năng lực 1 subpackage + allow-list riêng + contracts domain-local (INV-006)
  4. God Object prevention: 7 bước PLAN §11 cần ≥ 7 module — đơn file `planning.py` (~600 dòng) = God Object
- **Đề xuất: TÁI DÙNG `ExecutionPlan`/`PlanNode` (kernel/execution_plan.py) — KHÔNG tạo contract v2**:
  1. Additive-only bắt buộc (Out scope): tạo `PlanV2` song song = 2 contract phải đồng bộ mãi — vi phạm "không tạo hệ thống song song" (PLAN M5)
  2. ExecutionPlan đã có đủ: DAG validate (model_validator → validate_dag: unique/unknown-dep/cycle), depends_on, retries, timeout_s, capabilities, agent, required_permissions, required_resources, estimated_cost/tokens, status — đúng contract trung gian Planning (026) → Graph (027) → Runtime (ExecutionService đã consume)
  3. INV-014 KHÔNG đòi sửa ExecutionPlan: contract-level validate (structural) đã có trong model; 8 hạng mục còn lại (capability/permission/policy/resource/timeout/cycle-report) là **tầng PlanValidator mới** (ngoài model, không đổi model) — phân tách rõ: model validate = syntax, PlanValidator = semantics
  4. Lý do KHÔNG tạo v2: nếu cần thêm field (vd plan-level timeout) → đề xuất additive field ở 027 khi Execution Graph cần — KHÔNG làm trong 026
- Phương án thay thế: (a) top-level `aios_core/planning/` — tách domain nhưng phá pattern + allow-list mới; (b) contract v2 `PlannedExecution` — bị loại (lý do trên); (c) Planning Engine đặt trong `kernel/` — sai phân tầng (kernel = runtime, planning = intelligence — PLAN §26 tách Intelligence/Runtime) — **loại**
- Critic được phép phản biện; nếu đổi → cập nhật allow-list + AST tương ứng

## 6. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — `PlanningRequest`/`GoalAnalysis`/`TaskSpec`/`RiskItem`/`RiskReport`/`PlanValidationIssue`/`PlanValidationReport`/`PlanningResult` pydantic `extra="forbid"`; `ValidationRule` đủ đúng 8 giá trị PLAN §14; `PlanSource`/`GoalComplexity` đủ 4/3 giá trị; `PlanningError` mang `report` (YC-1)
- [ ] **AC2**: **Task Decomposition VD §12 exact** — "Review module authentication và viết test" → đúng 6 node T1..T6 (Analyze → {vuln, missing tests} → Write tests → Run → Report) với dependency `T1→{T2,T3}→T4→T5→T6` (id, name, capabilities, depends_on kiểm tra exact); SIMPLE → 1 node; OPEN → rỗng (decomposer) (YC-3)
- [ ] **AC3**: **Plan Validation 8 hạng mục** — mỗi hạng mục 1 test behavioral: contract/capability/permission/policy/dependency/resource/cycle/timeout; **cycle `T1→T2→T3→T1` → `PlanningError`** với `report.issues` chứa `rule=cycle, fatal=True` (reject — PLAN §14); policy needs-approval → non-fatal + `needs_approval=True`; plan hợp lệ → `status == READY` + `validation.valid == True` (YC-8)
- [ ] **AC4**: **Offline-first** — known workflow → `source == WORKFLOW`, `llm_calls == 0`, `planner.calls == 0` (mock 0 lần gọi — PLAN §13, §23); template → `(TEMPLATE, 0)`; rule → `(RULE, 0)`; chỉ OPEN → `(LLM, 1)`; `engine.llm_calls` cumulative + `reset_calls()` (YC-9)
- [ ] **AC5**: **Deterministic** — cùng input + cùng registry chạy 2 lần → `PlanningResult.model_dump()` (trừ latency_ms) y hệt; không LLM path không gọi model (`mock.calls == 0`); reports/risks sorted deterministic (YC-2..YC-9)
- [ ] **AC6**: **INV-014 enforcement** — `test_inv014_plan_validation_gate` (mọi plan trả ra valid + READY, tham số hóa 4 source), `test_inv014_planning_gate` (engine.py có call-site `self._validator.validate(`), `test_inv014_runtime_no_planning` (kernel/services không import planning), `test_inv014_validation_has_8_rules` (validation.py tham chiếu đủ 8 rule) — đều pass (YC-8, §5.1)
- [ ] **AC7**: **Allow-list** — `test_inv_planning_import_allowlist` pass: planning/ chỉ import allow-list (execution_plan/dag/permissions/policy/workflow/capabilities/planner/errors/intra; CẤM models/memory/context/knowledge/tools/agents/contracts/runtime_kernel kể cả TYPE_CHECKING); INV-005 rule A + rule B cũ vẫn pass không sửa (§5.2)
- [ ] **AC8**: **No God Object** — `test_inv014_no_god_object` pass: engine import đủ 7 module; analyzer không import engine; scan chuỗi cụ thể (c1..c6 — C2-04 v2); engine không chứa `ValidationRule.` logic (§5.4)
- [ ] **AC9**: **Additive only** — `git diff`: execution_plan.py/dag.py/planner.py/orchestrator.py/workflow_matcher.py/execution.py/models/*/workflow/*/capabilities/* không đổi; MOD chỉ thêm (errors/config/config.yaml/runtime_kernel) (§5.5)
- [ ] **AC10**: **Wiring + test suite** — `RuntimeKernel.create().container.resolve(PlanningEngine)` chạy được offline; `plan("check status")` → RULE + READY; Settings parse block planning + env override `AIOS_PLANNING__MAX_NODES`; **full pytest pass (baseline 949 + test mới ≥ ~60)**, coverage ≥ 95% mục tiêu (hard ≥ 80%) (YC-11, YC-12)
- [ ] **AC11**: **Ranh giới TASK-027/028** — không tồn tại `GraphNode`/`GraphEdge`/`JoinPolicy`/`FailurePolicy`/`GraphState` trong diff (027); không sửa `ExecutionService`/`ResourceService`/`SchedulerService` (028); `plan.nodes` + `depends_on` + `required_*` đủ dữ liệu cho 027 convert (kiểm tra spec 027 consume: edge = depends_on) (YC-7, §2 Out)

## 7. Rủi ro & giả định

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Template planning (deterministic) cứng — không cover task mở | Ladder đầy đủ: template → rule → LLM fallback (PLAN §13); template registry mở rộng được (`register`); task không khớp → RULE/LLM, không bao giờ trả plan sai im lặng |
| LLM chỉ trả intent/workflow, không trả DAG → chất lượng plan v1 hạn chế | Quyết định tường minh (PLAN §13 tinh thần deterministic-first): decomposition luôn deterministic; khi cần LLM decomposition thật → task sau (sau 027/028) — ghi giả định, critic phản biện được |
| Validator phụ thuộc `PolicyService` (kernel/services) — orchestrator lần đầu import kernel.services | Chỉ import `permissions` + `policy` (allow-list §5.2 tường minh); `PolicyService.evaluate` deterministic (deny > approval > allow — không LLM); giả định: evaluate có thể emit event (observability) — không phải hành vi chặn; `policy=None` → non-fatal issue (wiring phải inject — test AC10 bắt) |
| `llm_calls` (engine) vs `Planner.calls` (chat thật) lệch nhau gây hiểu nhầm | Semantics tường minh trong spec + docstring: engine.llm_calls = số lần pipeline phụ thuộc LLM; planner.calls = số model.chat thật; test phủ cả 2 (model unavailable → engine=1, planner=0) |
| `WorkflowLibrary`/`CapabilityRegistry` rỗng trong runtime_kernel → known workflow path không dùng được qua container | Wiring rỗng là chấp nhận v1 (orchestrator v1 wiring riêng ở api/wiring.py — composition root khác); test integration dựng library/capability đầy đủ trực tiếp; SystemCatalog đăng ký vào library là task sau |
| AST đếm cả TYPE_CHECKING (bài học TASK-023 C2-01) | planning/ dùng import runtime bình thường cho dependency thật, KHÔNG TYPE_CHECKING; allow-list test comment rõ |
| Resource validation chỉ ước lượng (estimated_tokens) không đo thật | TASK-024 ContextOptimizer cung cấp token count thật — ghi nhận tích hợp sau; v1 deterministic ước lượng + chặn budget cứng (INV-014 resource) |
| `validate_dag` raise ValueError bị pydantic wrap (ExecutionPlan model_validator) — cycle đã chặn ở contract khi build | PlanValidator bắt ở 2 tầng: (a) build ra plan có cycle → pydantic raise → bắt → fatal issue `cycle` với node_id từ message (parser regex đơn giản); (b) re-validate lại qua `validate_dag` cho report chính xác — test cycle VD §14 phủ |
| `needs_approval=True` plan không chạy được qua ExecutionService v1 (R2-3 review — `execution.py _run` trả FAILED "approval required" khi `decision.requires_approval`, runtime đọc lại policy không đọc plan.needs_approval) | **Giả định sửa (R2-3)**: v1 `needs_approval` chỉ là metadata cho orchestrator v2 / TASK-027-028 (Human Approval); plan cần approval hiện không chạy qua ExecutionService v1 — KHÔNG sửa execution (đúng Out scope); test không kỳ vọng plan ASK execute được |

**Giả định**:
- Planning v1: LLM path chỉ dùng cho intent/workflow selection — decomposition deterministic (PLAN §13: "Planning KHÔNG nhất thiết dùng LLM" — đúng tinh thần, critic phản biện được)
- Node id luôn `T<n>` theo thứ tự skeleton (deterministic, dễ đọc log/observability)
- `ResourcesSettings.max_tokens` là budget plan-level (so với `estimated_tokens`); `None` = không chặn
- `PolicyService` mặc định (allow filesystem, deny khác): plan cần scope ngoài allow → `requires_approval=True` → non-fatal + `needs_approval` (Human Approval — PLAN Decision Pipeline tầng 4); execution vẫn chạy khi orchestrator quyết định approve (runtime không đổi)
- `PlanningEngine` không phải là thay thế `Orchestrator` v1 — v1 giữ nguyên; 026 là intelligence layer mới, 027/028 nối vào flow (PLAN §20, §26)
- Không tích hợp `orchestrator/goals/` (GoalManager — goal lifecycle/quản lý, khác Goal Analyzer — phân tích request); nối sau khi Execution Graph consume plan (027)
- `latency_ms` dùng monotonic clock, chỉ là số liệu trả về (không emit event — M5 DoD observability gắn ở task sau)

## 8. Expected artifacts

| File | Loại | Nội dung |
|------|------|----------|
| `backend/src/aios_core/orchestrator/planning/contracts.py` | NEW | `PlanSource`/`GoalComplexity`/`GoalAnalysis`/`TaskSpec`/`RiskItem`/`RiskReport`/`ValidationRule`/`PlanValidationIssue`/`PlanValidationReport`/`PlanningRequest`/`PlanningResult` (pydantic `extra="forbid"`) + `ValidationContext` (dataclass) |
| `backend/src/aios_core/orchestrator/planning/templates.py` | NEW | `StepSpec`/`TemplateSkeleton` + `TASK_TEMPLATES` (review VD §12 + test/coding/chat) + `register()` (leaf — chỉ import contracts) |
| `backend/src/aios_core/orchestrator/planning/goal_analyzer.py` | NEW | `GoalAnalyzer.analyze` — intent/target/complexity/workflow match (deterministic) |
| `backend/src/aios_core/orchestrator/planning/task_decomposer.py` | NEW | `TaskDecomposer.decompose` — template/rule/simple → `TaskSpec` (3 đường deterministic; OPEN → rỗng) |
| `backend/src/aios_core/orchestrator/planning/dependency_analyzer.py` | NEW | `DependencyAnalyzer.analyze` — verify dep + topo order (stable) |
| `backend/src/aios_core/orchestrator/planning/capability_resolver.py` | NEW | `CapabilityResolver.resolve` — map capability/agent + risk (deterministic) |
| `backend/src/aios_core/orchestrator/planning/risk_analyzer.py` | NEW | `RiskAnalyzer.analyze` — RiskReport sorted (thuần hàm) |
| `backend/src/aios_core/orchestrator/planning/execution_planner.py` | NEW | `ExecutionPlanner.build` — `TaskSpec`/`WorkflowDefinition` → `ExecutionPlan` (DRAFT) + estimate |
| `backend/src/aios_core/orchestrator/planning/validation.py` | NEW | `PlanValidator.validate` — 8 hạng mục INV-014 → `PlanValidationReport` |
| `backend/src/aios_core/orchestrator/planning/engine.py` | NEW | `PlanningEngine` — điều phối pipeline + ladder + LLM fallback (qua `Planner` cũ + router inject) + `llm_calls`/`last_result` + gate validator |
| `backend/src/aios_core/orchestrator/planning/__init__.py` | NEW | Re-export public API |
| `backend/src/aios_core/orchestrator/errors.py` | MOD | Thêm `PlanningError(OrchestratorError)` + `report` (additive) |
| `backend/src/aios_core/config.py` | MOD | `PlanningSettings` (`extra="forbid"`) + `Settings.planning` (additive) |
| `backend/config.yaml` | MOD | Block `planning` (defaults §YC-11) |
| `backend/src/aios_core/kernel/runtime_kernel.py` | MOD | Wiring block planning (cuối `create()`, additive) |
| `backend/tests/test_planning_engine.py` | NEW | Unit (contracts/analyzer/decomposer/dependency/capability/risk/planner/validator/ladder) + INV-014 behavioral + integration (library/capabilities/policy/router) |
| `backend/tests/test_architecture.py` | MOD | `test_inv_planning_import_allowlist` + `test_inv014_planning_gate` + `test_inv014_runtime_no_planning` + `test_inv014_validation_has_8_rules` + `test_inv014_no_god_object` |
| `backend/tests/test_runtime_kernel.py` | MOD | `test_planning_engine_wired` (additive, pattern `test_model_router_wired`) |
| `aios/progress/tasks/TASK-026/` | — | critique-1/2, tasks.md, review.md, test.md, evaluation.md (theo workflow gate) |

## 9. Ghi chú thiết kế (cho critic phản biện)

- **Tái dùng `ExecutionPlan` vs tạo contract v2**: spec chốt **tái dùng** (builder mở rộng — lý do §5.6). Critic cân nhắc: ExecutionPlan thiếu field plan-level timeout/resources cấu hình từ planning — có nên additive thêm field vào ExecutionPlan (đổi file) hay giữ nguyên + bỏ qua? Spec chọn giữ nguyên (027 có thể đề xuất additive khi cần graph)
- **Vị trí subpackage**: `orchestrator/planning/` vs top-level `planning/` — spec chọn trong orchestrator (INV-005 rule A tự bao phủ, gần Planner). Critic phản biện: top-level có lợi gì về tách domain không đáng trả giá allow-list mới?
- **LLM path chỉ intent/workflow, decomposition deterministic**: quyết định mạnh (PLAN §13 tinh thần). Critic: có nên cho LLM sinh DAG trực tiếp (prompt → parse nodes/deps) khi OPEN? Spec loại vì: parse không deterministic (lỗi format), vi phạm offline-first, v1 cần deterministic cho test — nhưng critic có thể đề xuất LLM-decomposition opt-in (flag) cho 027
- **Validator gọi `PolicyService` (kernel.services)**: orchestrator lần đầu import kernel.services — allow-list mới. Critic: có nên tách policy check thành callback inject (không import policy trực tiếp) để giữ orchestrator thuần? Spec chọn import trực tiếp (deterministic, đơn giản) — chấp nhận dependency mới
- **`llm_calls` semantics** (engine đếm lần gọi `planner.plan`, không dùng `planner.calls`): 2 counter có thể lệch (model unavailable). Critic: có nên thống nhất 1 nguồn (chỉ dùng `planner.calls` delta)? Spec giữ 2 counter vì semantics khác nhau — test phủ
- **`engine.llm_calls` cumulative + `last_result` mutable state**: cần cho observability (M5 DoD planning latency/llm) — pattern `ModelRouter.last_decision`. Critic: có nên trả stats trong return value thay vì state? Spec làm cả 2 (result chứa per-request, property cumulative)
- **Template review cứng 2 finding (T2 vuln, T3 missing tests)**: VD §12 deterministic nhưng không mở rộng theo findings thật. Critic: có nên cho template khai báo `branch` dynamic (findings từ input)? Spec v1 giữ cứng (deterministic tuyệt đối); dynamic branch để 027/028 (graph condition) — ghi giả định
- **Resource validation chỉ ước lượng tokens**: không gọi `ResourceService.acquire` (side effect) — critic: có nên pre-acquire resource khi validate (reserve) để chắc chắn runtime chạy được? Spec loại (validation phải pure; acquire là việc 028 Scheduler)
- **`WorkflowDefinition` → `ExecutionPlan` mapping trong ExecutionPlanner**: workflow/definition.py đã có validate DAG riêng (compile) — mapping 1-1 node; critic: có nên dùng `workflow/compiler.py` (MockCompiler) thay vì tự map? Spec chọn tự map (compiler sinh engine-run, không phải plan contract; 026 cần `ExecutionPlan` output — không trộn)
