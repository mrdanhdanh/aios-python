# TASK-027 — Execution Graph (M5-P10, Phase 3)

**Metadata**: TASK-027 | M5/P10 | 2026-08-15 | v3 (critique-1 + critique-2 resolved) | AIOS Orchestrator
**Module đích**: `backend/src/aios_core/kernel/graph/` (subpackage mới) + `config.py`/`config.yaml` (MOD additive: block `graph`) + `kernel/runtime_kernel.py` (MOD additive: wiring cuối `create()`) + `tests/` (NEW `test_execution_graph.py` + MOD `test_architecture.py` + MOD `test_config.py` + MOD `test_runtime_kernel.py`)

## 1. Mục tiêu

Xây **Execution Graph** — nâng ExecutionService khỏi linear (Node1→2→3) thành **DAG execution** (PLAN §15):

```
        A
      /   \
     B     C
      \   /
        D
```

- **Graph Contract** (PLAN §16): `ExecutionGraph · GraphNode · GraphEdge · Dependency · Condition · JoinPolicy · FailurePolicy` — pydantic `extra="forbid"`. VD `nodes [analyze, test_backend, test_frontend, report]` + edges `analyze→{test_backend,test_frontend}→report`.
- **Graph State** (PLAN §17): **8 trạng thái** `PENDING · READY · RUNNING · SUCCEEDED · FAILED · SKIPPED · CANCELLED · BLOCKED` — foundation cho parallel execution (TASK-028).
- **Convert** từ TASK-026 output: `ExecutionPlan → ExecutionGraph` (nodes + `depends_on` → `GraphNode` + `Dependency`; join policy mặc định ALL; failure policy mặc định FAIL_FAST — cấu hình).
- **Topological traversal deterministic**: READY = dependencies SUCCEEDED (join ALL) hoặc ≥1 (ANY); SKIPPED nếu dep FAILED + failure policy; BLOCKED nếu dep CANCELLED/BLOCKED hoặc FAIL_FAST dừng graph.
- **INV-015 Graph Acyclicity**: graph không circular dependency — validate tại build (`validate_dag`) + enforcement test (behavioral + AST).
- **Runner injectable, KHÔNG sửa ExecutionService** (additive only): `GraphExecutor` chạy node qua `Callable[[GraphNode, dict], Any]` — TASK-028 sẽ nối real execution/resource vào chính injection point này.
- TASK-027 trả lời câu hỏi M5 *"Các bước phụ thuộc nhau thế nào?"* (đầu vào của 028 *"Task nào chạy song song?"* — 028 dùng graph state để schedule).

## 2. Phạm vi

**In**:
- `kernel/graph/` — NEW subpackage: `contracts.py`, `errors.py`, `state_machine.py`, `converter.py`, `executor.py`, `__init__.py`
- `config.py` — MOD (additive): `GraphSettings` (pydantic `extra="forbid"`) + `Settings.graph: GraphSettings = GraphSettings()`
- `config.yaml` — MOD (additive): block `graph` (defaults)
- `kernel/runtime_kernel.py` — MOD (additive): wiring block `register_instance(GraphExecutor, ...)` (CUỐI `create()` — sau block đăng ký services)
- `tests/test_execution_graph.py` — NEW: unit (contracts/state machine/converter/executor) + integration (fake runner + runtime_kernel) + INV-015 behavioral
- `tests/test_architecture.py` — MOD: `test_inv_graph_import_allowlist` + `test_inv015_graph_acyclicity_gate` + `test_inv015_graph_no_god_object` + `test_inv015_planning_no_graph` (pattern TASK-026 §5.1)
- `tests/test_config.py` — MOD (additive): Settings parse block `graph` + env override
- `tests/test_runtime_kernel.py` — MOD (additive): `test_graph_executor_wired` (pattern `test_model_router_wired`)

**Out (không làm — tránh scope creep)**:
- **KHÔNG sửa `ExecutionService`** (kernel/services/execution.py) — graph node chạy qua **runner injectable** (quyết định §5.6); ExecutionService giữ nguyên cho luồng cũ; KHÔNG làm "DAG-mode" bên trong ExecutionService
- **KHÔNG làm Parallel Scheduler** — TASK-028 (PLAN §18–19): 027 cung cấp graph state + readiness + max_parallel cơ bản (dependency-level); 028 dùng graph state để schedule (resource/thời điểm); `ResourceService`/`SchedulerService` KHÔNG sửa
- **KHÔNG sửa `StateService`** (kernel/services/state.py) — nó là generic store, schema do caller định nghĩa; graph state ghi vào **store hiện có** (schema mới `{graph, nodes, results, ...}`), zero MOD (quyết định §5.6); mọi method mới (vd `list_ready`) đề xuất ở 028
- **KHÔNG sửa `ExecutionPlan`/`PlanNode`/`dag.py`** — tái dùng (convert không đổi contract nguồn)
- **KHÔNG làm condition evaluation** — `Condition` chỉ là contract (PLAN §16 forward-compat); graph có edge `condition` non-None → **GraphExecutor từ chối execute (fail loud, không silent)**; evaluation = task sau
- **KHÔNG làm timeout enforcement** — `GraphNode.timeout_s` chỉ validate ≥ 0; thực thi timeout khi 028 nối real runner/ExecutionService (thread leak không thể kill — giả định §7)
- **KHÔNG làm graph resume/snapshot-restore** — state có persist (cho 028/observability) nhưng `resume()` là task sau (ExecutionService có resume riêng — không đụng)
- **KHÔNG emit event mới** (EventType giữ nguyên; GraphExecutor không emit event v1) — observability "graph execution time + parallelism" (M5 DoD §25) nằm trong `GraphResult` (return value) + StateService store (giống quyết định TASK-026 `latency_ms`)
- **KHÔNG import `aios_core.orchestrator.*`** trong `kernel/graph/` (kể cả TYPE_CHECKING — bài học TASK-023 C2-01): chiều intelligence → runtime không đảo; allow-list §5.2
- **KHÔNG làm**: async runner, multi-execution orchestration, dynamic graph mutation lúc chạy, LLM/random trong scheduling (deterministic tuyệt đối)

## 3. Input / Output

- **Input**:
  - `ExecutionPlan` (TASK-026 output — `plan.nodes` list `PlanNode`: `id/type/name/agent/capabilities/depends_on/timeout_s/retries` + `plan.required_permissions/required_resources/estimated_cost/estimated_tokens/request_ref`) — nguồn convert
  - `StateService` (inject — store graph state; dùng **cùng instance** với ExecutionService qua container)
  - `GraphSettings` (config: `max_parallel`, `default_failure_policy`)
  - Runner: `GraphNodeRunner = Callable[[GraphNode, dict[str, Any]], Any]` — inject tại `execute()`
