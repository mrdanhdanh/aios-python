# TASK-008 — M1/P2a: Workflow Definition + Compilers + Workflow Library

## Mục tiêu
Xây Workflow Definition declarative độc lập engine (nodes/edges/retries/timeout/resources/permissions — theo PLAN "Workflow Definition (độc lập engine)"), compiler pluggable (v1: MockCompiler chạy qua ExecutionService TASK-005; langgraph để sau — chỉ cần thêm compiler), và WorkflowLibrary (đăng ký/tra cứu/tái sử dụng workflow — nền cho Orchestrator Workflow Matcher M2).

## Phạm vi
- **In** (thuộc `backend/src/aios_core/workflow/`):
  1. `definition.py` — `WorkflowDefinition` pydantic (**ConfigDict extra="forbid"**): `name, version (semver — reuse semver.parse_version), description, nodes: list[WorkflowNode], retries (default), timeout_s (default), resources (dict), permissions (list[str]), metadata (dict)`; **`edges` = read-only computed property (derive từ depends_on — KHÔNG stored field)**; `from_dict()` classmethod + `from_yaml(path)` (**không wrap FileNotFoundError/yaml.YAMLError — exception tự nhiên, CLI in lỗi**); **`WorkflowNode` (ConfigDict extra="forbid"): `id/type (PlanNodeType — str Enum, YAML "task"/"tool" tự convert)/name` required; `agent: str = ""`, `capabilities: list[str] = []`, `depends_on: list[str] = Field(default_factory=list)`, `timeout_s: float | None = None`, `retries: int | None = None` (None = không khai báo → fallthrough; **retries=0 → giữ 0 (engine: 1 attempt); timeout_s=0 → giữ 0 (engine: không timeout)**)**; validator: name strip + non-empty (whitespace-only reject), version semver, nodes unique ids, **unknown dep, nodes rỗng (min 1), retries/timeout_s âm (definition + node level) → fail-fast ở definition**, cycle detect (DAG), permissions ∈ known scopes (TASK-004)
  2. `dag.py` (ở `kernel/`) — extract helper `validate_dag(nodes)`: 3 logic check (unique id / unknown dep / cycle) — **duck-type (object có .id/.depends_on), raise ValueError (pydantic wrap thành ValidationError), giữ nguyên message từng chữ, thứ tự unique → unknown → cycle; KHÔNG move PlanNodeType; refactor thuần — 107 test TASK-003 không sửa**; ExecutionPlan validator gọi helper
  3. `compiler.py` — `WorkflowCompiler` ABC: `compile(definition) -> ExecutionPlan`, **`is_available() -> bool` default True**; `MockCompiler`: compile → plan (plan.id = `f"wf:{definition.name}"`, nodes 1:1 — merge: node override > definition default > PlanNode default với semantics None-vs-0, required_permissions = defn.permissions, required_resources = defn.resources, **created_at = now ISO, status = READY**); `LangGraphCompiler` — stub: `is_available() -> False`, compile → NotImplementedError (docstring M2)
  4. `library.py` — `WorkflowLibrary`: **`register(definition)` — canonical name = definition.name (KHÔNG tham số name riêng; chỉ nhận WorkflowDefinition instance)**; `get(name)` (unknown → WorkflowError), `list()` (**insertion order**), `search(query)` (**empty/whitespace → []; case-insensitive substring trên name+description; nhiều từ → match toàn chuỗi**), `promote(name)` (**usage+1 dưới lock; unknown → WorkflowError; chỉ tăng counter — M2 rank**), `usage(name)` (unknown → WorkflowError); thread-safe lock
  5. `cli.py` — `python -m aios_core.workflow.cli run workflow.yaml --simulate`: **`--simulate` BẮT BUỘC v1 (thiếu → argparse error + hint "M2 sẽ chạy thật")**; load YAML → compile (MockCompiler) → ExecutionService (fake runner echo node; **audit db trong tempfile.TemporaryDirectory — simulate không ghi file dài hạn**) → in kết quả (deliverable M1 `aiagent run workflow.yaml --simulate`)
  6. `errors.py` — `WorkflowError`
  7. `__init__.py` exports + re-export `workflow` ở `aios_core/__init__.py`
  8. Tests: test_definition, test_compiler, test_library, test_cli (4 file)
