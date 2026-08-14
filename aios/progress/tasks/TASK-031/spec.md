# Spec — TASK-031: H3 Test & Simulation (M6)

**Trạng thái**: v3 (resolve critique-2) → implement | **Nguồn**: orchestrator tự soạn (spec-writer không phản hồi — ghi nhận như phiên TASK-025/030)

## 1. Mục tiêu

Kiểm thử AIOS mà không cần side effect thật: **Scenario Definition** (yaml/json, không hard-code) + **Simulation Mode** (Fake Runtime/Fake Tool, deterministic, offline) + **Failure Injection** (Chaos nhẹ: model timeout, tool failure, resource exhausted) — kiểm tra Retry/Fallback/Final state. Chạy qua H1 `HarnessRunner` (INV-017/018), kế thừa `Harness` như H2.

## 2. Phạm vi

- MỚI: `backend/src/aios_core/harness/testing/` — contracts.py, errors.py, scenarios.py, faults.py, simulation.py, testing.py, `__init__.py`
- SỬA (additive): `config.py` (+TestingSettings), `config.yaml` (+testing block), `runtime_kernel.py` (wiring TestHarness), `tests/test_architecture.py` (+`yaml` vào `_HARNESS_ALLOWED_EXTERNAL` + arch tests INV cho testing/), `tests/test_harness_testing.py` (mới)
- KHÔNG sửa Runtime/Orchestrator; KHÔNG MOD `_HARNESS_ALLOWED_AIOS`

## 3. Thiết kế

### 3.1 contracts.py (leaf — chỉ pydantic/typing/enum/datetime)
- `TestLevel(str, Enum)`: UNIT, CONTRACT, ARCHITECTURE, INTEGRATION, WORKFLOW, AGENT, CAPABILITY, TOOL, POLICY, PERMISSION, E2E, REGRESSION (12 loại — PLAN §H3)
- `FaultType(str, Enum)`: TIMEOUT, FAILURE, EXHAUSTED
- `Fault(BaseModel, extra=forbid)`: target: str ("model"|"tool.<name>"|"resource"), type: FaultType, params: dict = {} (retries: int = 1 → **tổng attempts = retries + 1** (C2-04); delay_s: float = 0.0)
- `ExpectedResult(BaseModel, extra=forbid)`: intent: str|None, agent: str|None, policy: str|None ("allow"/"deny" — None → bỏ qua so sánh policy, C2-01), required_capabilities: list[str] = [], tests_pass: bool = True, no_policy_bypass: bool = True
- `Scenario(BaseModel, extra=forbid)`: id: str, level: TestLevel = TestLevel.WORKFLOW, input: dict (request: str bắt buộc), environment: dict = {"mode": "simulation"}, expect: ExpectedResult (**verification nằm trong expect — C2-03**), faults: list[Fault] = [], tags: list[str] = []
- `SimulationOutcome(BaseModel, extra=forbid)`: scenario_id, status: SimulationStatus(SUCCESS/MISMATCH/ERROR — **bỏ BLOCKED, P1-02**), intent/agent/policy resolved (str|None), executed_nodes: list[str] (**append trước attempt đầu mỗi node — P1-03**), tool_calls: list[dict] (**mọi attempt kể cả fail; cap 100 — C2-06**), faults_injected: list[dict], recovery_events: list[dict], expectation_matches: dict[str, bool], verification: dict[str, bool], summary: str, metrics: dict (**chỉ counts — C1-04**: nodes/tool_calls/faults/recovery, KHÔNG duration/timestamp)
- `SimulationStatus(str, Enum)`: SUCCESS, MISMATCH, ERROR (**ERROR = fault không recover/runner exception; MISMATCH = expectation lệch — C3-01**)

### 3.2 errors.py
- `ScenarioError(Exception)`, `SimulationError(Exception)`, `TestError(Exception)`