- **Output**:
  - `plan_to_graph(plan, *, failure_policy=FAIL_FAST) -> ExecutionGraph` — convert deterministic
  - `GraphExecutor.execute(graph, runner, execution_id=None) -> GraphResult`:
    - `status: GraphRunStatus` (`SUCCEEDED|FAILED|CANCELLED`), `execution_id`, `node_statuses: dict[node_id, GraphNodeStatus]` (8 trạng thái), `node_results: dict[node_id, Any]`, `execution_order: list[str]` (thứ tự START — deterministic), `latency_ms: int` (graph execution time — PLAN §25), `max_concurrent_running: int` (parallelism — PLAN §25), `failure_policy`, `reason: str`
  - Graph state persist vào `StateService` (key = execution_id): `{graph: dict, nodes: {id: status}, results: {id: result}, started_at, execution_order, metrics: {latency_ms, max_concurrent_running}}` — TASK-028 đọc từ đây
- `GraphResult` ghi chú (C2-12): `set_state` lưu REFERENCE — result là object sống; `get_state` deepcopy, fallback repr cho object không copy được (hành vi StateService sẵn có); **028 nên đọc result qua GraphResult, state chỉ cho status/metrics**; `started_at` = ISO-8601 string (C2-08)

## 4. Yêu cầu chức năng

### YC-1 — Contracts (`kernel/graph/contracts.py`, pydantic `extra="forbid"` mọi model)
```python
class GraphNodeStatus(str, Enum):          # PLAN §17 — đúng 8 giá trị
    PENDING = "pending"; READY = "ready"; RUNNING = "running"
    SUCCEEDED = "succeeded"; FAILED = "failed"; SKIPPED = "skipped"
    CANCELLED = "cancelled"; BLOCKED = "blocked"

class GraphRunStatus(str, Enum):           # graph-level outcome
    SUCCEEDED = "succeeded"; FAILED = "failed"; CANCELLED = "cancelled"

class JoinPolicy(str, Enum):               # PLAN §16
    ALL = "all"    # mọi dep SUCCEEDED thì node READY (mặc định)
    ANY = "any"    # ≥1 dep SUCCEEDED thì node READY (join node)

class FailurePolicy(str, Enum):            # PLAN §16
    FAIL_FAST = "fail_fast"               # node FAILED → dừng toàn graph (mặc định)
    CONTINUE = "continue"                 # bỏ qua node lỗi, node khác chạy tiếp
    SKIP_DEPENDENTS = "skip_dependents"   # toàn bộ descendants của node lỗi → SKIPPED

class Condition(BaseModel):                # extra="forbid" — v1 contract-only
    expression: str

class Dependency(BaseModel):               # extra="forbid" — 1 cạnh vào node
    node_id: str
    condition: Condition | None = None     # v1: None bắt buộc khi execute (§2 Out)

class GraphNode(BaseModel):                # extra="forbid"
    id: str
    type: PlanNodeType                     # reuse kernel.execution_plan.PlanNodeType
    name: str = ""
    agent: str = ""
    capabilities: list[str] = []
    depends_on: list[Dependency] = []      # NGUỒN SỰ THẬT topology (convert từ PlanNode.depends_on)
    join_policy: JoinPolicy = JoinPolicy.ALL
    timeout_s: float = 300.0
    retries: int = 0
    metadata: dict[str, Any] = {}
    # model_validator: timeout_s >= 0; retries >= 0; depends_on không chứa chính id; node_id trong depends_on unique

class GraphEdge(BaseModel):                # extra="forbid" — derived view (property của ExecutionGraph)
    from_id: str
    to_id: str
    condition: Condition | None = None

class ExecutionGraph(BaseModel):           # extra="forbid"
    id: str
    nodes: list[GraphNode] = Field(min_length=1)
    failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST
    metadata: dict[str, Any] = {}          # plan_ref / required_permissions / required_resources / estimated_cost / estimated_tokens (từ convert)
    # model_validator (INV-015 build gate): node ids unique; mọi dep.node_id ∈ ids (không self); validate_graph_acyclic(self.nodes)
    @property
    def edges(self) -> list[GraphEdge]     # derived: for node in nodes: for dep in node.depends_on → GraphEdge(from_id=dep.node_id, to_id=node.id, condition=dep.condition)
    def to_dict(self) -> dict[str, Any]    # model_dump(mode="json")

@dataclass
class _DagView:                            # C1-01: adapter — validate_dag giả định depends_on: list[str]
    id: str
    depends_on: list[str]

def validate_graph_acyclic(nodes: list[GraphNode]) -> None:
    """INV-015 build gate — adapt Dependency edges to validate_dag (str ids).
    Gọi validate_dag (giữ literal — AST gate) với _DagView."""
    validate_dag([_DagView(n.id, [d.node_id for d in n.depends_on]) for n in nodes])

class GraphResult(BaseModel):              # extra="forbid" — return value + metrics (PLAN §25)
    status: GraphRunStatus
    execution_id: str
    node_statuses: dict[str, GraphNodeStatus] = {}
    node_results: dict[str, Any] = {}
    node_reasons: dict[str, str] = {}      # C3-01: per-node failure reason (C3-01)
    execution_order: list[str] = []
    latency_ms: int = 0                    # graph execution time
    max_concurrent_running: int = 0        # parallelism
    failure_policy: FailurePolicy
    reason: str = ""
```
- **Test**: mọi model `extra="forbid"` (field thừa → `ValidationError`); `GraphNodeStatus` đủ đúng 8 giá trị PLAN §17; `JoinPolicy`/`FailurePolicy` đủ 2/3 giá trị; `ExecutionGraph` node id trùng → lỗi; dep unknown/self → lỗi; **cycle A→B→C→A (dựng qua `model_construct` bypass) → `ValidationError`** (INV-015 tại build); `edges` derived đúng VD PLAN §16 (`analyze→{test_backend,test_frontend}→report` → 3 edges đúng from/to); timeout_s âm → lỗi; graph rỗng node → lỗi (min_length)

### YC-2 — Errors (`kernel/graph/errors.py`)
- `GraphError(Exception)` (base) + `GraphValidationError(GraphError)` (graph/runner/settings không hợp lệ) + `GraphExecutionError(GraphError)` (lỗi runtime trong executor — v1 dùng cho trường hợp không thể chạy wave hợp lệ)
- **Test**: hierarchy đúng; message giữ nguyên