- **Out (không làm)**: LangGraph dep thật (M2), workflow version history (M2), fuzzy search/tokenize (M2), workflow persist DB (in-memory v1), console_scripts entry (v1 chạy qua `python -m`)

## Yêu cầu chi tiết
1. **WorkflowDefinition**: reuse `PlanNodeType` + DAG validation pattern từ execution_plan.py (KHÔNG duplicate cycle detect — extract helper dùng chung nếu cần); permissions validate ∈ PermissionScope values (reuse TASK-004)
2. **MockCompiler**: `compile(defn) -> ExecutionPlan` — plan.id = `wf:{name}`, request_ref = name, nodes map 1:1 (timeout/retries: node override > definition default > PlanNode default), required_permissions = defn.permissions, required_resources = defn.resources, estimated_cost/tokens = 0 (Planner M2 ước lượng)
3. **WorkflowLibrary**: register name trùng → overwrite + warning; search keyword case-insensitive trên name + description; promote/usage counter (start 0)
4. Mọi test tmp_path + offline; coverage ≥ 80%; test_import cập nhật

## Input / Output
- Input: TASK-003 (ExecutionPlan, PlanNodeType, DAG validation), TASK-004 (PermissionScope), TASK-005 (ExecutionService — compile output chạy được)
- Output: workflow/ package + tests + commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: WorkflowDefinition validate **9 case**: version semver; nodes unique; cycle (kể cả self); permissions scope lạ; name empty/whitespace; **depends_on unknown; nodes rỗng; retries/timeout_s âm (definition + node level); key lạ (extra forbid)** → ValidationError (có test)
- [ ] AC2: Merge defaults **4 case**: node override > definition default > PlanNode default; **node timeout_s=0 → giữ 0 (không bị definition default đè)** (có test)
- [ ] AC3: MockCompiler.compile: plan.id = "wf:{definition.name}", nodes 1:1, permissions/resources map đúng, **status=READY, created_at non-empty** (có test)
- [ ] AC4: Compile output chạy qua ExecutionService end-to-end (**permissions rỗng hoặc ["filesystem"] — tránh policy pre-check FAILED "approval required"**; fake runner) (có test)
- [ ] AC5: LangGraphCompiler.is_available() = False; compile → NotImplementedError (có test)
- [ ] AC6: Library: register/get/list (**insertion order**); unknown get/promote/usage → WorkflowError; search (**empty → [], substring case-insensitive, multi-word toàn chuỗi**); promote tăng usage; **thread-safe (2 thread register/search/promote)** (có test)
- [ ] AC7: pytest pass + coverage ≥ 80%; test_import: `from aios_core.workflow import WorkflowDefinition, WorkflowNode, WorkflowCompiler, MockCompiler, LangGraphCompiler, WorkflowLibrary, WorkflowError` pass; **107 test TASK-003 vẫn pass sau refactor dag helper (không sửa test nào)**
- [ ] AC8: Mọi test offline — git sạch
- [ ] AC9: CLI: test gọi `main()` trực tiếp + monkeypatch sys.argv (**offline deterministic — subprocess fail vì src layout chưa cài**): `run <yaml> --simulate` → load + compile + chạy (fake runner) + in COMPLETED; **thiếu --simulate → argparse error** (có test)
- [ ] AC10: `edges` property trả đúng tập cạnh theo depends_on; from_dict/from_yaml roundtrip (có test)

## Phụ thuộc
- TASK-003 (ExecutionPlan, DAG), TASK-004 (PermissionScope), TASK-005 (ExecutionService)
- Không dep mới

## Rủi ro
- R1: Duplicate DAG validation → extract helper từ execution_plan.py (module `kernel/dag.py` — cả 2 dùng)
- R2: LangGraph stub có thể bị hiểu là "phải cài" → is_available=False rõ ràng + docstring
- R3: WorkflowLibrary search keyword đơn giản → M2 nâng cấp (ghi chú)
