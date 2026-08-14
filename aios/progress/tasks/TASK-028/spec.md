# TASK-028 — Parallel Scheduler (M5-P10, Phase 3 — task CUỐI M5)

**Metadata**: TASK-028 | M5/P10 | 2026-08-15 | v3 (critique-1 + critique-2 resolved) | AIOS Orchestrator
**Tiền đề**: TASK-023..027 đã `done` (đặc biệt 027 Execution Graph: wave loop + READY persist + runner injectable + max_parallel + INV-015 enforced)
**Module đích**: `backend/src/aios_core/kernel/scheduler/` (subpackage mới) + `config.py`/`config.yaml` (MOD additive: block `scheduler`) + `kernel/runtime_kernel.py` (MOD additive: wiring cuối `create()`) + `tests/` (NEW `test_parallel_scheduler.py` + MOD `test_architecture.py` + MOD `test_config.py` + MOD `test_runtime_kernel.py`)

## 1. Mục tiêu

Trả lời câu hỏi M5 cuối cùng (PLAN §18): ***"Task nào có thể chạy đồng thời?"*** — không chỉ theo dependency (đã có ở 027) mà còn theo **resource toàn hệ thống**:

```
Planning → Execution Graph → Graph Scheduler → Resource Service → Execution Service → State Service
```

- **Graph Scheduler (028)** quyết định "khi nào node chạy được" = dependency-level (READY set — đã có từ GraphExecutor 027) **∧ resource có sẵn** (qua ResourceService — F-003 FIFO slot queue sẵn có).
- **INV-016 Scheduler Separation** (PLAN §22): Scheduler **KHÔNG sở hữu Resource/Execution implementation** — chỉ gọi qua public API (interface-level, duck-typing); enforcement bằng test AST + behavioral (pattern INV-015 của 027).
- **Value-add của 028 so với 027** (xác định rõ để tránh trùng lặp):
  1. **Resource gating**: 027 chạy tối đa `max_parallel` node *bất chấp* giới hạn toàn hệ thống; 028 tôn trọng `ResourceService.max_concurrent` — node READY phải **acquire slot → execute → release** trước khi thực sự chạy (node chờ → FIFO queue).
  2. **Scheduler metrics** (PLAN §25): queue time, resource usage, parallelism — trong `ScheduledGraphResult` + StateService (không emit event mới — pattern 026/027).
  3. **INV-016 enforced** — ranh giới "Scheduler không sở hữu Resource/Execution" được test AST + behavioral, không chỉ tuyên bố.
  4. **Cầu nối real execution**: `ExecutionServiceRunner` (adapter qua **public API** của ExecutionService — 1-node plan per GraphNode: policy check per node + events + state envelope) + `schedule_plan()` convenience tiêu thụ `GraphSettings.default_failure_policy` (ghi chú config 027: *"consumed by TASK-028 when building graphs via plan_to_graph"*).
- **Quan hệ với GraphExecutor: 028 WRAP, không thay thế wave loop** — `GraphScheduler.schedule()` gọi `GraphExecutor.execute(graph, gated_runner)`; gating nằm trong runner wrapper (chính injection point 027 để dành — xem evaluation 027: *"runner adapter nối real execution (injection point sẵn)"*). KHÔNG duplicate dependency logic (dead-end/policy/cancel/retries/READY persist giữ nguyên ở GraphExecutor).

## 2. Phạm vi

**In**:
- `kernel/scheduler/` — NEW subpackage: `contracts.py`, `errors.py`, `scheduler.py`, `execution_runner.py`, `__init__.py`
- `config.py` — MOD (additive): `SchedulerSettings` (pydantic `extra="forbid"`) + `Settings.scheduler: SchedulerSettings = SchedulerSettings()`
- `config.yaml` — MOD (additive): block `scheduler` (defaults)
- `kernel/runtime_kernel.py` — MOD (additive): wiring block `register_instance(GraphScheduler, ...)` (CUỐI `create()` — sau block GraphExecutor 027)
- `tests/test_parallel_scheduler.py` — NEW: unit (resource gating, queue, order, timeout, metrics) + integration (graph + scheduler + ResourceService thật/fake + runtime_kernel) + INV-016 behavioral + PLAN §23 (A→B→C và A→B, A→C, B/C→D)
- `tests/test_architecture.py` — MOD (additive): `test_inv016_scheduler_import_allowlist` + `test_inv016_scheduler_no_god_object` + `test_inv016_scheduler_no_private_access` + `test_inv016_scheduler_call_sites` + `test_inv016_graph_no_scheduler` + `test_inv016_planning_no_scheduler`
- `tests/test_config.py` — MOD (additive): Settings parse block `scheduler` + env override
- `tests/test_runtime_kernel.py` — MOD (additive): `test_graph_scheduler_wired` (pattern `test_graph_executor_wired`)