### YC-3 — State machine (`kernel/graph/state_machine.py` — thuần, không I/O)
```python
class GraphStateMachine:
    TRANSITIONS: dict[GraphNodeStatus, frozenset[GraphNodeStatus]] = {
        PENDING:  {READY, RUNNING, SKIPPED, BLOCKED, CANCELLED},   # C1-02: RUNNING hợp lệ (READY persist flow)
        READY:    {RUNNING, SKIPPED, BLOCKED, CANCELLED},
        RUNNING:  {SUCCEEDED, FAILED, CANCELLED},
        # SUCCEEDED/FAILED/SKIPPED/BLOCKED/CANCELLED: terminal (không transition ra)
    }
    @staticmethod
    def can_transition(current: GraphNodeStatus, target: GraphNodeStatus) -> bool
    @staticmethod
    def is_terminal(status: GraphNodeStatus) -> bool
    @staticmethod
    def is_ready(node: GraphNode, dep_statuses: dict[str, GraphNodeStatus]) -> bool
        # không dep → True (root); join ALL → mọi dep == SUCCEEDED; join ANY → ≥1 dep == SUCCEEDED
    @staticmethod
    def dead_end_status(dep_statuses: dict[str, GraphNodeStatus]) -> GraphNodeStatus
        # mọi dep đã terminal nhưng node không thể READY:
        #   có dep ∈ {CANCELLED, BLOCKED} → BLOCKED (ưu tiên cao nhất)
        #   ngược lại (dep ∈ {FAILED, SKIPPED}) → SKIPPED
    @staticmethod
    def graph_outcome(node_statuses: dict[str, GraphNodeStatus], cancelled: bool) -> GraphRunStatus
        # cancelled → CANCELLED; có node ∈ {FAILED, BLOCKED} → FAILED; ngược lại → SUCCEEDED (SKIPPED không tính lỗi)
```
- **Test (bảng đầy đủ)**: `can_transition` đúng mọi cặp hợp lệ/không hợp lệ (tham số hóa toàn bộ 8×8 — chỉ đúng các cặp trong TRANSITIONS); `is_terminal` đúng 5 terminal; `is_ready`: root → True; join ALL (2 dep: 1 SUCCEEDED + 1 PENDING → False; 2 SUCCEEDED → True); join ANY (1 SUCCEEDED + 1 FAILED → True; 0 SUCCEEDED → False); `dead_end_status`: dep CANCELLED → BLOCKED; dep BLOCKED → BLOCKED; dep FAILED → SKIPPED; dep SKIPPED → SKIPPED; **ưu tiên: [A FAILED, B BLOCKED] → BLOCKED**; `graph_outcome`: toàn SUCCEEDED → SUCCEEDED; có SKIPPED không FAILED → SUCCEEDED; có FAILED → FAILED; có BLOCKED → FAILED; cancelled=True → CANCELLED; mọi hàm thuần (2 lần chạy y hệt)

### YC-4 — Converter (`kernel/graph/converter.py`)
- `plan_to_graph(plan: ExecutionPlan, *, failure_policy: FailurePolicy = FailurePolicy.FAIL_FAST) -> ExecutionGraph`:
  1. `GraphNode` per `PlanNode` (giữ **thứ tự `plan.nodes`**): `id/type/name/agent/capabilities/timeout_s/retries`; `depends_on = [Dependency(node_id=d) for d in node.depends_on]` (giữ thứ tự); `join_policy = ALL` (mặc định PLAN §16; node-level override = task sau)
  2. `graph.id = plan.id`; `metadata = {source: "execution_plan", request_ref: plan.request_ref, required_permissions: plan.required_permissions, required_resources: plan.required_resources, estimated_cost: plan.estimated_cost, estimated_tokens: plan.estimated_tokens}` (028 đọc resource từ đây)
  3. **Deterministic**: cùng plan → `model_dump()` y hệt (2 lần)
  4. **Defense in depth (INV-015)**: plan lỗi (cycle/unknown dep — dựng qua `model_construct`) → `ExecutionGraph` validator raise → bọc `GraphValidationError` (converter không trả graph vòng bao giờ)
- **Test**: plan 3 node `A→B→C` → graph 3 node đúng id/type/capabilities/retries, edges derived đúng (`A→B`, `B→C`); plan VD PLAN §16 (4 node `analyze→{test_backend,test_frontend}→report`) → `edges` đúng 3 cạnh + join ALL mặc định; metadata map đúng (permissions/resources/tokens/cost/request_ref); `failure_policy` mặc định FAIL_FAST + override CONTINUE; node không dep → Dependency rỗng; deterministic 2 lần; plan cycle (model_construct) → `GraphValidationError`; plan có `depends_on` self → `GraphValidationError`

### YC-5 — GraphExecutor (`kernel/graph/executor.py`)
- `GraphExecutor(state_service: StateService, settings: GraphSettings | None = None)` — KHÔNG giữ runner (inject tại execute); thread-safe (RLock pattern ExecutionService)
- Runner contract: `GraphNodeRunner = Callable[[GraphNode, dict[str, Any]], Any]` — `fn(node, results_so_far)`; return = node result; exception → node FAILED (reason = `str(exc)`); `results_so_far` = **snapshot results tại đầu wave** (consistent view — deterministic cho test)
- `execute(graph, runner, execution_id: str | None = None) -> GraphResult` (**execution_id mặc định = f"graph:{graph.id}" — C2-05 namespace riêng, tránh đè key ExecutionService dùng plan.id**):
  1. **Pre-validate** (INV-015 defense-in-depth): **gọi thẳng `validate_dag([_DagView(n.id, [d.node_id for d in n.depends_on]) for n in graph.nodes])` — C2-01 v2: literal `validate_dag(` nằm TRONG executor.py (khớp AST gate AC7)** (ValueError → `GraphValidationError`); mọi `Dependency.condition is None` (không → `GraphValidationError("conditions not supported in v1")`); `runner` required; `settings.default_failure_policy` string hợp lệ (convert `FailurePolicy(...)` — sai → `GraphValidationError` tại init) — **C2-01 v1: field default_failure_policy được 028 tiêu thụ khi gọi plan_to_graph; 027 converter nhận failure_policy param**
  2. **Cancel-before-execute**: flag cancel đã set → trả `CANCELLED` ngay (pattern ExecutionService)
  3. **Init state**: `StateService.set_state(execution_id, {graph: graph.to_dict(), nodes: {id: PENDING}, results: {}, started_at, execution_order: [], metrics: {}})`
  4. **Wave loop (deterministic)**:
     - check cancel flag → mọi node PENDING/READY → CANCELLED; break (graph CANCELLED)
     - resolve dead-end: node PENDING mà mọi dep terminal nhưng không `is_ready` → `dead_end_status` (SKIPPED/BLOCKED) — theo dep statuses (dep FAILED/SKIPPED → SKIPPED; dep CANCELLED/BLOCKED → BLOCKED)
     - `ready = [n for n in graph.nodes if status(n) == PENDING and is_ready(n)]` — **sort theo node id asc** (deterministic — không random, không LLM); **set PENDING→READY (persist) cho toàn bộ ready set (C1-02 — 028 đọc READY từ store)**
     - ready rỗng: **nếu tồn tại node non-terminal (kẹt READY/RUNNING — path bất thường) → `raise GraphExecutionError` (no-progress guard — C2-04 v2)**; mọi node terminal → break
     - **chạy batch**: `ThreadPoolExecutor(max_workers=min(settings.max_parallel, len(ready)))`; submit theo **id asc**; **`execution_order` append do MAIN tại submit (thứ tự submit — deterministic — C2-03 v2)**; mỗi node — **worker start sequence (C2-02 v2)**: (1) check cancel flag + status hiện tại: flag set → persist `CANCELLED`, KHÔNG chạy runner; status != READY (đã terminal do policy) → bỏ qua, không ghi đè; (2) ngược lại **READY→RUNNING (persist — do WORKER — C2-03 v2)** → runner loop (retries §YC-5b — **check cancel flag TRƯỚC MỖI attempt kể cả lần 1 — C2-06 v1/C2-09**) → SUCCEEDED + result (persist) / FAILED + reason (persist); **state write protocol (C2-06 v2): executor sở hữu dict `nodes`/`results` (khởi tạo `nodes` đủ mọi node id = PENDING; set_state lưu REFERENCE — không copy khi ghi); worker CHỈ gán key đã tồn tại `nodes[node_id] = status` (GIL-atomic, không đổi kích thước); persist qua `update_state(execution_id, nodes=nodes)` cùng reference — KHÔNG read-modify-write toàn dict từ worker**; **`max_concurrent_running = max(đã ghi, min(len(ready), max_parallel))` — C2-03 v1**
     - **sau batch (tại ranh giới wave — C2-02)**, nếu có node FAILED → áp **failure policy** (node RUNNING trong batch chạy xong ghi nhận bình thường; CHỈ node PENDING/READY bị ảnh hưởng):
       - `FAIL_FAST` → mọi node còn lại PENDING/READY → **BLOCKED**; break (graph FAILED)
       - `SKIP_DEPENDENTS` → với mỗi node FAILED: toàn bộ **descendants transitive** (đảo ngược depends_on) đang PENDING/READY → **SKIPPED** (kể cả node có dep khác SUCCEEDED)
       - `CONTINUE` → không hành động ngay; dead-end resolution wave sau xử lý (node phụ thuộc dep FAILED → SKIPPED; join ANY vẫn chạy nếu có dep SUCCEEDED)
  5. **Kết thúc**: `graph_outcome(node_statuses, cancelled)` → `GraphResult`; persist state cuối (`update_state`: nodes/results/execution_order/metrics) — TASK-028/observability đọc ở đây