### 3.3 scenarios.py — ScenarioLoader
- `load(scenario: dict | str | Path) -> Scenario`: dict → validate; file path → json hoặc yaml → validate
- `load_many(source) -> list[Scenario]`: file chứa list hoặc key `scenarios:` (C3-04 — hỗ trợ cả 2)
- Lỗi parse/validate → `ScenarioError` (kèm context id/file)
- **PyYAML bắt buộc `safe_load`** (C2-07)
- KHÔNG import os (C1-03)

### 3.4 faults.py — FaultInjector
- `FaultInjector(faults: list[Fault], *, retry_ok: bool = True)` — stateful (đếm lần inject per target), đơn luồng (C3-05)
- `next_for(target: str) -> Fault | None` — fault còn attempts cho target
- `apply(target, call_fn, ctx) -> (result, recovery_events)` — gọi call_fn với fault semantics:
  - TIMEOUT: raise TimeoutError lần đầu → gọi lại (retry) → ghi "retry" (nếu hết attempts → raise → ERROR)
  - FAILURE: raise RuntimeError lần đầu → fallback result `{"ok": False, "error": ...}` → ghi "fallback" (hết attempts → raise)
  - EXHAUSTED: raise ResourceExhaustedError lần đầu → delay_s → retry → ghi "queued" (hết attempts → raise)
- Deterministic: sequence cố định theo (target, lần gọi)

### 3.5 simulation.py — Fake Runtime + Fake Tool + Runner (KHÔNG side effect)
- `FakeRuntime`: detectors injectable, defaults keyword-based (C3-02):
  - `intent(request) -> str`: injectable; default keyword map deterministic: review→coding, fix→coding, write→writing, summarize→writing, test→testing, plan→planning, khác→general
  - `resolve_agent(intent) -> str`: default coding→coder, testing→coder, writing→writer, planning→generalist, general→generalist
  - `check_policy(request, intent) -> str`: default "allow"
  - `capabilities(agent) -> list[str]`: default coder→[filesystem, python], writer→[filesystem], generalist→[filesystem]
- `FakeTool(name, *, behavior: dict | None = None)`: `run(input) -> dict` deterministic (ghi last_call); behavior mặc định `{"ok": True}`
- `SimulationRunner(runtime, ...)` (thuần — C3-06, không state):
  - `run(scenario) -> SimulationOutcome`:
    1. intent = runtime.intent(request); agent = runtime.resolve_agent(intent); policy = runtime.check_policy(...)
    2. **policy == "deny" → không chạy tool nào (C2-02: tool_calls rỗng)**: expect.policy == "deny" → SUCCESS (summary "blocked-as-expected"); expect.policy == "allow" hoặc None → MISMATCH (P1-02); no_policy_bypass = (tool_calls == [])
    3. plan fake: node `model` đầu tiên (**luôn thêm — C1-02: fault target model luôn có chỗ inject**) + `capability:{c}` cho từng required_capabilities
    4. chạy tuần tự: mỗi node → FakeTool tự dựng (`tool:{capability}` — C1-01); **fault target "resource" inject tại node ĐẦU (model) — P1-01**; FaultInjector áp theo target match ("tool.{capability}", "model", "resource"); **executed_nodes append trước attempt đầu; tool_calls ghi mọi attempt (P1-03)** — shape {node, tool, input, ok, status, attempt} (P3-03)
    5. expectation_matches: intent/agent/policy (nếu expect.policy != None — C2-01)/required_capabilities (subset của resolved)
    6. verification: tests_pass = (mọi node output ok) ∧ (có fault → recovery thành công, không fault → True) (P2-03); no_policy_bypass = deny ⇒ tool_calls rỗng (C2-02)
    7. status: SUCCESS (mọi match) / MISMATCH (có mismatch) / ERROR (fault không recover hoặc runner exception — C3-01)
- Không import sqlite3/httpx/socket/requests/os (INV-020b)