**Out (không làm — tránh scope creep)**:
- **KHÔNG sửa** `ExecutionService`/`ResourceService`/`SchedulerService`/`StateService` (kernel/services/*) — 028 chỉ **gọi qua public API**; ExecutionServiceRunner dựng 1-node `ExecutionPlan` qua `ExecutionPlanBuilder` (additive, không đổi service)
- **KHÔNG sửa** `kernel/graph/*` (GraphExecutor/plan_to_graph/contracts/state_machine) — allow-list graph CẤM resource/scheduler từ 027 §5.2 vẫn giữ nguyên; 028 nằm package riêng (quyết định §5.1)
- **KHÔNG tương tác với `SchedulerService` (kỹ thuật — cron/one-shot)**: "khi nào chạy" của 028 = dependency READY ∧ resource available; SchedulerService phục vụ background jobs — giữ nguyên, không dùng, không làm cron mới
- **KHÔNG làm distributed scheduler / multi-process / async runner** — M7–M9 (PLAN §M5-1)
- **KHÔNG thêm trạng thái mới vào graph state machine** (8 trạng thái 027 giữ nguyên; node chờ resource hiển thị `RUNNING` — semantic v1, xem §7)
- **KHÔNG emit event mới** — metrics trong `ScheduledGraphResult` + StateService key `scheduler_metrics` (pattern 026 `latency_ms` / 027 metrics)
- **KHÔNG làm token gating ở scheduler** — scheduler gate = concurrency slot; token accounting nằm trong ExecutionService (khi dùng adapter) — v1 (giả định §7)
- **KHÔNG làm resource types động / per-node resource requirement mới**: v1 mỗi node = 1 slot; plan contract chưa có per-node `required_resources` (chỉ plan-level — 027 đã copy vào `graph.metadata`) — đề xuất additive field ở task sau
- **KHÔNG import `aios_core.orchestrator.*`** trong `kernel/scheduler/` (kể cả TYPE_CHECKING — bài học TASK-023 C2-01): chiều intelligence → runtime không đảo (INV-014 tinh thần); allow-list §5.2
- **KHÔNG**: LLM/random trong scheduling (deterministic tuyệt đối), dynamic graph mutation lúc chạy, queue riêng của scheduler (dùng FIFO `acquire_slot_wait` sẵn có — F-003)

## 3. Input / Output

- **Input**:
  - `ExecutionGraph` (027 output — node/edge/dependency/failure_policy + `graph.metadata.required_resources`) HOẶC `ExecutionPlan` (026 output — qua `schedule_plan`)
  - `GraphNodeRunner = Callable[[GraphNode, dict[str, Any]], Any]` (caller-injected — tool dispatch/agent dispatch; giữ contract 027)
  - `ResourceService` (inject — **cùng instance** với ExecutionService qua container; dùng `acquire_slot_wait`/`release_slot`/`stats`/`pending` — public API)
  - `StateService` (inject — **cùng instance**; ghi `scheduler_metrics`)
  - `GraphExecutor` (inject — mặc định tự dựng `GraphExecutor(state_service)` nếu không truyền)
  - `SchedulerSettings` (config: `resource_wait_timeout_s`)
- **Output**:
  - `GraphScheduler.schedule(graph, runner, *, execution_id=None) -> ScheduledGraphResult`:
    - `execution_id: str` (mặc định `f"graph:{graph.id}"` — namespace 027, không đổi)
    - `graph: GraphResult` — kết quả đầy đủ từ GraphExecutor (wrap — status/order/statuses/metrics 027)
    - `node_metrics: dict[node_id, NodeResourceMetrics]` — `{resource_wait_ms: int, slots_acquired: int}` (queue time per node — PLAN §25)
    - `queue_time_ms: int` — max per-node wait
    - `peak_slots_used: int` — đỉnh số slot scheduler giữ đồng thời (resource usage)
    - `resource_stats: dict[str, Any]` — `ResourceService.stats()` sau chạy (used_tokens/running/max_*)
  - State persist: `update_state(execution_id, scheduler_metrics={node_metrics, queue_time_ms, peak_slots_used, resource_stats})` — key **riêng**, KHÔNG clobber `metrics` của graph (027 đã ghi `metrics={latency_ms, max_concurrent_running}` — last-write-wins nếu cùng key)
  - `GraphScheduler.schedule_plan(plan, runner, *, failure_policy=FailurePolicy.FAIL_FAST, execution_id=None)` — `plan_to_graph` → `schedule` (tiêu thụ `default_failure_policy` từ settings tại call-site)

## 4. Yêu cầu chức năng

### YC-1 — Contracts (`kernel/scheduler/contracts.py`, pydantic `extra="forbid"`)
```python
class NodeResourceMetrics(BaseModel):          # extra="forbid"
    resource_wait_ms: int = 0                  # TỔNG thời gian chờ slot (queue time — C2-01: tổng, không phải attempt cuối)
    slots_acquired: int = 0                    # C2-01: tổng số lần acquire THÀNH CÔNG (tính cả retry); tăng dưới lock

class ScheduledGraphResult(BaseModel):         # extra="forbid" — 028 sở hữu contract riêng (KHÔNG MOD GraphResult 027)
    execution_id: str
    graph: GraphResult                         # wrap kết quả GraphExecutor (027 — không đổi)
    node_metrics: dict[str, NodeResourceMetrics] = {}   # pre-init ĐỦ mọi node id (pattern 027)
    queue_time_ms: int = 0                     # max(node_metrics.resource_wait_ms)
    peak_slots_used: int = 0                   # đỉnh slot scheduler giữ đồng thời (C3-06: = slot scheduler giữ, ≠ stats().running)
    resource_stats: dict[str, Any] = {}        # ResourceService.stats() cuối chạy
```
- **Test**: `extra="forbid"` (field thừa → `ValidationError`); `ScheduledGraphResult` nhận `GraphResult` thật (graph 3 node SUCCEEDED); `node_metrics` chứa mọi node id; default metrics = 0

### YC-2 — Errors (`kernel/scheduler/errors.py`)
- `SchedulerError(Exception)` (base) + `ResourceUnavailableError(SchedulerError)` (acquire timeout — reason chứa node id + thời gian chờ) + `ExecutionNodeError(SchedulerError)` (ExecutionServiceRunner: node execution thất bại — reason từ `ExecutionResult.reason`)
- **Test**: hierarchy đúng; message giữ nguyên

### YC-3 — GraphScheduler (`kernel/scheduler/scheduler.py`)
```python
class GraphScheduler:
    def __init__(self, resource_service, state_service, *,
                 executor: GraphExecutor | None = None,
                 settings: SchedulerSettings | None = None,
                 graph_settings: GraphSettings | None = None) -> None:  # C1-02
        # resource_service/state_service/executor: duck-typed (public API) — INV-016
        # executor mặc định = GraphExecutor(state_service); graph_settings dùng cho
        # schedule_plan resolve default_failure_policy (C1-02)
        # settings mặc định = SchedulerSettings(); settings sai kiểu → SchedulerError

    def schedule(self, graph: ExecutionGraph, runner: GraphNodeRunner, *,
                 execution_id: str | None = None) -> ScheduledGraphResult: ...
    def schedule_plan(self, plan: ExecutionPlan, runner: GraphNodeRunner, *,
                      failure_policy: FailurePolicy | None = None,  # C1-02: None → graph_settings.default_failure_policy
                      execution_id: str | None = None) -> ScheduledGraphResult: ...
    def cancel(self, execution_id: str) -> None: ...   # C2-05: delegate tới GraphExecutor.cancel
```
- `schedule()` flow (single-threaded orchestration; execution threads thuộc GraphExecutor):
  1. **Pre-init** `node_metrics = {n.id: NodeResourceMetrics() for n in graph.nodes}` (worker chỉ gán key đã tồn tại — GIL-atomic, pattern 027)
  2. **Gated runner** (bọc `runner` caller-injected — chính injection point 027):
     ```
     def gated(node, results_so_far):
         t0 = time.monotonic()
         acquired = False
         try:
             if not resource_service.acquire_slot_wait(timeout=settings.resource_wait_timeout_s):
                 raise ResourceUnavailableError(f"node {node.id}: resource wait timeout")
             acquired = True
             with lock:
                 node_metrics[node.id].resource_wait_ms += int((time.monotonic() - t0) * 1000)  # C2-01: tổng
                 node_metrics[node.id].slots_acquired += 1  # C2-01: dưới lock, tính retry
                 slots_held += 1; peak_slots_used = max(peak_slots_used, slots_held)
             return runner(node, results_so_far)          # real execution (caller-injected)
         finally:
             if acquired:                                  # release CHỈ khi đã acquire (không lệch âm)
                 with lock: slots_held -= 1                # C3-06: decrement TRƯỚC release
                 resource_service.release_slot()
     ```
     - exception từ runner → gate KHÔNG nuốt: GraphExecutor bắt → node FAILED (reason) — hành vi 027 giữ nguyên
  3. `graph_result = executor.execute(graph, gated, execution_id=execution_id)` — **wrap, không thay wave loop**
  4. `queue_time_ms = max(m.resource_wait_ms for m in node_metrics.values(), default=0)`; `resource_stats = resource_service.stats()`
  5. Persist `update_state(execution_id or f"graph:{graph.id}", scheduler_metrics={...})` — key riêng
  6. Trả `ScheduledGraphResult` — `execution_id` = `graph_result.execution_id` (nguồn duy nhất)
- `schedule_plan()`: `plan_to_graph(plan, failure_policy=failure_policy)` → `schedule(...)` — **INV-015 defense-in-depth đã có sẵn trong converter/executor 027, không làm lại**
- KHÔNG chứa: `def execute(`, `ThreadPoolExecutor`, private-attr access (`. _running`, `._queue`, `._states`, `._run_node`...) — §5.3
- **Test (unit — fake runner, barrier `wait(timeout=5)` — bài học 027 C2-10)**:
  - **Single slot serial**: `ResourceService(max_concurrent=1)`, graph `A→B→C`, max_parallel=1 → `execution_order == ["A","B","C"]`; runner B (barrier) chỉ start sau khi A finish (event chain) → deterministic
  - **Parallel bounded (C2-06 v2 — inject executor tường minh)**: `max_concurrent=2`, graph `A→{B,C,D}` (3 ready), **inject `executor=GraphExecutor(state, GraphSettings(max_parallel=3))`** → barrier: tại mọi thời điểm ≤ 2 runner đồng thời (đếm qua fake runner with lock), cả 3 SUCCEEDED, `peak_slots_used == 2`, `execution_order == ["A","B","C","D"]`
  - **Queue observability**: chạy trên → `resource_service.pending() >= 1` trong lúc node sau chờ (barrier + poll); sau chạy `pending() == 0`
  - **Timeout (P3-07 — barrier-poll thay sleep, timeout 0.1s)**: `resource_wait_timeout_s=0.1`, slot bị giữ vô hạn (fake runner barrier) → node chờ FAILED (reason chứa `"timeout"`), graph FAILED (FAIL_FAST → node còn lại BLOCKED); **release an toàn**: `stats()["running"] == 0` và `pending() == 0` sau
  - **Runner raise → slot released**: runner raise → node FAILED, `stats()["running"] == 0` (finally chạy đủ)
  - **Cancel-while-waiting (C2-04 v2)**: `max_concurrent=1`, {X,Y} độc lập, X giữ slot (barrier), `GraphScheduler.cancel(execution_id)` lúc Y chờ → với `node.retries ≥ 1`: Y CANCELLED, `pending()==0` sau; **ghi rõ: retries=0 → Y FAILED timeout (KHÔNG CANCELLED — worker chỉ check flag giữa attempts)**
  - **Metrics**: `resource_wait_ms >= 0` mọi node; `queue_time_ms == max(node_metrics...)`; `peak_slots_used == 2`; `resource_stats` có `running/max_concurrent`; **`slots_acquired == 2` với `retries=1` (P3-08)**
  - **schedule_plan**: plan 3 node → SUCCEEDED + order đúng; `failure_policy=CONTINUE` override → graph.failure_policy == CONTINUE; **`failure_policy=None` → resolve `graph_settings.default_failure_policy` (convert str→FailurePolicy — C2-01 v2)**; plan cycle → `GraphValidationError`
  - **Deterministic (P3-04)**: cùng graph + runner chạy 2 lần trên **ResourceService instance MỚI** → `ScheduledGraphResult` (trừ timing fields) y hệt

### YC-4 — ExecutionServiceRunner (`kernel/scheduler/execution_runner.py` — adapter, INV-016)
```python
class ExecutionServiceRunner:
    """Chạy 1 GraphNode qua ExecutionService — public API DUY NHẤT (INV-016):
    dựng 1-node ExecutionPlan per node → execution_service.execute(plan, {node_id: inner}).
    Envelope v1: policy check per node (PLAN §20) + events (WORKFLOW_* per node) + state + slot/token
    accounting bên trong ExecutionService. Real capability execution = inner (caller-injected)."""
    def __init__(self, execution_service, *, permissions: list[str] | None = None,
                 tokens: int = 0, inner: NodeRunner | None = None) -> None:
        # permissions/tokens: caller-side composition (vd graph.metadata.get("required_permissions", []))
        # inner: Callable[[PlanNode, dict], Any] — None → noop (envelope-only, cho wiring test)
    def __call__(self, node: GraphNode, results: dict[str, Any]) -> Any:
        plan = ExecutionPlan(
            id=f"gnode:{node.id}",                    # namespace riêng — không đè graph:{id} / plan.id
            nodes=[PlanNode(id=node.id, type=node.type, name=node.name,
                            agent=node.agent, capabilities=list(node.capabilities),
                            depends_on=[], timeout_s=node.timeout_s, retries=node.retries)],
            required_permissions=list(self._permissions),
            estimated_tokens=self._tokens,
            required_resources={},
        )
        res = self.execution_service.execute(plan, {node.id: self._inner or _noop_runner})  # C2-04: literal khớp AC9
        if res.status is not ExecutionStatus.COMPLETED:
            raise ExecutionNodeError(f"node {node.id}: {res.reason}")
        return res.node_results.get(node.id)
```
- **Test (fake ExecutionService — spy public API, không đụng internals)**:
  - `__call__` dựng đúng 1-node plan: `plan.nodes == [node]` (id/type/capabilities/retries/timeout), `depends_on == []`, `id == f"gnode:{node.id}"`, permissions/tokens truyền đúng
  - `execute` trả COMPLETED → trả `node_results[node.id]`; trả FAILED → `ExecutionNodeError` (reason giữ)
  - inner được gọi với `(PlanNode, results)`; inner None → noop (result None, node COMPLETED)
  - Qua `RuntimeKernel.create()` thật: plan 3 node `A→B→C` + `GraphScheduler.schedule_plan` + `ExecutionServiceRunner(execution_service=..., permissions=[], inner=noop)` → SUCCEEDED, mọi node COMPLETED qua ExecutionService, state có cả `graph:*` (027) + `gnode:*` (ExecutionService) + `scheduler_metrics`

### YC-5 — Config + Wiring (additive)
- `config.py` MOD:
  ```python
  class SchedulerSettings(BaseModel):
      """TASK-028: graph scheduler tuning (INV-016 bounds)."""
      model_config = ConfigDict(extra="forbid")
      resource_wait_timeout_s: float | None = None   # None = chờ vô hạn (FIFO fair — F-003)
      # model_validator: resource_wait_timeout_s is None or >= 0
  class Settings(BaseSettings):
      ...
      scheduler: SchedulerSettings = SchedulerSettings()
  ```
- `config.yaml` MOD (additive block):
  ```yaml
  scheduler:
    resource_wait_timeout_s: null
  ```
- `runtime_kernel.create()` — additive block CUỐI (sau block GraphExecutor 027, trước `return cls(container, bus)`):
  ```python
  # Graph scheduler (TASK-028): resource-aware scheduling via ResourceService
  # public API (INV-016 — không sở hữu Resource/Execution implementation).
  from ..kernel.scheduler import GraphScheduler

  graph_scheduler = GraphScheduler(
      resource_service=container.resolve(ResourceService),  # CÙNG instance với ExecutionService
      state_service=container.resolve(StateService),       # CÙNG instance
      executor=container.resolve(GraphExecutor),           # CÙNG instance 027
      settings=settings.scheduler,
      graph_settings=settings.graph,                       # C2-01 v2: schedule_plan tiêu thụ default_failure_policy
  )
  container.register_instance(GraphScheduler, graph_scheduler)
  ```
- **Test**: `RuntimeKernel.create().container.resolve(GraphScheduler)` trả instance; `_resources is container.resolve(ResourceService)` + `_state is container.resolve(StateService)` + `_executor is container.resolve(GraphExecutor)` (shared instances — pattern `test_graph_executor_wired`); **`_graph_settings is settings.graph` (C2-01 v2 — AC10 assert)**; Settings parse block scheduler + env override `AIOS_SCHEDULER__RESOURCE_WAIT_TIMEOUT_S=0.5`

### YC-6 — Integration end-to-end (PLAN §23 + §19 flow)
- **Test (bắt buộc đúng tên PLAN §23)**: `test_plan23_a_to_b_to_c_via_scheduler` và `test_plan23_a_to_b_a_to_c_bc_to_d_via_scheduler` — dựng `ExecutionPlan` (builder) → `GraphScheduler.schedule_plan` với fake runner (đếm call order) → order đúng + parallelism ≤ resource limit + `ScheduledGraphResult` đầy đủ metrics
- **Test INV-016 behavioral (chain thật)**: `ResourceService(max_concurrent=1)` + spy wrapper (bọc public methods — ghi call sequence) + graph `A→B` → **call sequence deterministic**: `acquire_slot_wait(A) → release_slot(A) → acquire_slot_wait(B) → release_slot(B)` (A chạy xong rồi B mới acquire — FIFO); KHÔNG có call private nào
- **Test duck-typed stub**: `StubResource` chỉ implement `acquire_slot_wait/release_slot/stats/pending` (KHÔNG kế thừa ResourceService) → GraphScheduler chạy bình thường — chứng minh phụ thuộc API-level (INV-016 behavioral)

## 5. Yêu cầu kiến trúc

### 5.1 Vị trí package: `kernel/scheduler/` (NEW) — KHÔNG mở rộng `kernel/graph/`, KHÔNG vào `kernel/services/`
1. **Allow-list 027 CẤM sẵn**: `test_inv_graph_import_allowlist` (TASK-027 §5.2) chặn `kernel/graph/` import `kernel.services.resource`/`scheduler` — kèm chú thích "(028)". Đặt scheduler vào graph/ = bắt buộc MOD allow-list vừa dựng (bài học: invariant ổn định); scheduler ở package riêng → graph/ giữ nguyên, allow-list giữ nguyên, chiều phụ thuộc đúng: **scheduler → graph** (scheduler là consumer).
2. **PLAN §19 5 thành phần là 5 vai tách bạch**: Graph Scheduler (dependency + resource timing) khác Execution Graph (dependency topology) khác Resource Service (resource) — gộp scheduler vào graph/ tạo package "God Object" 2 trách nhiệm; gộp vào `kernel/services/` trộn M1 9-service layer với M5 intelligence layer (services/ đang được scan riêng — `test_inv014_runtime_no_planning`; thêm file vào đó phải MOD các scan hiện có).
3. **INV-016 testable boundary**: package riêng = allow-list riêng + no-private-access scan riêng — ranh giới "không sở hữu implementation" kiểm chứng được bằng AST, không phải lời tuyên bố.
4. Naming: `kernel/scheduler/` (GraphScheduler) vs `kernel/services/scheduler.py` (SchedulerService kỹ thuật) — package boundary disambiguates; risk + cách giảm ở §7.
- Phương án thay thế (cho critic): (a) mở rộng `kernel/graph/` — gần về dependency nhưng phá allow-list 027 + trộn trách nhiệm — **loại**; (b) `kernel/services/` — trộn layer — **loại**

### 5.2 Allow-list import `kernel/scheduler/` (test mới `test_inv016_scheduler_import_allowlist` — loop từng file, pattern `test_inv_graph_import_allowlist`)
- **aios_core allowed (toàn dir — C2-06 v2)**: `aios_core.kernel.graph` (contracts/executor/converter/errors/state_machine — **liệt kê đủ submodule, pattern `test_inv_graph_import_allowlist` prefix filter — P3-01**), `aios_core.kernel.services.state`, `aios_core.kernel.services.resource`, **`aios_core.kernel.execution_plan` (TOÀN DIR — contracts thuần, annotation `schedule_plan` — C2-03 v2)**, `aios_core.config`, `aios_core.logging` + intra-package `aios_core.kernel.scheduler.*` (loại trừ trong scan)
- **aios_core allowed — CHỈ `execution_runner.py`** (pin bằng AST — §5.3): `aios_core.kernel.services.execution` (ExecutionService)
- **LƯU Ý (P3-02)**: import `aios_core.kernel.services` TRẦN KHÔNG nằm allow — bắt buộc import đường dẫn đầy đủ (`.state`/`.resource`/`.execution`); `aios_core.kernel.graph` import tương tự cần submodule rõ ràng
- **CẤM (kể cả TYPE_CHECKING — bài học TASK-023 C2-01)**: `aios_core.orchestrator.*` (kể cả `planning` — chiều intelligence → runtime không đảo), `aios_core.models.*`, `aios_core.memory/context/knowledge/tools/agents/capabilities/workflow/contracts`, **`aios_core.kernel.services.scheduler`** (SchedulerService kỹ thuật — không tương tác), `aios_core.kernel.runtime_kernel` (cycle), `aios_core.kernel.graph` bị CẤM chỉ đối với... không — graph ALLOWED (scheduler là consumer)
- **external allowed**: `pydantic`, `typing`, `threading` (RLock — peak counter), `time` (monotonic), `logging`
- **Import tuyệt đối TOÀN BỘ** (bài học TASK-027: `_resolve_relative` resolve 2-dots từ package 3 cấp SAI — `kernel/scheduler/x.py` là package 3 cấp): `from aios_core.kernel.services.resource import ResourceService`, `from aios_core.kernel.graph import GraphExecutor`, ... — KHÔNG relative import
- Scan toàn dir `kernel/scheduler/*.py` qua `collect_imports`, loại trừ `startswith("aios_core.kernel.scheduler")`; AST đếm mọi Import node kể cả TYPE_CHECKING — scheduler dùng import runtime bình thường

### 5.3 INV-016 — Scheduler Separation (behavioral + AST enforcement)
Bản chất: *"Scheduler không sở hữu Resource/Execution implementation — chỉ gọi qua interface/API"* (PLAN §22):

1. **AST** (`test_architecture.py`):
   - `test_inv016_scheduler_call_sites` — `scheduler.py` PHẢI chứa literal `acquire_slot_wait(` VÀ `release_slot(` (đi qua public API ResourceService — không thể bypass mà không sửa source); `execution_runner.py` PHẢI chứa literal `execution_service.execute(` (public API ExecutionService — không gọi `_run`/`_run_node`)
   - `test_inv016_scheduler_no_private_access` — scan AST toàn `kernel/scheduler/*.py`: KHÔNG có `ast.Attribute` nào có `attr` bắt đầu `_` với `value` là `Name` (không phải `self`) — chặn `resource_service._running`, `svc._queue`, `execution._run_node`, `state._states`... (loại trừ `self._x` — nội bộ)
   - `test_inv016_scheduler_no_god_object` — `kernel/scheduler/*` KHÔNG chứa `ThreadPoolExecutor` (execution threads thuộc GraphExecutor — scheduler không tự thực thi) + `scheduler.py` KHÔNG chứa `def execute(` (API là `schedule`/`schedule_plan` — không duplicate wave loop) + `execution_runner.py` KHÔNG chứa `def schedule(`
   - `test_inv016_scheduler_import_allowlist` — §5.2 + **pin execution isolation**: `dir_imports(kernel/scheduler, ["aios_core.kernel.services.execution", "aios_core.kernel.execution_plan"], exclude=["aios_core/kernel/scheduler/execution_runner"]) == []` — chỉ execution_runner.py được import execution/execution_plan
   - `test_inv016_graph_no_scheduler` — `kernel/graph/` KHÔNG import `aios_core.kernel.scheduler` (chiều duy nhất scheduler → graph; chống cycle)
   - `test_inv016_planning_no_scheduler` — `orchestrator/planning/` KHÔNG import `aios_core.kernel.scheduler` (pattern `test_inv015_planning_no_graph`)
2. **Behavioral** (`test_parallel_scheduler.py`):
   - Duck-typed stub resource (không kế thừa ResourceService) chạy được — phụ thuộc API-level
   - Spy wrapper ghi call sequence → A→B single slot: `acquire_slot_wait(A)→release_slot(A)→acquire_slot_wait(B)→release_slot(B)` (đúng thứ tự, chỉ public methods)
   - Runner raise / timeout → `release_slot` không gọi khi chưa acquired (stats không lệch âm)

### 5.4 Deterministic first (PLAN §13, §23)
- Scheduling order cố định: READY set id asc + submit id asc (GraphExecutor 027 có sẵn — 028 không đổi); gate FIFO qua `acquire_slot_wait` (F-003 queue pop(0))
- Không random, không LLM, không network
- **Giới hạn determinism (tường minh)**: thứ tự *đến queue* giữa các node cùng wave phụ thuộc thread scheduling (CPython GIL) → KHÔNG đảm bảo node nào chờ trước; nhưng same-wave nodes độc lập (không dependency nhau) → **outcome deterministic** (statuses/order/results); test aggregate invariants (≤ max_concurrent đồng thời, peak, mọi node SUCCEEDED) + kịch bản single-slot deterministic (A→B→C) + spy sequence (A→B)
- Cùng input 2 lần → `ScheduledGraphResult` (trừ timing fields `resource_wait_ms`/`queue_time_ms`/`latency_ms` — pattern 027 AC12) y hệt (test)

### 5.5 Additive only
- `git diff` sau implement: `kernel/services/execution.py`, `kernel/services/resource.py`, `kernel/services/scheduler.py`, `kernel/services/state.py`, `kernel/graph/*`, `kernel/execution_plan.py`, `kernel/dag.py`, `orchestrator/planning/*` **không đổi**
- MOD (chỉ THÊM, không đổi hành vi cũ): `config.py` (+`SchedulerSettings` + field `scheduler`), `config.yaml` (block scheduler), `runtime_kernel.py` (block wiring cuối), `tests/*` (additive)
- Mọi test cũ pass không sửa (baseline 1055 — TASK-027 evaluation)

### 5.6 Quyết định thiết kế (mở — cho critic phản biện)
- **Wrap vs thay wave loop**: 028 chọn **wrap** (`GraphExecutor.execute` + gated runner). Lý do: dependency logic (dead-end/policy/cancel/retries/READY persist/no-progress guard) ~200 dòng 027 đã test kỹ — duplicate = 2 nguồn sự thật + God Object; runner injectable chính là injection point 027 để dành cho 028 (evaluation 027). Critic: có nên scheduler tự wave để gate theo wave (acquire trước submit) cho determinism tuyệt đối? — chi phí: duplicate toàn bộ dependency machinery
- **Block (acquire_slot_wait) vs queue riêng non-blocking**: 028 chọn **block qua FIFO sẵn có** (F-003 — queue + pending() + fairness) — zero code mới, semantic "chờ resource" đúng nghĩa. Critic: nên non-blocking + retry-wave để scheduler giữ determinism tuyệt đối của thứ tự acquire?
- **RUNNING-while-waiting**: node chờ resource hiển thị RUNNING trong graph state (worker 027 đã READY→RUNNING trước khi gọi runner — hành vi có sẵn, không sửa). Phân biệt qua `node_metrics.resource_wait_ms`. Critic: có nên thêm trạng thái WAITING (phá 8-state PLAN §17)?
- **ExecutionServiceRunner envelope v1**: adapter chạy qua public API (policy per node PLAN §20 + events + state) nhưng real capability execution vẫn caller-injected (inner). Critic: nên defer hẳn adapter sang task sau (M5 DoD chỉ cần "Scheduler không sở hữu Resource/Execution")?
- **Double slot counting**: khi dùng ExecutionServiceRunner + `resources.max_concurrent` hữu hạn → mỗi node tiêu 2 slot (gate + ExecutionService internal acquire) — giả định tường minh §7; mitigation: caller dùng runner thuần / chấp nhận conservative / đề xuất additive `execute_node` ở task sau
- **SchedulerSettings 1 field**: chỉ `resource_wait_timeout_s`. Critic: có nên thêm `enable_slot_gate: bool` (tắt gate khi không cần)?
- **scheduler_metrics key riêng**: tránh clobber `metrics` của graph (027 last-write-wins). Critic: nên merge vào `metrics` thay vì key riêng?

## 6. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — `NodeResourceMetrics`/`ScheduledGraphResult` pydantic `extra="forbid"`; `ScheduledGraphResult` wrap `GraphResult` 027 (không MOD GraphResult); `SchedulerError`/`ResourceUnavailableError`/`ExecutionNodeError` hierarchy đúng (YC-1, YC-2)
- [ ] **AC2**: **Resource gate** — `max_concurrent=1`, `A→B→C`: `execution_order == ["A","B","C"]`, runner B chỉ start sau A finish (barrier + event); release an toàn (`stats()["running"] == 0`, `pending() == 0` sau chạy) (YC-3)
- [ ] **AC3**: **Parallelism bounded** — `max_concurrent=2`, `A→{B,C,D}` (3 ready): ≤ 2 runner đồng thời tại mọi thời điểm (barrier + counter), mọi node SUCCEEDED, `peak_slots_used == 2`, `execution_order == ["A","B","C","D"]` (YC-3)
- [ ] **AC4**: **Queue + metrics** — trong lúc chờ: `pending() >= 1`; sau: `pending() == 0`; `resource_wait_ms`/`queue_time_ms`/`peak_slots_used`/`resource_stats` đúng giá trị kỳ vọng; state persist key `scheduler_metrics` không đè `metrics` của graph (YC-3)
- [ ] **AC5**: **Timeout** — `resource_wait_timeout_s=0.05`, slot bị giữ → node FAILED (reason chứa "timeout"), graph FAILED (FAIL_FAST → node còn lại BLOCKED), không release khi chưa acquired (YC-3)
- [ ] **AC6**: **PLAN §23** — `test_plan23_a_to_b_to_c_via_scheduler` (`["A","B","C"]`) + `test_plan23_a_to_b_a_to_c_bc_to_d_via_scheduler` (`["A","B","C","D"]`) qua `schedule_plan`; `failure_policy=CONTINUE` override hoạt động (YC-6, YC-3)
- [ ] **AC7**: **schedule_plan + ranh giới 027** — `plan_to_graph` được tiêu thụ đúng (`default_failure_policy` từ settings tại call-site); plan cycle → `GraphValidationError` từ converter (không duplicate INV-015); GraphExecutor/plan_to_graph KHÔNG đổi (YC-3)
- [ ] **AC8**: **ExecutionServiceRunner** — spy ExecutionService: nhận đúng 1-node plan (`id == f"gnode:{node.id}"`, `depends_on == []`, capabilities/retries/timeout giữ); COMPLETED → result map; FAILED → `ExecutionNodeError` (reason giữ); inner None → noop; e2e qua `RuntimeKernel.create()` 3 node SUCCEEDED (YC-4)
- [ ] **AC9**: **INV-016 enforcement** — 6 test AST pass (`call_sites`: `acquire_slot_wait(`+`release_slot(` trong scheduler.py, `execution_service.execute(` trong execution_runner.py; `no_private_access`; `no_god_object` — không `ThreadPoolExecutor`, không `def execute(`; `import_allowlist` + execution isolation chỉ execution_runner.py; `graph_no_scheduler`; `planning_no_scheduler`) + behavioral (duck-typed stub chạy; spy sequence `acquire(A)→release(A)→acquire(B)→release(B)`) (§5.2, §5.3)
- [ ] **AC10**: **Wiring + config** — `container.resolve(GraphScheduler)` trả instance; `_resources`/`_state`/`_executor` là shared instances với ExecutionService/GraphExecutor; Settings parse block `scheduler` + env override `AIOS_SCHEDULER__RESOURCE_WAIT_TIMEOUT_S=0.5`; `resource_wait_timeout_s` âm → ValidationError (YC-5)
- [ ] **AC11**: **Additive only** — `git diff`: execution.py/resource.py/scheduler.py/state.py/graph/*/execution_plan.py/dag.py/planning/* không đổi; MOD chỉ thêm (config/config.yaml/runtime_kernel/tests); allow-list graph 027 (`test_inv_graph_import_allowlist`) vẫn pass không sửa (§5.5)
- [ ] **AC12**: **Deterministic + suite** — cùng input 2 lần → `ScheduledGraphResult` (trừ timing fields) y hệt; **full pytest pass (baseline 1055 + test mới ≥ ~35)**, coverage ≥ 95% mục tiêu (hard ≥ 80%) (YC-3, §5.4)

## 7. Rủi ro & giả định

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Thứ tự đến FIFO queue giữa node cùng wave không deterministic (thread scheduling) | Tường minh §5.4: same-wave nodes độc lập → outcome deterministic; test aggregate invariants + single-slot/spy deterministic; timing fields loại trừ khỏi determinism claim |
| Node chờ resource hiển thị RUNNING (không có trạng thái WAITING) — observability lệch | Semantic v1 tường minh (§2 Out): phân biệt qua `node_metrics.resource_wait_ms`; thêm trạng thái = phá 8-state PLAN §17 — critic phản biện được |
| Cancel không phá được `acquire_slot_wait(None)` đang chờ (thread bị block vô hạn) | Pattern 027 (in-flight không kill): cancel = flag; node chờ sẽ FAILED khi timeout. Mitigation: đặt `resource_wait_timeout_s` hữu hạn khi cần cancel-chịu-lỗi; test timeout + cancel riêng |
| Double slot counting khi `ExecutionServiceRunner` + `resources.max_concurrent` hữu hạn (gate + ExecutionService internal acquire) | Giả định tường minh §5.6: chấp nhận conservative v1; caller dùng runner thuần khi cần chính xác; đề xuất additive `ExecutionService.execute_node` (không acquire) ở task sau |
| Policy per node thiếu nguồn dữ liệu (plan contract chưa có per-node `required_permissions` — 027 chỉ copy plan-level vào `graph.metadata`) | Adapter nhận `permissions` qua constructor (caller-side composition); per-node field = đề xuất additive task sau |
| Nhầm lẫn `kernel/scheduler/` (GraphScheduler 028) vs `kernel/services/scheduler.py` (SchedulerService kỹ thuật) | Package boundary + docstring rõ; allow-list CẤM `kernel.services.scheduler` trong kernel/scheduler/ (test bắt); SchedulerService kỹ thuật không đổi (git diff) |
| Timeout gate → release nhầm (release slot chưa acquire — lệch âm `_running`) | `acquired` flag + `finally: if acquired: release_slot()`; test: timeout → `stats()["running"] == 0` và `pending() == 0` (AC2/AC5) |
| `scheduler_metrics` clobber `metrics` của graph (cùng key, last-write-wins) | Key riêng `scheduler_metrics` (test AC4 bắt: sau chạy state có CẢ `metrics` (graph) VÀ `scheduler_metrics`) |
| `resolve(ResourceService)`/`resolve(StateService)`/`resolve(GraphExecutor)` không trả shared instances | Wiring note (pattern 027): container cache singleton — test AC10 bắt; nếu không cache → implementer tạo instance duy nhất truyền cho cả 2 |
| 028 bị coi là scope creep (027 đã có max_parallel) | Value-add tường minh §1: resource-aware (tôn trọng max_concurrent toàn hệ thống — 027 chỉ giới hạn nội bộ), metrics queue/resource usage (PLAN §25 DoD), INV-016 enforced, cầu nối ExecutionService — 027 evaluation đề xuất chính các điểm này |

**Giả định**:
- Scheduler gate v1 = concurrency slot duy nhất (1 slot/node); token gating nằm trong ExecutionService (khi dùng adapter); resource types động = task sau
- Runner vẫn caller-injected (tool dispatch/agent dispatch — như 027); 028 KHÔNG tự biết cách chạy capability thật (đó là Execution Plane — INV-001/002)
- `ScheduledGraphResult` + state `scheduler_metrics` là nguồn observability v1 (không emit event mới — EventType giữ nguyên)
- Node chờ resource = RUNNING (semantic v1, xem bảng trên); `resource_wait_ms` phân biệt chờ vs chạy
- Same-wave nodes độc lập (dependency-free) — bất biến từ graph validation 027 (cycle/unknown dep bị chặn từ build)
- `resource_wait_timeout_s=None` (mặc định) = chờ vô hạn, FIFO fair; hữu hạn khi cần chặn hang/cancel
- Scheduling deterministic tuyệt đối về outcome; timing fields (wait/latency) là ngoại lệ đo lường (pattern 027 AC12)
- M5 close-out: sau 028 `done` → tổng hợp `aios/progress/STATS.md` + đối chiếu DoD M5 (PLAN §25) — việc của orchestrator, không nằm trong scope implement 028

## 8. Expected artifacts

| File | Loại | Nội dung |
|------|------|----------|
| `backend/src/aios_core/kernel/scheduler/contracts.py` | NEW | `NodeResourceMetrics` + `ScheduledGraphResult` (wrap `GraphResult` 027) — pydantic `extra="forbid"` |
| `backend/src/aios_core/kernel/scheduler/errors.py` | NEW | `SchedulerError` + `ResourceUnavailableError` + `ExecutionNodeError` |
| `backend/src/aios_core/kernel/scheduler/scheduler.py` | NEW | `GraphScheduler` — `schedule()` (gated runner: acquire_slot_wait → execute → release, finally-safe) + `schedule_plan()` (plan_to_graph + schedule) + metrics + state persist `scheduler_metrics` — import tuyệt đối toàn bộ |
| `backend/src/aios_core/kernel/scheduler/execution_runner.py` | NEW | `ExecutionServiceRunner` — adapter 1-node plan qua `execution_service.execute` (public API — INV-016); `permissions/tokens/inner` constructor params |
| `backend/src/aios_core/kernel/scheduler/__init__.py` | NEW | Re-export (GraphScheduler/ScheduledGraphResult/NodeResourceMetrics/ExecutionServiceRunner/SchedulerError...) |
| `backend/src/aios_core/config.py` | MOD | `SchedulerSettings` (`extra="forbid"`: `resource_wait_timeout_s` ≥ 0 hoặc None) + `Settings.scheduler` (additive) |
| `backend/config.yaml` | MOD | Block `scheduler` (`resource_wait_timeout_s: null`) |
| `backend/src/aios_core/kernel/runtime_kernel.py` | MOD | Wiring block `GraphScheduler` cuối `create()` (additive — shared ResourceService/StateService/GraphExecutor) |
| `backend/tests/test_parallel_scheduler.py` | NEW | Unit (gate serial/parallel/timeout/metrics/schedule_plan) + INV-016 behavioral (duck-typed stub, spy sequence) + integration (adapter + RuntimeKernel e2e) + PLAN §23 2 test đúng tên + determinism |
| `backend/tests/test_architecture.py` | MOD | `test_inv016_scheduler_import_allowlist` + `test_inv016_scheduler_call_sites` + `test_inv016_scheduler_no_private_access` + `test_inv016_scheduler_no_god_object` + `test_inv016_graph_no_scheduler` + `test_inv016_planning_no_scheduler` |
| `backend/tests/test_config.py` | MOD | Settings parse block `scheduler` + env override + validator âm (additive) |
| `backend/tests/test_runtime_kernel.py` | MOD | `test_graph_scheduler_wired` (additive — pattern `test_graph_executor_wired` + shared instances) |
| `aios/progress/tasks/TASK-028/` | — | critique-1/2, tasks.md, review.md, test.md, evaluation.md (theo workflow gate) |

## 9. Ghi chú thiết kế (cho critic phản biện)

- **kernel/scheduler/ vs extend kernel/graph/**: spec chọn package riêng vì allow-list 027 CẤM sẵn resource/scheduler trong graph/ (MOD invariant vừa dựng = xấu) + 2 trách nhiệm khác nhau (PLAN §19). Critic: có nên đặt `GraphScheduler` trong `kernel/graph/` để gom "execution intelligence" 1 package? — nếu vậy đề xuất cách mở rộng allow-list 027 additive (thêm allowed thay vì bỏ cấm) như thế nào
- **Wrap vs thay wave loop**: spec chọn wrap (`GraphExecutor.execute` + gated runner) — không duplicate dependency machinery 027 (~200 dòng đã test). Critic: scheduler tự wave có xứng đáng để đạt determinism tuyệt đối thứ tự acquire không?
- **Block FIFO vs non-blocking queue riêng**: spec dùng `acquire_slot_wait` (F-003 sẵn có — queue/pending/fairness, zero code mới). Critic: non-blocking + wave-retry giữ determinism thứ tự acquire tốt hơn — chi phí queue riêng + thay đổi semantic chờ?
- **RUNNING-while-waiting**: node chờ resource hiển thị RUNNING (8-state PLAN §17 giữ nguyên; worker 027 đã chuyển READY→RUNNING trước runner). Critic: có nên thêm WAITING (phá 8-state) hay đổi GraphExecutor để persist RUNNING sau gate (MOD 027 — bị cấm additive)?
- **ExecutionServiceRunner envelope v1**: chạy qua public API (policy per node PLAN §20 + events + state) nhưng real execution caller-injected. Critic: defer hẳn adapter (M5 DoD chỉ cần separation) hay giữ — spec giữ vì nó chứng minh chain §19 đầy đủ trong kernel
- **Double slot counting** khi adapter + max_concurrent hữu hạn: chấp nhận conservative v1 hay cần giải pháp (vd scheduler gate chỉ khi runner KHÔNG phải adapter)?
- **SchedulerSettings 1 field** (`resource_wait_timeout_s`): đủ hay thiếu (`enable_slot_gate`?)
- **scheduler_metrics key riêng** vs merge vào `metrics` của graph: key riêng tránh clobber (027 last-write-wins) — critic phản biện nếu muốn 1 metrics block hợp nhất