- `cancel(execution_id)` — thread-safe flag (pattern ExecutionService `_cancel_flags`); **lock chỉ bảo vệ `_cancel_flags` dict + StateService op đơn lẻ; wave loop chạy KHÔNG giữ lock; `cancel()` luôn trả về ngay — C2-06**; in-flight runner **không bị kill** (chạy xong, kết quả ghi nhận; các node chưa chạy → CANCELLED) — giả định §7
- **KHÔNG gọi ExecutionService** — runner injectable là nơi 028 nối real execution (adapter ExecutionService-per-node hoặc tool dispatch); GraphExecutor không đổi khi đó
- **KHÔNG emit event** — metrics trong GraphResult + StateService (giống TASK-026 `latency_ms` decision)
- **YC-5b — Retries (deterministic)**: chạy runner tối đa `node.retries + 1` lần; exception → thử lại; hết lượt → FAILED (reason lần cuối); retries = 0 → 1 lần duy nhất
- **Test (unit — fake runner, không sleep ngẫu nhiên)**:
  - `A→B→C`, max_parallel=1 → `execution_order == ["A","B","C"]`; node_statuses toàn SUCCEEDED; graph SUCCEEDED
  - `A→B, A→C, B/C→D` (join ALL) → order `["A","B","C","D"]` (B,C theo id asc); `max_concurrent_running == 1` (mặc định)
  - **READY persist (C2-03 v2)**: A→B, A→C, max_parallel=1 → runner của B (worker pool 1) assert `get_state(id)["nodes"]["C"] == "ready"` — READY persist + 028 đọc được
  - **Parallelism**: max_parallel=2, `A→B, A→C` — fake runner B chờ C started (Event, **`wait(timeout=5)` — C2-10**) → cả 2 start trước khi 1 finish → `max_concurrent_running == 2`; `execution_order == ["A","B","C"]` (thứ tự submit — deterministic bất chấp completion order)
  - **max_concurrent_running biên (C2-11)**: 3 ready, max=2 → 2
  - **FAIL_FAST**: `A→B→C`, runner A raise → `execution_order == ["A"]`; B, C **BLOCKED**; graph FAILED; reason = lỗi A
  - **CONTINUE**: `A→B, A→C, B/C→D`, A fail, B ok → A FAILED, B SUCCEEDED, C **SKIPPED** (dep A FAILED), D **SKIPPED** (dep A FAILED — join ALL); order `["A","B"]`; graph FAILED (có node FAILED — §7 giả định); node_results giữ kết quả B
  - **SKIP_DEPENDENTS**: `A→B, A→C, B/C→D`, A fail → B/C/D đều **SKIPPED** (descendants transitive — B không chạy dù dep hợp lệ); order `["A"]`; graph FAILED
  - **Join ANY**: `D depends [A, B], join ANY`, A fail, B ok, policy CONTINUE → D chạy (≥1 dep SUCCEEDED) → order `["A","B","D"]`; graph FAILED
  - **Cancel queued (C2-02 v2)**: A→{B,C,D}, max_parallel=2, cancel khi B/C đang chạy (barrier) → D KHÔNG bao giờ được gọi (runner đếm call), D CANCELLED, graph CANCELLED
  - **Retries**: runner fail 2 lần rồi ok, `retries=2` → SUCCEEDED (3 attempts); runner fail 3 lần, `retries=2` → FAILED; `retries=0` fail 1 lần → FAILED
  - **Retry-cancel (C2-09)**: fail attempt 1, cancel giữa attempt 2 → CANCELLED, không chạy attempt tiếp
  - **Cancel**: A đang chạy (fake runner chờ event), gọi `cancel()` → A finish, B/C → CANCELLED, graph CANCELLED; cancel trước execute → CANCELLED ngay; cancel 2 lần → idempotent
  - **State persist**: sau execute KHÔNG truyền execution_id → `get_state(f"graph:{graph.id}")` có đủ `graph/nodes/results/execution_order/metrics`; `get_state(graph.id) is None`; `GraphResult.execution_id == f"graph:{graph.id}"` (C2-05 v2); node statuses trong store khớp `node_statuses`
  - **Condition**: graph có `Dependency.condition` non-None → execute raise `GraphValidationError` (fail loud)
  - **No-progress guard (C2-04 v2)**: monkeypatch `ThreadPoolExecutor.submit` gây kẹt READY → `GraphExecutionError`
  - **Init validation (C2-07)**: `GraphExecutor(state, GraphSettings(default_failure_policy="bogus"))` → `GraphValidationError`
  - **Deterministic**: cùng graph + runner chạy 2 lần → `GraphResult` (trừ `latency_ms`) y hệt