### 3.6 testing.py — TestHarness (H1 kế thừa, pattern H2)
- `TestHarness(SimulationRunner, *, state_service=None)` — id="test", name="Test & Simulation", version="1.0.0"
- `run(ctx)`: scenario = ctx.config["scenario"] (Scenario); runner = ctx.config.get("runtime") override nếu có (P2-01); outcome = runner.run(scenario); ctx.config["_outcome"] = outcome; return outcome.model_dump()
- `verify(ctx, payload)`: outcome từ config; **persist TRƯỚC raise** (pattern H2 AC5 — P2-02 confirm: key "testing" sống sót qua H1 _persist): state.update_state(run_id, testing={"scenario_id", "status", "matches", "summary", "metrics", "tool_calls": capped 100, "faults_injected", "recovery_events", "strict"})
  - status MISMATCH/ERROR → raise TestError (trừ ctx.config.get("strict", False) == False → summary prefix "WARNING:" — C2-05/P2-04)
- `get_outcome(run_id)` — trả dict compact từ state (P3-05)

### 3.7 Wiring + config
- `TestingSettings(BaseModel, extra=forbid)`: `default_retries: int = 1`, `strict: bool = True`, `simulation_timeout_s: float = 30.0` (reserved — runner không block, chốt v1)
- config.yaml: `testing:` block
- runtime_kernel: sau H2 — `TestHarness(SimulationRunner(FakeRuntime()), state_service=resolve(StateService))` + `harness_registry.register(test_harness)` + register_instance

## 4. Invariants (arch tests mới trong test_architecture.py)
- **INV-020a**: testing/ không import `kernel.services.execution|events|resource|scheduler` + `kernel.graph|orchestrator.planning` (simulation dùng fake, duck-typed)
- **INV-020b**: simulation.py/testing.py không chứa import `sqlite3|httpx|socket|requests|os` (không side effect — AST literal)
- **INV-020c**: testing.py chứa literal `SimulationRunner(` + `TestError(` (behavioral: chạy qua runner, fail → raise)
- **INV-020d**: `_HARNESS_ALLOWED_EXTERNAL` + `yaml` (additive — scenarios loader)

## 5. Tiêu chí chấp nhận (AC)
| AC | Mô tả | Kiểm chứng |
|----|-------|-----------|
| AC1 | Contracts: TestLevel 12, Scenario, ExpectedResult, Fault/FaultType, SimulationOutcome/Status — extra=forbid | unit test |
| AC2 | ScenarioLoader: dict + json + yaml (safe_load); lỗi → ScenarioError | unit test |
| AC3 | FaultInjector: 3 loại fault, attempts=retries+1 (P3-02: default từ TestingSettings.default_retries), recovery events | unit test |
| AC4 | FakeRuntime: injectable detectors + defaults; không side effect | unit test |
| AC5 | FakeTool deterministic, ghi call | unit test |
| AC6 | SimulationRunner pipeline đầy đủ; outcome khớp expect; node model luôn chạy | unit test |
| AC7 | Policy deny → không tool call, no_policy_bypass true; expect deny → SUCCESS blocked-as-expected; expect allow/None → MISMATCH | unit test |
| AC8 | Mismatch → MISMATCH (không raise ở runner) | unit test |
| AC9 | TestHarness qua H1 runner: run+verify; strict raise TestError; persist trước raise; get_outcome | unit + integration |
| AC10 | Fault scenario: recovery thành công + node ok → tests_pass true; hết attempts → ERROR; resource fault tại node đầu | unit test |
| AC11 | Config + wiring runtime_kernel register "test" | unit test |
| AC12 | Arch tests INV-020a..d; **tổng ≥1290 tests (baseline 1210 + ≥80), coverage ≥90%** | full suite |

## 6. Không làm (out of scope)
- KHÔNG thay pytest/vitest; KHÔNG gọi Orchestrator/Planner/ExecutionService thật (fake hoàn toàn — deterministic)
- KHÔNG E2E thật, KHÔNG network, KHÔNG disk I/O trong simulation (persist chỉ qua H1 runner)
- Golden Scenario registry (GS-001..020) — TASK-033/034