### YC-6 — Wiring + config (additive)
- `config.py` MOD:
  ```python
  class GraphSettings(BaseModel):
      """TASK-027: execution graph tuning (INV-015 bounds)."""
      model_config = ConfigDict(extra="forbid")
      max_parallel: int = 1                     # số runner chạy đồng thời tối đa (>= 1)
      default_failure_policy: str = "fail_fast" # plain string — config không import kernel.graph
      # model_validator: max_parallel >= 1
  class Settings(BaseSettings):
      ...
      graph: GraphSettings = GraphSettings()
  ```
- `config.yaml` MOD (additive block):
  ```yaml
  graph:
    max_parallel: 1
    default_failure_policy: fail_fast
  ```
- `runtime_kernel.create()` — additive block **CUỐI** (sau `container.register(ExecutionService, ExecutionService)`, trước `return cls(container, bus)`):
  ```python
  # Execution graph (TASK-027): DAG execution + graph state (INV-015).
  from ..kernel.graph import GraphExecutor

  graph_executor = GraphExecutor(
      state_service=container.resolve(StateService),  # CÙNG instance với ExecutionService
      settings=settings.graph,
  )
  container.register_instance(GraphExecutor, graph_executor)
  ```
  - KHÔNG sửa block đăng ký services hiện có; `container.resolve(StateService)` phải trả **cùng instance** mà ExecutionService dùng (test AC11 bắt — nếu container không cache singleton → implementer tạo 1 `StateService()` duy nhất truyền cho cả 2 — ghi chú implement)
- **Test** (integration): `RuntimeKernel.create().container.resolve(GraphExecutor)` trả instance; `graph_executor._state is container.resolve(StateService)` (shared instance — pattern `test_model_router_wired`); Settings parse block graph + env override `AIOS_GRAPH__MAX_PARALLEL=2` (pattern test_config)

### YC-7 — Integration end-to-end (executor ↔ converter ↔ state ↔ container)
- **Test**: dựng `ExecutionPlan` hợp lệ (3 node `A→B→C` — dùng `ExecutionPlanBuilder.from_dict`) → `plan_to_graph` → `GraphExecutor.execute` với fake runner (đếm call order) → `execution_order == ["A","B","C"]`, graph SUCCEEDED, state persist đúng; qua container (runtime_kernel) execute được; **PLAN §23**: `A→B→C` và `A→B, A→C, B/C→D` → verify execution order (2 test bắt buộc đúng tên); cùng input 2 lần → deterministic

## 5. Yêu cầu kiến trúc

### 5.1 INV-015 — Graph Acyclicity (behavioral + AST enforcement)
Bản chất: *"Execution Graph không được circular dependency"* (PLAN §22):

1. **Tại build** (3 tầng — defense in depth):
   - `ExecutionGraph` model_validator gọi `validate_graph_acyclic(self.nodes)` (adapter `_DagView` — C1-01) — cycle → `ValidationError` (pydantic wrap, pattern `ExecutionPlan`)
   - `plan_to_graph` bọc lỗi → `GraphValidationError` (converter không bao giờ trả graph vòng)
   - `GraphExecutor.execute` pre-validate lại `validate_graph_acyclic` trước khi chạy (bắt graph dựng tay sai)
2. **Behavioral** (`test_inv015_graph_acyclicity` trong `test_execution_graph.py`):
   - Cycle `A→B→C→A` (qua `model_construct` bypass) → `ExecutionGraph` validation raise
   - Cycle qua convert (plan `model_construct`) → `GraphValidationError`
   - Cycle graph dựng tay + `execute` → `GraphValidationError` (không chạy node nào — `execution_order == []`)
3. **AST** (`test_architecture.py`):
   - `test_inv015_graph_acyclicity_gate` — `contracts.py` (qua `validate_graph_acyclic`) VÀ `executor.py` (pre-validate) PHẢI chứa call-site `validate_dag(` (pattern `test_inv014_planning_gate`) — graph không thể thoát validate tại build/execute mà không sửa source
   - `test_inv015_planning_no_graph` — `orchestrator/planning/` KHÔNG import `aios_core.kernel.graph` (`dir_imports(AIOS / "orchestrator" / "planning", ["aios_core.kernel.graph"]) == []`) — planning chỉ sinh plan, convert là việc graph layer (không đảo chiều trách nhiệm)

### 5.2 Allow-list import `kernel/graph/` (test mới `test_inv_graph_import_allowlist` — loop từng file, pattern `test_inv_planning_import_allowlist`)
- **aios_core allowed**: `aios_core.kernel.execution_plan` (PlanNodeType/ExecutionPlan — convert), `aios_core.kernel.dag` (validate_dag — INV-015), `aios_core.kernel.services.state` (StateService — store; nếu import qua package init thì thêm `aios_core.kernel.services`), `aios_core.config` (GraphSettings — pattern `resource.py`), `aios_core.logging` (get_logger) + intra-package `aios_core.kernel.graph.*` (loại trừ trong scan)
- **CẤM (kể cả TYPE_CHECKING — bài học TASK-023 C2-01)**: `aios_core.orchestrator.*` (kể cả `planning` — chiều intelligence → runtime không đảo; `dir_imports` đảo chiều đã có INV-014), `aios_core.models.*`, `aios_core.memory/context/knowledge/tools/agents/capabilities/workflow/contracts`, **`aios_core.kernel.services.execution`** (KHÔNG gọi ExecutionService — runner injectable §5.6), **`aios_core.kernel.services.resource`/`scheduler`** (028), `aios_core.kernel.runtime_kernel` (cycle)
- **external allowed**: `pydantic`, `typing`, `enum`, `dataclasses`, `threading`, `concurrent.futures` (ThreadPoolExecutor), `time` (monotonic), `logging`, **`datetime` (C2-04 — started_at)**
- Scan toàn dir `kernel/graph/*.py` qua `collect_imports`, loại trừ `startswith("aios_core.kernel.graph")`; ghi chú: AST đếm mọi Import node kể cả TYPE_CHECKING — graph/ dùng import runtime bình thường, KHÔNG TYPE_CHECKING
- **INV-005/INV-006/INV-014 cũ không cần sửa**: graph/ nằm trong kernel (không thuộc orchestrator allow-list); `test_inv014_runtime_no_planning` (kernel/services không import planning) vẫn pass — graph không import planning

### 5.3 Deterministic first (PLAN §13, §23)
- Scheduling **thứ tự cố định**: READY set sort node id asc; submit ThreadPool theo id asc; `execution_order` ghi thứ tự START (deterministic) — completion order KHÔNG ảnh hưởng kết quả vì cập nhật state per-node độc lập + `results_so_far` snapshot đầu wave
- Không random, không LLM, không network trong toàn bộ graph layer
- `dead_end_status`/`graph_outcome`/converter/retries đều deterministic; cùng input chạy 2 lần → `GraphResult` (trừ `latency_ms`) y hệt (test)

### 5.4 No God Object (pattern TASK-025 §5.4 / TASK-026 §5.4)
- Dependency DAG (mỗi module 1 trách nhiệm, chiều đi xuống):
```
errors.py  contracts.py                             (leaf — chỉ pydantic + kernel.execution_plan/dag)
   ↑            ↑
state_machine.py → contracts                        # transitions + readiness/skip/block + outcome (thuần)
converter.py → {contracts, errors, kernel.execution_plan}   # ExecutionPlan → ExecutionGraph
executor.py → {contracts, errors, state_machine, kernel.services.state, config}  # CHỈ điều phối wave + runner + persist
```
- **Arch assert `test_inv015_graph_no_god_object` — scan chuỗi CỤ THỂ** (pattern C2-04): (a) `executor.py` chứa `GraphStateMachine` reference (state logic nằm ngoài executor); (b) `state_machine.py` KHÔNG chứa `def execute(`; (c) `converter.py` KHÔNG chứa `def execute(`; (d) `contracts.py` KHÔNG import `executor`/`converter`/`state_machine` (leaf — qua `collect_imports`); (e) `executor.py` KHÔNG chứa `def plan_to_graph(` (convert tách module)

### 5.5 Additive only
- `git diff` sau implement: `kernel/services/execution.py`, `kernel/services/state.py`, `kernel/services/resource.py`, `kernel/services/scheduler.py`, `kernel/execution_plan.py`, `kernel/dag.py`, `orchestrator/planning/*`, `orchestrator/planner.py`, `orchestrator/orchestrator.py` **không đổi**
- MOD (chỉ THÊM, không đổi hành vi cũ): `config.py` (thêm `GraphSettings` + field `graph`), `config.yaml` (block graph), `runtime_kernel.py` (block wiring cuối), `tests/*` (additive)
- ExecutionService/StateService API cũ hoạt động y hệt (test cũ pass không sửa)

### 5.6 Quyết định thiết kế (mở — cho critic phản biện)
- **Vị trí package: `aios_core/kernel/graph/`** — KHÔNG đặt `orchestrator/execution_graph/`:
  1. **Hướng phụ thuộc TASK-028**: Graph Scheduler (kernel/services/scheduler.py) sẽ đọc graph state để schedule (PLAN §19: Graph Scheduler → Resource → Execution → State) — graph nằm kernel → scheduler import trực tiếp, không đảo chiều; nếu graph ở orchestrator → kernel/services phải import orchestrator = vi phạm đúng invariant INV-014 mà 026 vừa dựng ("Runtime không phụ thuộc intelligence")
  2. **Dùng chung 3 tầng** (PLAN M5: "dùng chung cho Runtime, Orchestrator và Harness M6") — kernel là lớp chia sẻ; orchestrator import kernel đã là pattern (planning import execution_plan/dag)
  3. **Graph state nằm trong StateService (kernel/services)** — cùng tầng, không cần allow-list chéo
  4. INV-005 rule A không dính: graph/ không nằm trong orchestrator → không cần allow-list models (vốn là bài toán của orchestrator)
  - Phương án thay thế: (a) `orchestrator/execution_graph/` — gần planning nhưng phá hướng phụ thuộc 028 (kernel→orchestrator) — **loại**; (b) đơn file `kernel/graph.py` — God Object (~500 dòng 5 trách nhiệm) — **loại** (§5.4)
- **Runner injectable, KHÔNG qua ExecutionService**: ExecutionService chạy cả plan tuyến tính với policy/resource orchestration riêng (pre-check toàn plan) — không tương thích điều khiển per-node (skip/block/join/parallel); chạy node qua ExecutionService per-node = lặp lại resource acquire/release mỗi node (đúng việc của 028); runner injectable giữ 027 additive-only + test deterministic với fake runner. **028 nối real execution vào chính injection point này** (adapter ExecutionService-per-node hoặc tool dispatch) — GraphExecutor không đổi
- **JoinPolicy trên GraphNode, KHÔNG trên GraphEdge**: join policy là thuộc tính của node đích (cách node join các dep của nó); per-edge policy vô nghĩa (A→D ANY + B→D ALL mâu thuẫn). `Dependency` mang `condition` (per-edge) — tách bạch
- **GraphEdge là derived property, không phải field**: `depends_on` (list `Dependency`) là nguồn sự thật duy nhất — edges dựng lại từ nodes mỗi lần truy cập (observability/serialization), không có dual-source drift; validator chỉ kiểm topology qua depends_on
- **StateService KHÔNG sửa — "mở rộng" theo nghĩa dữ liệu**: PLAN §17 "mở rộng State Service" được thực hiện bằng schema mới trong store hiện có (`{graph, nodes, results, ...}` với 8 trạng thái enum ở `graph/contracts.py` — nguồn duy nhất, value `"succeeded"` khác biệt với `NODE_COMPLETED="completed"` cũ — không va chạm execution cũ); StateService là generic dict store (caller-defined schema) nên **zero MOD**; thêm method query (vd `list_ready`) = đề xuất additive ở 028 khi cần
- **max_parallel trong 027 vs 028 scope**: 027 chạy READY batch với `max_workers = max_parallel` (mặc định 1 = deterministic tuyến tính) — graph biết **"task nào có thể chạy đồng thời"** (dependency-level, PLAN §19 Graph Scheduler trách nhiệm); 028 quyết định **"khi nào"** theo resource (Resource Service/Scheduler Service) — không trùng lặp
- **Condition evaluation OUT + fail loud**: contract có sẵn (PLAN §16 forward-compat), execute từ chối rõ ràng nếu gặp condition non-None — không có hành vi silent sai
- **Retries IN, timeout enforcement OUT**: retries deterministic (loop runner) rẻ và test được; timeout cần kill thread (không khả thi an toàn) — defer 028/real runner; `timeout_s` chỉ validate ≥ 0
- **Graph outcome FAILED khi CONTINUE có node FAILED**: bất kỳ node FAILED nào → graph FAILED (parity ExecutionService: node lỗi → plan FAILED); giá trị của CONTINUE/SKIP_DEPENDENTS = partial results (node_results giữ) + per-node statuses cho orchestrator quyết định — giả định §7
- **Không emit event v1**: metrics (latency_ms, max_concurrent_running) trong `GraphResult` + StateService (pattern TASK-026 `latency_ms` decision); gắn metrics/event khi 028 nối flow hoàn chỉnh

## 6. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — `GraphNodeStatus` đủ đúng 8 giá trị PLAN §17; `JoinPolicy`/`FailurePolicy` đủ 2/3 giá trị; `Condition`/`Dependency`/`GraphEdge`/`GraphNode`/`ExecutionGraph`/`GraphResult` pydantic `extra="forbid"`; `ExecutionGraph.edges` derived đúng VD PLAN §16 (analyze→{test_backend,test_frontend}→report); `GraphValidationError`/`GraphExecutionError` hierarchy đúng (YC-1, YC-2)
- [ ] **AC2**: **Convert deterministic** — `ExecutionPlan → ExecutionGraph`: nodes/depends_on → GraphNode/Dependency (giữ thứ tự plan), join ALL mặc định, failure FAIL_FAST mặc định (override được), metadata map đủ (permissions/resources/cost/tokens/request_ref); cùng plan 2 lần → `model_dump()` y hệt (YC-4)
- [ ] **AC3**: **State machine bảng đầy đủ** — `can_transition` tham số hóa 8×8 (chỉ đúng cặp trong TRANSITIONS); `is_ready` ALL/ANY/root; `dead_end_status` SKIPPED vs BLOCKED + ưu tiên CANCELLED/BLOCKED > FAILED/SKIPPED; `graph_outcome` 4 nhánh (YC-3)
- [ ] **AC4**: **PLAN §23 Graph tests** — `A→B→C` → `execution_order == ["A","B","C"]`; `A→B, A→C, B/C→D` (join ALL) → `["A","B","C","D"]` (B,C id asc); **parallelism** max_parallel=2 → 2 node READY chạy đồng thời (barrier fake runner) + `max_concurrent_running == 2` + order vẫn deterministic (YC-5)
- [ ] **AC5**: **Failure policies** — FAIL_FAST: A fail → B/C/D BLOCKED, graph FAILED, order `["A"]`; CONTINUE: dep FAILED → node SKIPPED, nhánh khác chạy tiếp, partial results giữ; SKIP_DEPENDENTS: descendants transitive SKIPPED (kể cả dep khác SUCCEEDED); **Join ANY**: D chạy khi ≥1 dep SUCCEEDED (A fail, B ok → D chạy); **parallel-failure (C2-02): max_parallel=2, A→{B,C}, B fail, C barrier → C vẫn SUCCEEDED (chạy xong trong batch), D BLOCKED**; retries=2 fail 2 lần rồi ok → SUCCEEDED (YC-5)
- [ ] **AC6**: **Cancel** — cancel lúc chạy: in-flight finish, node còn lại CANCELLED, graph CANCELLED; cancel trước execute → CANCELLED ngay; idempotent (YC-5)
- [ ] **AC7**: **INV-015 enforcement** — cycle `A→B→C→A`: **build (dựng qua `GraphNode.model_construct` bypass per-node rồi `ExecutionGraph.model_validate` — C2-07) → ValidationError**; convert (plan `model_construct`) → GraphValidationError; execute graph lỗi dựng tay (model_construct toàn bộ — pre-validate bắt) → GraphValidationError (không chạy node nào); `test_inv015_graph_acyclicity_gate` (contracts.py + executor.py chứa `validate_dag(` call-site) + `test_inv015_planning_no_graph` (planning không import kernel.graph) pass (§5.1)
- [ ] **AC8**: **Allow-list** — `test_inv_graph_import_allowlist` pass: kernel/graph/ chỉ import allow-list (execution_plan/dag/services.state/config/logging/intra; CẤM orchestrator.*/models/memory/context/knowledge/tools/agents/capabilities/workflow/contracts/execution/resource/scheduler/runtime_kernel kể cả TYPE_CHECKING); INV-005/006/014 cũ vẫn pass không sửa (§5.2)
- [ ] **AC9**: **No God Object** — `test_inv015_graph_no_god_object` pass: executor chứa `GraphStateMachine`; state_machine/converter không chứa `def execute(`; executor không chứa `def plan_to_graph(`; contracts leaf (không import executor/converter/state_machine) (§5.4)
- [ ] **AC10**: **Additive only** — `git diff`: execution.py/state.py/resource.py/scheduler.py/execution_plan.py/dag.py/planning/* không đổi; MOD chỉ thêm (config/config.yaml/runtime_kernel/tests) (§5.5)
- [ ] **AC11**: **Wiring + test suite** — `RuntimeKernel.create().container.resolve(GraphExecutor)` trả instance; `GraphExecutor._state is container.resolve(StateService)` (shared instance với ExecutionService); execute graph 3 node với fake runner qua container → SUCCEEDED; Settings parse block graph + env override `AIOS_GRAPH__MAX_PARALLEL=2`; **full pytest pass (baseline 1003 + test mới ≥ ~50)**, coverage ≥ 95% mục tiêu (hard ≥ 80%) (YC-6, YC-7)
- [ ] **AC12**: **Deterministic** — cùng graph + runner chạy 2 lần → `GraphResult` (trừ latency_ms) y hệt; `execution_order`/node_statuses không đổi khi completion order khác nhau (YC-5, §5.3)
- [ ] **AC13**: **Ranh giới TASK-028/026** — không tồn tại scheduler/resource logic trong diff (028); không sửa `ResourceService`/`SchedulerService`; graph state persist trong StateService sẵn sàng cho 028 đọc (schema tài liệu ở §3); `plan_to_graph` tiêu thụ đúng output TASK-026 (`plan.nodes.depends_on` → Dependency) (§3, §2 Out)

## 7. Rủi ro & giả định

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Parallel completion order nondeterministic phá determinism | `execution_order` ghi thứ tự START (submit id asc — deterministic); cập nhật state per-node độc lập + `results_so_far` snapshot đầu wave → kết quả cuối deterministic (test AC12) |
| ThreadPool runner treo vô hạn (không timeout) | Timeout enforcement OUT (giả định tường minh §2); runner do caller cung cấp (028/real execution có timeout riêng); `timeout_s` chỉ validate ≥ 0 |
| CONTINUE/SKIP_DEPENDENTS vẫn kết thúc graph FAILED khi có node FAILED — "tiếp tục" nhưng báo lỗi | Giả định tường minh: giá trị = partial results + per-node statuses cho orchestrator; parity ExecutionService (node lỗi → plan FAILED); critic phản biện được |
| `container.resolve(StateService)` không trả cùng instance với ExecutionService (nếu container không cache singleton) | Wiring note: nếu resolve tạo instance mới → implementer tạo 1 `StateService()` duy nhất truyền cho cả ExecutionService (sửa block register services — additive) — test AC11 bắt |
| Graph state dùng chung StateService với execution cũ — key trùng | **execution_id mặc định = `f"graph:{graph.id}"` (C2-05 v2 — namespace riêng, không đè key plan.id của ExecutionService)**; test: execute không truyền execution_id → `get_state(f"graph:{graph.id}")` có state, `get_state(graph.id) is None`, `GraphResult.execution_id == f"graph:{graph.id}"`; snapshot riêng từng schema |
| SKIPPED vs BLOCKED semantics nhầm lẫn giữa các policy | Bảng tường minh §YC-3/§YC-5: SKIPPED = dep FAILED/SKIPPED (không chạy được); BLOCKED = dep CANCELLED/BLOCKED hoặc FAIL_FAST dừng graph; test từng nhánh policy riêng |
| Thread leak khi cancel (in-flight runner không kill được) | Giả định tường minh (pattern ExecutionService cũng vậy): cancel = flag, in-flight chạy xong; kill thread không khả thi an toàn Python |
| Condition field tồn tại nhưng không evaluate — người dùng tưởng chạy được | Fail loud: execute từ chối graph có condition non-None (`GraphValidationError`) — không bao giờ silent |
| max_parallel=1 mặc định làm mất lợi ích song song | Mặc định deterministic tuyến tính (test ổn định nhất); bật song song qua config `graph.max_parallel` (test riêng); 028 sẽ schedule resource-aware |

**Giả định**:
- `Condition.expression` v1 không có cú pháp chuẩn — chỉ là contract placeholder (PLAN §16); evaluation + syntax = task sau 028/029
- `GraphResult` là nguồn observability duy nhất v1 (không emit event mới — EventType giữ nguyên; TASK-026 precedent `latency_ms`)
- Node chạy đồng bộ (sync runner); async runner = task sau (deterministic-first)
- Graph v1 không resume từ snapshot (state persist để 028/observability dùng; resume = task sau)
- `max_parallel` giới hạn số runner đồng thời, không phải số wave; READY batch có thể lớn hơn max_parallel → ThreadPool giới hạn workers (chạy theo đợt con nội bộ, submit order id asc)
- `required_permissions/required_resources` từ plan chuyển vào `metadata` (028 sẽ đọc để policy/resource check — không thực thi trong 027)
- Failures do runner raise Exception; runner trả `None` hợp lệ (result = None — node vẫn SUCCEEDED)

## 8. Expected artifacts

| File | Loại | Nội dung |
|------|------|----------|
| `backend/src/aios_core/kernel/graph/contracts.py` | NEW | `GraphNodeStatus` (8) / `GraphRunStatus` / `JoinPolicy` / `FailurePolicy` / `Condition` / `Dependency` / `GraphEdge` / `GraphNode` / `ExecutionGraph` (+ `edges` derived property + validate_dag trong model_validator) / `GraphResult` (metrics) — pydantic `extra="forbid"` |
| `backend/src/aios_core/kernel/graph/errors.py` | NEW | `GraphError` + `GraphValidationError` + `GraphExecutionError` |
| `backend/src/aios_core/kernel/graph/state_machine.py` | NEW | `GraphStateMachine` — `TRANSITIONS`/`can_transition`/`is_terminal`/`is_ready`/`dead_end_status`/`graph_outcome` (thuần, không I/O) |
| `backend/src/aios_core/kernel/graph/converter.py` | NEW | `plan_to_graph(plan, *, failure_policy)` — ExecutionPlan → ExecutionGraph (deterministic, INV-015 defense-in-depth) |
| `backend/src/aios_core/kernel/graph/executor.py` | NEW | `GraphExecutor` — wave scheduling deterministic + ThreadPool max_parallel + failure policies + cancel + retries + metrics + StateService persist + `GraphNodeRunner` type |
| `backend/src/aios_core/kernel/graph/__init__.py` | NEW | Re-export public API (ExecutionGraph/GraphNode/GraphNodeStatus/JoinPolicy/FailurePolicy/GraphResult/GraphExecutor/plan_to_graph/GraphError...) |
| `backend/src/aios_core/config.py` | MOD | `GraphSettings` (`extra="forbid"`: max_parallel ≥ 1, default_failure_policy string) + `Settings.graph` (additive) |
| `backend/config.yaml` | MOD | Block `graph` (max_parallel: 1, default_failure_policy: fail_fast) |
| `backend/src/aios_core/kernel/runtime_kernel.py` | MOD | Wiring block `GraphExecutor` cuối `create()` (additive, shared StateService) |
| `backend/tests/test_execution_graph.py` | NEW | Unit (contracts/state machine bảng 8×8/converter/executor policies/cancel/retries/parallelism/determinism) + INV-015 behavioral + integration (converter→executor, runtime_kernel) + PLAN §23 (A→B→C, A→B/A→C/B/C→D) |
| `backend/tests/test_architecture.py` | MOD | `test_inv_graph_import_allowlist` + `test_inv015_graph_acyclicity_gate` + `test_inv015_graph_no_god_object` + `test_inv015_planning_no_graph` |
| `backend/tests/test_config.py` | MOD | Settings parse block `graph` + env override (additive) |
| `backend/tests/test_runtime_kernel.py` | MOD | `test_graph_executor_wired` (additive, pattern `test_model_router_wired`) |
| `aios/progress/tasks/TASK-027/` | — | critique-1/2, tasks.md, review.md, test.md, evaluation.md (theo workflow gate) |

## 9. Ghi chú thiết kế (cho critic phản biện)

- **kernel/graph/ vs orchestrator/execution_graph/**: spec chọn kernel (hướng phụ thuộc 028: scheduler kernel đọc graph state — tránh kernel→orchestrator inversion vi phạm tinh thần INV-014). Critic: có nên đặt graph ở orchestrator để tách Intelligence/Runtime theo PLAN §26 (Graph thuộc Intelligence)? — nếu vậy, 028 scheduler (kernel) phải import orchestrator — đề xuất cách giải quyết nếu critic chọn hướng này
- **Runner injectable vs ExecutionService**: spec chọn runner (additive-only + per-node control). Critic: có nên để GraphExecutor nhận `ExecutionService` làm runner mặc định (adapter) ngay trong 027? Spec defer sang 028 vì policy/resource pre-check của ExecutionService không tương thích per-node skip/block — nhưng critic có thể đề xuất adapter tối thiểu
- **StateService zero-MOD**: spec đọc "mở rộng State Service" (PLAN §17) là mở rộng schema dữ liệu, không đổi code. Critic: có nên thêm method additive vào StateService (vd `node_statuses(execution_id)` query) để 028 đọc sạch hơn? Spec defer (generic store đã đủ `get_state`)
- **GraphEdge derived property**: spec loại field stored (dual-source drift). Critic: có nên cho phép edges stored để hỗ trợ edge không thuộc depends_on (vd conditional trigger edge) tương lai? Spec chọn YAGNI v1
- **JoinPolicy trên node, không trên edge**: spec chốt node-level (join semantics thuộc node đích). Critic phản biện nếu có pattern yêu cầu per-edge
- **Graph FAILED khi CONTINUE có node failed**: quyết định mạnh (parity ExecutionService). Critic: có nên SUCCEEDED-with-partial khi policy CONTINUE và không node nào BLOCKED/CANCELLED?
- **max_parallel trong 027**: có phải scope creep sang 028? Spec cho rằng "graph hỗ trợ dependency + parallel" là DoD M5 của chính Graph (§25 Intelligence), 028 = resource-aware scheduling; boundary: 027 không đụng ResourceService
- **Condition fail-loud**: contract có sẵn nhưng execute từ chối — critic: có nên validation chặn ngay tại build (ExecutionGraph validator) thay vì lúc execute? Spec chọn execute (contract cho phép lưu trữ, converter không tạo condition — linh hoạt forward-compat)
- **Retries IN / timeout OUT**: critic: có nên thực thi timeout v1 (future.result(timeout) — chấp nhận thread leak) để graph tự trị hoàn toàn? Spec defer (leak thread không an toàn; ExecutionService/028 có timeout riêng)
