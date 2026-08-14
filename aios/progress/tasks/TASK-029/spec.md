# TASK-029 — Harness Kernel (M6-P11, H1 — task ĐẦU TIÊN M6)

**Metadata**: TASK-029 | M6/P11 | 2026-08-15 | v3 (critique-1 + critique-2 resolved) | AIOS Orchestrator
**Tiền đề**: M5 đã `done` (1086 tests, coverage 95.22% — TASK-028 evaluation). M6 chưa có task nào; TASK-029 là nền tảng H1 cho TASK-030..034 (H2 Execution Verification, H3 Test & Simulation, H4 Evaluation & Benchmark, H5 Doctor & Readiness).
**Module đích**: `backend/src/aios_core/harness/` (subpackage MỚI — 7 file flat) + `config.py`/`config.yaml` (MOD additive: block `harness`) + `kernel/runtime_kernel.py` (MOD additive: wiring cuối `create()`) + `tests/` (NEW `test_harness_kernel.py` + MOD `test_architecture.py` + MOD `test_config.py` + MOD `test_runtime_kernel.py`)

## 1. Mục tiêu

Trả lời câu hỏi M6 (PLAN §M6-2): ***"AIOS có tự kiểm chứng được không?"*** — bắt đầu bằng nền tảng chung cho mọi Harness H2–H5:

> Harness → Context · Run · Event · Result · Artifact · Report

- **H1 Harness Kernel** cung cấp **contract chung + lifecycle + registry + runner** để **không một Harness nào (Test/Eval/Doctor/Verification) tự tạo logger/trace/result/artifact/config/lifecycle riêng** (PLAN §M6-2).
- **INV-017 Harness Isolation** (PLAN §M6-9): `harness/` chỉ import public API (config, kernel services state/artifacts, contracts.artifact) — **KHÔNG chui** `kernel/services/execution|resource|scheduler|policy|permissions|context` implementation; enforced bằng AST allow-list + test (pattern INV-015/016 của TASK-027/028).
- **INV-018 Evidence First** (PLAN §M6-9): **mọi Harness Run — thành công LẪN thất bại — tự động tạo evidence truy xuất được** (ít nhất 2 `HarnessArtifact`: `events` + `report`), lưu qua ArtifactService (M1 — tái dùng, không tạo hệ thống song song).
- **HarnessRun** là hạt nhân truy ngược `Release → Harness Run → Execution Trace → Evaluation → Failure` (PLAN §M6-2): mỗi run có `run_id, harness, target, version, environment, started_at, status`.
- Wiring: `RuntimeKernel.create()` đăng ký `HarnessRegistry` + `HarnessRunner` vào container (additive — **KHÔNG sửa service cũ**, không đổi hành vi M1–M5).

## 2. Quyết định vị trí package (QUAN TRỌNG — lệch PLAN, cần critic phản biện)

**PLAN §M6-2** ghi cấu trúc `aios/harness/` (monorepo root): `contracts/` (harness, run, result, assertion, report) · `kernel/` (runner, registry, lifecycle, context) · `execution/` · `testing/` · `evaluation/` · `doctor/`.

**Quyết định TASK-029**: đặt tại **`backend/src/aios_core/harness/`** — subpackage flat 7 file: `contracts.py`, `context.py`, `lifecycle.py`, `registry.py`, `runner.py`, `errors.py`, `__init__.py`.

Lý do (bài học TASK-002 scaffold + TASK-016 arch scan + TASK-027/028 package convention):
1. **Toàn bộ Python codebase nằm trong `backend/src/aios_core/`** — một Python root duy nhất: packaging (pyproject/hatchling), import runtime, pytest, coverage, và đặc biệt **`observability/arch_scan.py` giả định `SRC_ROOT = parents[2] = backend/src`** (allow-list scan chỉ quét dưới SRC_ROOT). Tạo `aios/harness/` ở monorepo root = Python root thứ 2, phá mọi công cụ trên.
2. **Convention package hiện có là subpackage flat** (không lồng `contracts/`+`kernel/`): `kernel/graph/` (7 file flat), `kernel/scheduler/` (4 file flat) — không có tiền lệ lồng 2 cấp dirs trong codebase; giữ convention giảm chi phí review + scan.
3. **H2–H5 (TASK-030..034) sẽ theo cùng vị trí**: `harness/execution/`, `harness/testing/`, `harness/evaluation/`, `harness/doctor/` — gọn dưới 1 package, allow-list phủ cả cây.
- Phương án thay thế (cho critic): (a) `aios/harness/` root như PLAN — đúng chữ PLAN nhưng phá packaging/arch-scan — **loại**; (b) `backend/src/aios_core/harness/contracts/` + `harness/kernel/` 2 cấp như PLAN — giữ cấu trúc PLAN nhưng lệch convention codebase + scan phức tạp hơn — **cân nhắc**, spec chọn flat (7 file, quyết định D1).

## 3. Phạm vi

**In**:
- `harness/` — NEW subpackage: `contracts.py`, `context.py`, `lifecycle.py`, `registry.py`, `runner.py`, `errors.py`, `__init__.py`
- `config.py` — MOD (additive): `HarnessSettings` (pydantic `extra="forbid"`) + `Settings.harness`
- `config.yaml` — MOD (additive): block `harness`
- `kernel/runtime_kernel.py` — MOD (additive): wiring block `HarnessRegistry` + `HarnessRunner` (CUỐI `create()` — sau block GraphScheduler 028)
- `tests/test_harness_kernel.py` — NEW: unit (contracts/lifecycle/registry/runner) + INV-017 behavioral + INV-018 behavioral + integration (RuntimeKernel e2e) + determinism
- `tests/test_architecture.py` — MOD (additive): `test_inv017_harness_import_allowlist` + `test_inv017_harness_no_kernel_impl` + `test_inv017_harness_no_god_object` + `test_inv017_harness_call_sites` + `test_inv017_harness_no_private_access` + `test_inv017_no_harness_in_kernel` + `test_inv018_runner_builds_evidence`
- `tests/test_config.py` — MOD (additive): Settings parse block `harness` + env override + extra=forbid
- `tests/test_runtime_kernel.py` — MOD (additive): `test_harness_wired` (pattern `test_graph_scheduler_wired`)

**Out (không làm — tránh scope creep)**:
- **KHÔNG sửa** `kernel/services/*` (state/events/artifacts/execution/resource/scheduler/policy/permissions/context), `kernel/events.py` (EventBus + EventType — **không thêm EventType mới v1**), `kernel/graph/*`, `kernel/scheduler/*`, `orchestrator/*`, `observability/*` — harness/ chỉ GỌI qua public API; git diff các thư mục này phải sạch
- **KHÔNG làm Harness API/CLI** (`POST /api/v1/harness/run`, `aiagent harness ...` — PLAN §M6-8) — thuộc task sau (H2/H3 wiring API); TASK-029 chỉ cung cấp kernel gọi được từ Python
- **KHÔNG làm Verification contract/verdict** (Preconditions/Postconditions/Verdict PASS·FAIL·INCONCLUSIVE — PLAN §M6-3) — TASK-030; hook `verify()` v1 chỉ raise-or-pass (INV-019 thuộc 030)
- **KHÔNG làm Test levels / Scenario / Simulation** (PLAN §M6-4) — TASK-031
- **KHÔNG làm Evaluation/Benchmark** (metrics, thresholds, regression gate — PLAN §M6-5) — TASK-032/033; `HarnessResult.metrics` v1 chỉ ghi `duration_ms` + `phase_count`
- **KHÔNG làm Doctor/Readiness** (PLAN §M6-6) — TASK-034
- **KHÔNG mở rộng EventType** (`kernel/events.py`) — harness events nội bộ qua sink (HarnessEvent), không chạm M1 core; nối EventBus = việc của task API sau
- **KHÔNG import `aios_core.orchestrator.*` / `observability.*` / `models.*` / `memory.*`** trong `harness/` (kể cả TYPE_CHECKING) — H1 là nền cho H2–H5, chiều phụ thuộc ngược (H4 dùng H1), không bao giờ H1 dùng H4; allow-list §6.1
- **KHÔNG**: LLM/random/network trong lifecycle/registry/runner (deterministic tuyệt đối — trừ run_id uuid + timestamp), persistence DB riêng (StateService + ArtifactService sẵn có), replay (TASK-030), failure injection (TASK-031)

## 4. Input / Output

- **Input**:
  - `Harness` instance (ABC — hooks prepare/validate/run/verify/complete/on_failure/diagnose) HOẶC `harness_id: str` (runner resolve qua registry)
  - `HarnessContext` (runner tạo qua `create_context()` — caller cung cấp target/version/environment/config/run_id)
  - `HarnessSettings` (config: `diagnose_on_failure`)
  - `StateService` (inject — **cùng instance** với kernel; persist run/result/artifact refs dưới key `harness:{run_id}`)
  - `ArtifactService` (inject — **cùng instance** M1; lưu evidence file + sidecar checksum + emit `ARTIFACT_CREATED`)
- **Output**:
- **Output**:
- `HarnessRunner.execute(harness, context) -> HarnessReport` — chạy lifecycle đầy đủ, trả report gồm run/result/artifacts; **evidence build nằm trong `finally` (C1-03 — on_failure/diagnose raise vẫn tạo đủ artifact — bọc try/except log warning)**; **catch-all exception NGOÀI hook → run FAILED (transition từ phase hiện tại — CREATED:{FAILED} — B1) + run.error**; **lỗi trong finally (store fail) → log warning + trả report in-memory (path/ref None) — B1**; duplicate run_id trên cùng runner → `HarnessError` (C2-03); **collector sink attach ĐẦU execute (re-attach idempotent — C3-06 v2: evidence không phụ thuộc ai tạo ctx)**
- `HarnessRunner.get_run(run_id) -> HarnessRun | None` · `get_result(run_id) -> HarnessResult | None` · `get_evidence(run_id) -> list[HarnessArtifact]` — truy xuất sau run (INV-018); **run_id không tồn tại → `[]` (B8)**; **sau restart: get_run/get_result → None, get_evidence → fallback `ArtifactService.list(JSON)` lọc `metadata.run_id` reconstruct từ sidecar (B3)**
- Evidence tự động trên disk: `{artifacts.dir}/harness/{safe_run_id}/events.json` + `.../report.json` — **safe_run_id = regex `[\\/:*?"<>|]` → `_` (B4: sanitize toàn bộ ký tự bất hợp lệ Windows)**; encode UTF-8 (B11)
- State persist: `update_state(run_id, run=..., result=..., artifacts=...)` — **key = run_id TRỰC TIẾP (C3-02: run_id đã có prefix `harness:`, không double-prefix)**

## 5. Yêu cầu chức năng

### YC-1 — Contracts (`harness/contracts.py`, pydantic `extra="forbid"` — leaf, không import gì ngoài pydantic/typing/datetime/enum/uuid)
```python
class HarnessRunStatus(str, Enum):
    CREATED = "created"      # run vừa tạo
    PREPARING = "preparing"  # prepare hook
    VALIDATING = "validating"  # validate hook
    RUNNING = "running"      # run hook (execution thật)
    VERIFYING = "verifying"  # verify hook
    COMPLETED = "completed"  # complete hook xong — terminal
    FAILED = "failed"        # lỗi (từ RUNNING/VALIDATING/PREPARING/VERIFYING/COMPLETED — D4 + C1-02) — KHÔNG terminal
    DIAGNOSED = "diagnosed"  # post-mortem xong (on_failure + diagnose) — terminal

class HarnessRun(BaseModel):            # extra="forbid" — PLAN §M6-2 + additive D2
    run_id: str
    harness: str                        # harness id
    target: str                         # đối tượng bị harness (workflow/agent/model/...)
    version: str | None = None          # target version — truy ngược Release → Run
    environment: str = "local"
    started_at: datetime
    status: HarnessRunStatus = HarnessRunStatus.CREATED
    ended_at: datetime | None = None    # D2 (additive): cần cho report/evidence error path
    error: str | None = None            # D2 (additive): message lỗi khi FAILED/DIAGNOSED

class HarnessEvent(BaseModel):          # extra="forbid"
    run_id: str
    phase: str                          # tên phase (HarnessRunStatus.value) đang chuyển tới
    timestamp: datetime
    level: Literal["info", "warning", "error"] = "info"
    message: str

class HarnessResult(BaseModel):         # extra="forbid"
    run_id: str
    status: HarnessRunStatus            # status CUỐI của run (COMPLETED/FAILED/DIAGNOSED)
    summary: str                        # runner tự sinh: f"{harness_id}:{run_id} → {status.value}"
    metrics: dict[str, Any] = {}        # v1: {"duration_ms": int, "phase_count": int} (H4 thêm sau)
    artifacts: list[str] = []           # refs = artifact ids (evidence của run này)

class HarnessArtifact(BaseModel):       # extra="forbid" — evidence (INV-018)
    id: str                             # C2-02: DETERMINISTIC f"{run_id}:{kind}" (không uuid — determinism AC10)
    run_id: str
    kind: str                           # "events" | "report" | (H2+ thêm kind mới)
    path: str | None = None             # storage_path tương đối trong artifact base dir
    ref: str | None = None              # sha256 checksum (ArtifactService trả) — tamper-evident
    created_at: datetime

class HarnessReport(BaseModel):         # extra="forbid"
    run_id: str
    summary: str
    result: HarnessResult
    artifacts: list[HarnessArtifact] = []
    generated_at: datetime
```
- **Test**: mỗi model `extra="forbid"` (field thừa → `ValidationError`); `HarnessRun` defaults (status=CREATED, environment="local"); `HarnessEvent.level` sai giá trị → `ValidationError`; serialization round-trip `model_dump(mode="json")` → `model_validate` → y hệt (trừ datetime tz)

### YC-2 — Errors (`harness/errors.py`, leaf)
```python
class HarnessError(Exception): ...                      # base
class HarnessRegistrationError(HarnessError): ...       # duplicate id / metadata rỗng
class HarnessNotFoundError(HarnessError): ...           # get/require/execute id không tồn tại
class HarnessLifecycleError(HarnessError): ...          # transition không hợp lệ (from → to)
class HarnessHookError(HarnessError): ...               # hook raise — message chứa phase + lý do gốc
```
- **Test**: hierarchy đúng (`issubclass` chain); message giữ nguyên thông tin phase

### YC-3 — Lifecycle (`harness/lifecycle.py` — thuần, deterministic, KHÔNG IO/event/registry)
```python
class HarnessLifecycle:
    TRANSITIONS: dict[HarnessRunStatus, set[HarnessRunStatus]] = {
        CREATED: {PREPARING, FAILED},         # B1: catch-all exception trước phase đầu
        PREPARING: {VALIDATING, FAILED},      # FAILED: extended (D4) — hook prepare fail
        VALIDATING: {RUNNING, FAILED},        # FAILED: extended (D4) — validate fail
        RUNNING: {VERIFYING, FAILED},         # FAILED: đúng PLAN §M6-2
        VERIFYING: {COMPLETED, FAILED},       # FAILED: extended (D4) — verify fail
        COMPLETED: {FAILED},                  # C1-02: complete hook fail → FAILED (nhất quán mọi hook)
        FAILED: {DIAGNOSED},                  # đúng PLAN §M6-2
        DIAGNOSED: set(),                     # terminal
    }
    def can_transition(self, current: HarnessRunStatus, next: HarnessRunStatus) -> bool: ...
    def transition(self, current, next) -> HarnessRunStatus: ...   # invalid → HarnessLifecycleError
    def is_terminal(self, status) -> bool: ...  # {COMPLETED, DIAGNOSED}
```
- **Test**: happy chain `CREATED→PREPARING→VALIDATING→RUNNING→VERIFYING→COMPLETED` pass; error chain `RUNNING→FAILED→DIAGNOSED` pass; MỌI cặp (from,to) ngoài TRANSITIONS → `can_transition` False + `transition` raise `HarnessLifecycleError` (duyệt toàn ma trận 8×8 — deterministic); `is_terminal(COMPLETED)`/`is_terminal(DIAGNOSED)` True, `is_terminal(FAILED)` False (FAILED → DIAGNOSED được)

### YC-4 — HarnessContext (`harness/context.py` — run-scoped)
```python
class HarnessContext(BaseModel):                    # extra="forbid"
    model_config = ConfigDict(extra="forbid")
    run_id: str
    harness: str
    target: str
    version: str | None = None
    environment: str = "local"
    config: dict[str, Any] = {}                     # run-scoped config (không lẫn global settings)
    started_at: datetime
    _sink: Callable[[HarnessEvent], None] | None = PrivateAttr(default=None)  # không serialize
    def attach_sink(self, sink: Callable[[HarnessEvent], None]) -> None: ...  # runner gọi khi tạo
    def emit_event(self, phase: str, message: str, level: Literal["info","warning","error"] = "info") -> HarnessEvent:
        # build event (run_id + timestamp) → sink(event) nếu có → trả event
```
- Sink **không nằm trong serialization** (`PrivateAttr` — `model_dump` không chứa callable; không deep-copy lỗi)
- **Test**: `model_dump(mode="json")` không chứa `_sink`; emit_event trả event đúng run_id/phase/message/level + sink nhận đúng event; chưa attach sink → emit không raise (no-op); extra field → `ValidationError`

### YC-5 — Harness ABC + Registry (`harness/registry.py` — thread-safe, deterministic)
```python
class Harness(ABC):
    """Hooks mặc định no-op — harness con override cái cần."""
    id: str                                   # bắt buộc override (abstract property)
    name: str                                 # bắt buộc
    version: str                              # bắt buộc (non-empty)
    description: str = ""
    tags: list[str] = []
    def prepare(self, ctx: HarnessContext) -> None: ...
    def validate(self, ctx: HarnessContext) -> None: ...      # raise → FAILED
    def run(self, ctx: HarnessContext) -> Any: ...            # trả payload
    def verify(self, ctx: HarnessContext, payload: Any) -> None: ...  # raise → FAILED (verdict = TASK-030)
    def complete(self, ctx: HarnessContext, payload: Any) -> None: ...
    def on_failure(self, ctx: HarnessContext, error: Exception) -> None: ...
    def diagnose(self, ctx: HarnessContext, error: Exception) -> None: ...

class HarnessRegistry:
    def __init__(self) -> None: ...           # _entries: dict[str, Harness] + RLock
    def register(self, harness: Harness) -> None: ...
        # id/name/version rỗng → HarnessRegistrationError; duplicate id → HarnessRegistrationError
    def get(self, harness_id: str) -> Harness | None: ...
    def require(self, harness_id: str) -> Harness: ...        # không có → HarnessNotFoundError
    def list(self) -> list[Harness]: ...      # SORTED theo id — deterministic
    def count(self) -> int: ...
```
- Metadata `register (id/name/version/description/tags)` — đọc từ attrs của Harness instance (KHÔNG tạo HarnessDefinition riêng — giảm contract, quyết định D3)
- **Test**: register/get/require/list/count; duplicate id → `HarnessRegistrationError`; id rỗng → error; get unknown → None; require unknown → `HarnessNotFoundError`; `list()` trả sorted theo id (register thứ tự lộn xộn → list vẫn sorted); **thread-safety**: 8 thread register 8 harness khác nhau → `count() == 8` + get từng cái được; register duplicate đồng thời → đúng 1 lần thành công (không corrupt)

### YC-6 — HarnessRunner (`harness/runner.py` — orchestration + evidence INV-018)
```python
class HarnessRunner:
    def __init__(self, registry: HarnessRegistry, *,
                 state_service=None, artifact_service=None,
                 settings: HarnessSettings | None = None,
                 external_sink: Callable[[HarnessEvent], None] | None = None) -> None:
        # state_service/artifact_service: duck-typed (public API — INV-017); None → chạy evidence-less
        # (vẫn tạo HarnessArtifact in-memory — INV-018) — test stub thuận tiện
        # settings mặc định = HarnessSettings(); external_sink: bridge ra ngoài (vd EventBus) — tùy chọn

    def create_context(self, harness_id: str, target: str, *, version: str | None = None,
                       environment: str = "local", config: dict[str, Any] | None = None,
                       run_id: str | None = None) -> HarnessContext:
        # run_id mặc định = f"harness:{uuid4().hex}"; gắn sink = collector nội bộ (theo run_id) + external_sink

    def execute(self, harness: Harness | str, context: HarnessContext) -> HarnessReport: ...
    def get_run(self, run_id: str) -> HarnessRun | None: ...
    def get_result(self, run_id: str) -> HarnessResult | None: ...
    def get_evidence(self, run_id: str) -> list[HarnessArtifact]: ...
```
- `execute()` flow (synchronous, single-run):
  1. `harness` là str → `registry.require(id)`; context khớp run_id/ctx.harness vs harness.id (lệch → `HarnessError`)
  2. Dựng `run = HarnessRun(run_id, harness.id, target=ctx.target, version=ctx.version, environment=ctx.environment, started_at=ctx.started_at, status=CREATED)`; persist state `harness:{run_id}` (run) — **mỗi lần đổi status đều persist lại**
  3. Vòng lifecycle (mỗi phase emit `HarnessEvent(phase, level="info")` + gọi hook tương ứng):
     ```
     PREPARING  → harness.prepare(ctx)
     VALIDATING → harness.validate(ctx)
     RUNNING    → payload = harness.run(ctx)
     VERIFYING  → harness.verify(ctx, payload)
     COMPLETED  → harness.complete(ctx, payload)
     ```
     - Hook raise → `HarnessHookError(phase=..., lý do gốc)`: emit event `level="error"` → `run.status` → FAILED (qua `lifecycle.transition` từ phase hiện tại — D4 cho phép PREPARING/VALIDATING/VERIFYING → FAILED) → `harness.on_failure(ctx, error)` → nếu `settings.diagnose_on_failure` → `harness.diagnose(ctx, error)` + `transition(FAILED, DIAGNOSED)` → `run.error = str(error)`; `run.ended_at = now`
  4. `result = HarnessResult(run_id, status=run.status, summary=f"{harness.id}:{run_id} → {run.status.value}", metrics={"duration_ms": int((now - started_at).total_seconds()*1000), "phase_count": len(phases đã qua)}, artifacts=[artifact ids])`
  5. **INV-018 — evidence tự động (mọi run kể cả FAILED)**:
     - `events.json`: `ArtifactContract(type=JSON, storage_path=f"harness/{run_id}/events.json", metadata={run_id, kind: "events"})` → `artifact_service.store(contract, json_bytes)` (nội dung = list HarnessEvent `model_dump_json`)
     - `report.json`: tương tự (`kind: "report"` — report HOÀN CHỈNH gồm cả 2 artifact)
     - Dựng `HarnessArtifact(id=uuid, run_id, kind, path=storage_path, ref=checksum từ contract.checksum, created_at)` cho cả 2 — `artifact_service is None` → artifact vẫn được tạo (path=None, ref=None — INV-018 vẫn giữ in-memory)
  6. `report = HarnessReport(run_id, summary=result.summary, result=result, artifacts=[events_artifact, report_artifact], generated_at=now)`
  7. Persist state `harness:{run_id}`: `{run, result, artifacts}`; trả report
- `get_run/get_result/get_evidence` — đọc từ StateService (`get_state(f"harness:{run_id}")` → parse pydantic)
- **KHÔNG chứa**: `def can_transition(`/`def is_terminal(` (dùng lifecycle object), `ThreadPoolExecutor` (sync v1), private-attr access trên service (`_states`, `_entries`...) — §6.2
- **Test (unit — MockHarness ghi call log)**:
  - **Happy path**: call order chính xác `[prepare, validate, run, verify, complete]`; `run` payload truyền đúng vào `verify`/`complete`; events có đủ 5 phase info; statuses qua events = `[preparing, validating, running, verifying, completed]`; result.status=COMPLETED; summary đúng format; `metrics["phase_count"] == 5`, `metrics["duration_ms"] >= 0`; report.artifacts có đúng 2 artifact (kind events + report); state `harness:{run_id}` chứa run/result/artifacts; file trên disk tồn tại qua `artifact_service.list(JSON)` chứa `harness/{run_id}/events.json` + `report.json`; checksum ref = sha256 64 hex
  - **Failure path — validate raise** (`diagnose_on_failure=True`): status cuối DIAGNOSED; events có error level (phase=validating); `on_failure` + `diagnose` được gọi với đúng exception; result.artifacts vẫn đủ 2 (INV-018); run.error chứa message gốc
  - **Failure path — run raise** (`diagnose_on_failure=False`): status cuối FAILED (KHÔNG DIAGNOSED); `diagnose` KHÔNG được gọi; vẫn tạo evidence
  - **execute theo id str**: `execute("mock_harness", ctx)` resolve qua registry; id không có → `HarnessNotFoundError`
  - **Duck-typed stub** (không kế thừa StateService/ArtifactService — chỉ implement public methods `update_state/get_state` + `store/list`) → chạy bình thường — INV-017 behavioral
  - **Harness không override hook nào** (no-op defaults) → run vẫn COMPLETED, payload=None
  - **create_context**: run_id mặc định prefix `harness:`; run_id caller truyền giữ nguyên; config/env/version gắn đúng; emit qua external_sink nhận được (nếu truyền)

### YC-7 — Config + Wiring (additive)
```python
# config.py
class HarnessSettings(BaseModel):
    """TASK-029: AIOS Harness kernel (INV-017/018 bounds)."""
    model_config = ConfigDict(extra="forbid")
    diagnose_on_failure: bool = True   # FAILED → chạy on_failure + diagnose → DIAGNOSED

class Settings(BaseSettings):
    ...
    harness: HarnessSettings = HarnessSettings()
```
- `config.yaml` MOD (additive block): `harness: {diagnose_on_failure: true}`
- `runtime_kernel.create()` — additive block CUỐI (sau block GraphScheduler 028, trước `return cls(container, bus)`):
  ```python
  # AIOS Harness (TASK-029, M6): H1 kernel — registry + runner (INV-017/018).
  # Chỉ gọi public API: StateService/ArtifactService (shared instances M1).
  from ..harness import HarnessRegistry, HarnessRunner

  harness_registry = HarnessRegistry()
  harness_runner = HarnessRunner(
      registry=harness_registry,
      state_service=container.resolve(StateService),     # CÙNG instance kernel
      artifact_service=container.resolve(ArtifactService),  # CÙNG instance M1
      settings=settings.harness,
  )
  container.register_instance(HarnessRegistry, harness_registry)
  container.register_instance(HarnessRunner, harness_runner)
  ```
- **Test**: `RuntimeKernel.create().container.resolve(HarnessRegistry)` + `resolve(HarnessRunner)` trả instance; `runner._state is container.resolve(StateService)` + `runner._artifacts is container.resolve(ArtifactService)` (shared — pattern `test_graph_scheduler_wired`); `runner._settings is settings.harness`; registry ban đầu `count() == 0`; Settings parse block `harness` + env override `AIOS_HARNESS__DIAGNOSE_ON_FAILURE=false`; field thừa trong block → `ValidationError`

## 6. Yêu cầu kiến trúc

### 6.1 Allow-list import `harness/` (test mới `test_inv017_harness_import_allowlist` — loop từng file, pattern `test_inv016_scheduler_import_allowlist`)
- **aios_core allowed (toàn dir)**: `aios_core.config` (HarnessSettings), `aios_core.logging`, `aios_core.kernel.services.state` (StateService), `aios_core.kernel.services.artifacts` (**D1: lưu evidence**, xem §6.7), `aios_core.contracts.artifact` (**D1: ArtifactContract/ArtifactType**) + intra-package `aios_core.harness.*` (loại trừ trong scan); **KHÔNG `kernel.events` v1 (C3-05: chưa dùng — diện tích cho phép = diện tích dùng)**
- **CẤM (kể cả TYPE_CHECKING — bài học TASK-023 C2-01)**: `aios_core.kernel.services.execution|resource|scheduler|policy|permissions|context` (**INV-017 lõi**), `aios_core.kernel.runtime_kernel` (cycle), `aios_core.kernel.graph`/`kernel.scheduler`/`kernel.execution_plan`/`kernel.dag` (H1 không cần), `aios_core.orchestrator.*` (kể cả planning), `aios_core.observability.*` (H1 là nền, KHÔNG import H4/H5 — chiều ngược), `aios_core.models/memory/context/knowledge/tools/agents/capabilities/workflow`
- **external allowed**: `pydantic`, `typing`, `uuid`, `datetime`, `enum`, `threading` (RLock registry), `abc` (Harness ABC), `collections.abc` (Callable), `logging`
- **Import tuyệt đối TOÀN BỘ** (bài học TASK-027: `_resolve_relative` resolve 2-dots từ package 3 cấp SAI — `aios_core/harness/x.py` là package 3 cấp): `from aios_core.kernel.services.state import StateService`, `from aios_core.config import HarnessSettings` — KHÔNG relative import
- Scan toàn dir `harness/*.py` qua `collect_imports`, loại trừ `startswith("aios_core.harness")`; AST đếm mọi Import node kể cả TYPE_CHECKING

### 6.2 INV-017 — Harness Isolation (behavioral + AST enforcement)
Bản chất (PLAN §M6-7/9): *"Harness đọc/quan sát và gọi API, không chui vào implementation của Runtime"*:
1. **AST** (`test_architecture.py`):
   - `test_inv017_harness_import_allowlist` — §6.1
   - `test_inv017_harness_no_kernel_impl` — pin: `dir_imports(harness_dir, ["aios_core.kernel.services.execution", "aios_core.kernel.services.resource", "aios_core.kernel.services.scheduler", "aios_core.kernel.services.policy", "aios_core.kernel.services.permissions", "aios_core.kernel.services.context"]) == []` — KHÔNG chui implementation (INV-017 lõi)
   - `test_inv017_harness_call_sites` — `runner.py` PHẢI chứa literal `.prepare(` VÀ `.validate(` VÀ `.run(` VÀ `.verify(` VÀ `.complete(` (hook orchestration); `lifecycle.py` PHẢI chứa `can_transition(` VÀ `transition(`; `registry.py` PHẢI chứa `def register(` VÀ `def get(` VÀ `def list(` — runner không tự quyết transition, registry không tự invoke hook
   - `test_inv017_harness_no_private_access` — scan AST toàn `harness/*.py`: KHÔNG có `ast.Attribute` nào có `attr` bắt đầu `_` với `value` là `Name` (không phải `self`) — chặn `svc._states`, `registry._entries`... (loại trừ `self._x` nội bộ; `ctx._sink` nội bộ context — `self._sink` OK)
   - `test_inv017_harness_no_god_object` — `lifecycle.py` KHÔNG chứa `def execute(` + KHÔNG import `aios_core.kernel.services` (thuần); `registry.py` KHÔNG chứa `can_transition`/`def execute(`; `runner.py` KHÔNG chứa `def can_transition(`/`def is_terminal(` (ủy thác lifecycle) + KHÔNG `ThreadPoolExecutor` (sync v1); `contracts.py` KHÔNG chứa `lifecycle|registry|runner|context|errors` (leaf — pattern `test_inv015_contracts_leaf`)
   - `test_inv017_no_harness_in_kernel` — reverse: `kernel/services`, `kernel/graph`, `kernel/scheduler`, `orchestrator/planning`, `observability` KHÔNG import `aios_core.harness` (chiều duy nhất harness → kernel; H1 không bị ai trong kernel phụ thuộc)
   - `test_inv018_runner_builds_evidence` — `runner.py` PHẢI chứa literal `HarnessArtifact(` VÀ `"events.json"` VÀ `"report.json"` (evidence tự động bắt buộc — INV-018 không thể tắt)
2. **Behavioral** (`test_harness_kernel.py`):
   - Duck-typed stub state/artifact services (không kế thừa) chạy được — phụ thuộc API-level
   - MockHarness kiểm soát hook raise ở từng phase → status cuối đúng (DIAGNOSED/FAILED) + evidence vẫn đủ (INV-018)

### 6.3 INV-018 — Evidence First (behavioral)
- **Mọi run — thành công LẪN thất bại — tự động tạo ≥ 2 `HarnessArtifact`** (`events` + `report`) — runner không có đường tắt, không cờ tắt
- Evidence truy xuất được: `get_evidence(run_id)` (StateService) + file trên disk (ArtifactService — checksum + sidecar + `ARTIFACT_CREATED` event)
- **Test**: chạy 2 harness — 1 thành công + 1 fail → CẢ 2 report.artifacts đều có 2 artifact; `artifact_service.list(JSON)` chứa đủ 4 file (`harness/{run_id1}/...` + `harness/{run_id2}/...`); checksum hợp lệ (load lại khớp nội dung)

### 6.4 Deterministic (PLAN §13, §23)
- Lifecycle = hàm thuần của (current, next) — không trạng thái ẩn; registry `list()` sorted theo id; runner thứ tự phase cố định
- Không random (trừ run_id uuid — caller truyền run_id cố định trong test), không LLM, không network
- **Giới hạn determinism (tường minh)**: run_id uuid + timestamp + `duration_ms` là ngoại lệ đo lường (pattern 027 AC12/028 AC12); test determinism dùng run_id cố định + loại trừ started_at/ended_at/generated_at/timestamps/duration_ms → 2 lần chạy cùng input (runner + registry MỚI) → `HarnessReport` y hệt

### 6.5 Additive only
- `git diff` sau implement: `kernel/services/*`, `kernel/events.py`, `kernel/graph/*`, `kernel/scheduler/*`, `orchestrator/*`, `observability/*` **không đổi**
- MOD (chỉ THÊM, không đổi hành vi cũ): `config.py` (+`HarnessSettings` + field `harness`), `config.yaml` (block), `runtime_kernel.py` (block wiring cuối), `tests/*` (additive)
- Mọi test cũ pass không sửa (baseline 1086 — TASK-028)

### 6.6 Tái dùng từ codebase (đã khảo sát code thật)
- **`kernel/services/state.py`** — `StateService.update_state/get_state` (public API): persist run/result/artifacts dưới key `harness:{run_id}` (không đụng `graph:*`/`gnode:*`)
- **`kernel/services/artifacts.py`** — `ArtifactService.store/list` (public API): lưu evidence file + sha256 checksum + sidecar + emit `ARTIFACT_CREATED`; path guard có sẵn — KHÔNG tự viết file IO trong harness/ (tránh "hệ thống song song" — PLAN §M5: *"không tạo hệ thống song song"*)
- **`contracts/artifact.py`** — `ArtifactContract`/`ArtifactType.JSON` (contract M1, đã test field-evolution)
- **`observability/arch_scan.py`** (TASK-021) — engine `collect_imports`/`dir_imports` cho allow-list INV-017 (qua shim `tests/_arch_scan.py`)
- **KHÔNG dùng trong H1** (để cho H4/H5 — TASK-032/034): `observability/metrics.py` (MetricsService), `evaluation.py` (EvaluationStore/Evaluator), `profiler.py`, `doctor.py` — H1 chỉ cung cấp nền; chiều import ngược (evaluation dùng harness, không ngược lại)
- **Config pattern** — `HarnessSettings` theo `SchedulerSettings` (028): pydantic `extra="forbid"` + block yaml + env override `AIOS_HARNESS__...`

### 6.7 Quyết định thiết kế (mở — cho critic phản biện)
- **D1 — Allow-list thêm `kernel.services.artifacts` + `contracts.artifact`**: user spec gốc cho phép "container/kernel.events/kernel.services.state + config", nhưng INV-018 cần lưu evidence truy xuất được → tái dùng ArtifactService (checksum/sidecar/audit event/path guard) thay vì file IO thủ công. Critic: nên giữ list gốc + stdlib `json/pathlib` tự ghi file (mất checksum/audit, tự reimplement path guard) hay chấp nhận 2 entry thêm?
- **D2 — HarnessRun additive `ended_at` + `error`**: PLAN liệt kê run_id/harness/target/version/environment/started_at/status; error path cần ghi lỗi + thời điểm kết thúc vào report/evidence — 2 field additive. Critic: giữ strict PLAN (error chỉ trong HarnessEvent)?
- **D3 — KHÔNG tạo `HarnessDefinition`**: metadata register (id/name/version/description/tags) đọc từ attrs của `Harness` ABC — giảm contract; nếu critic muốn serializable metadata → thêm pydantic model ở TASK-029 hay để task sau?
- **D4 — Extended FAILED transitions**: PLAN literal chỉ `RUNNING → FAILED`; spec thêm `PREPARING/VALIDATING/VERIFYING → FAILED` vì hook fail trước/sau RUNNING không thể đi qua `RUNNING → FAILED` (state machine kẹt). Critic: giữ strict — run fail ở PREPARING/VALIDATING xử lý thế nào (dừng ở phase hiện tại + error field)?
- **D5 — KHÔNG mở rộng EventType v1**: harness events nội bộ (HarnessEvent + sink); không MOD `kernel/events.py`; `kernel.events` nằm allow-list nhưng v1 chưa dùng (dự phòng bridge cho task API sau). Critic: nên thêm `HARNESS_RUN_*` EventType ngay (additive enum — audit được qua EventService)?
- **D6 — DIAGNOSED tự động**: `diagnose_on_failure=True` (mặc định) → runner tự gọi `diagnose` hook + `FAILED → DIAGNOSED`; DIAGNOSED nghĩa "đã chạy post-mortem" (kể cả no-op). Critic: DIAGNOSED nên là bước riêng (caller gọi `runner.diagnose(run_id)`) để phân tách "fail" vs "đã chẩn đoán"?
- **D7 — verify hook v1 raise-or-pass**: INV-019 (Verification Before Verdict) thuộc TASK-030; verify v1 chỉ là hook (raise → FAILED), không có verdict model. Critic: nên đưa `HarnessVerdict` sớm vào H1 để contract ổn định từ đầu?
- **D8 — Sink trong HarnessContext (PrivateAttr)**: sink = runtime dependency, không serialize (`PrivateAttr`); context tạo bởi runner (`create_context`) — caller không tự dựng. Critic: sink nên là tham số `execute()` thay vì field ẩn trong context?

## 7. Tiêu chí chấp nhận (AC)

- [ ] **AC1**: Contracts — 6 model (`HarnessRunStatus` enum + `HarnessRun`/`HarnessEvent`/`HarnessResult`/`HarnessArtifact`/`HarnessReport`) pydantic `extra="forbid"`; defaults đúng; serialization round-trip; `HarnessEvent.level` Literal chặn giá trị sai (YC-1)
- [ ] **AC2**: Errors — `HarnessError` + 5 subclass hierarchy đúng; message giữ nguyên thông tin (YC-2)
- [ ] **AC3**: Lifecycle — happy chain + error chain (`RUNNING→FAILED→DIAGNOSED`) pass; toàn ma trận 8×8: cặp ngoài TRANSITIONS → `can_transition` False + `transition` raise `HarnessLifecycleError`; `is_terminal` = {COMPLETED, DIAGNOSED} (YC-3)
- [ ] **AC4**: HarnessContext — `extra="forbid"`; `_sink` không xuất hiện trong `model_dump`; emit_event gửi đúng event qua sink; chưa attach sink → no-op không raise (YC-4)
- [ ] **AC5**: Registry — register/get/require/list/count; duplicate + metadata rỗng → `HarnessRegistrationError`; `list()` sorted theo id; thread-safe (8 thread register → count == 8, không corrupt) (YC-5)
- [ ] **AC6**: Runner happy path — hook order `[prepare, validate, run, verify, complete]`; payload truyền đúng; events đủ 5 phase; result COMPLETED + summary + metrics (`phase_count == 5`, `duration_ms >= 0`); report.artifacts đủ 2 (events + report); state `harness:{run_id}` đầy đủ; file evidence tồn tại qua `ArtifactService.list(JSON)`; ref = sha256 64 hex (YC-6)
- [ ] **AC7**: **INV-018** — run THẤT BẠI cũng tạo đủ 2 artifact (events + report) + `get_evidence()` truy xuất được; fail path status đúng (`diagnose_on_failure=True` → DIAGNOSED + `on_failure`/`diagnose` được gọi; `False` → FAILED, `diagnose` không gọi); run.error chứa message gốc (YC-6, §6.3)
- [ ] **AC8**: **INV-017 enforcement** — 6 test AST pass (`import_allowlist`; `no_kernel_impl` — execution/resource/scheduler/policy/permissions/context CẤM; `call_sites` — runner gọi `.prepare(`/`.validate(`/`.run(`/`.verify(`/`.complete(`, lifecycle chứa `can_transition(`/`transition(`, registry chứa `def register(`/`def get(`/`def list(`; `no_private_access`; `no_god_object` — lifecycle/registry/contracts leaf, runner không `ThreadPoolExecutor`/`def can_transition(`; `no_harness_in_kernel` — kernel services/graph/scheduler/planning/observability không import harness) + behavioral (duck-typed stub chạy) (§6.1, §6.2)
- [ ] **AC9**: **INV-018 enforcement** — `test_inv018_runner_builds_evidence` pass (runner.py chứa `HarnessArtifact(` + `"events.json"` + `"report.json"`) (§6.2)
- [ ] **AC10**: **Wiring + config + additive + deterministic** — `resolve(HarnessRegistry)`/`resolve(HarnessRunner)` từ `RuntimeKernel.create()`; runner dùng shared StateService/ArtifactService; `runner._settings is settings.harness`; Settings parse block `harness` + env override `AIOS_HARNESS__DIAGNOSE_ON_FAILURE=false`; field thừa → ValidationError; **git diff**: kernel/services/*, kernel/events.py, kernel/graph/*, kernel/scheduler/*, orchestrator/*, observability/* sạch; **determinism**: 2 lần chạy cùng input (run_id cố định, runner/registry MỚI) → report y hệt (trừ timestamp/duration_ms); **full pytest pass (baseline 1086 + test mới ≥ ~45)**, coverage ≥ 95% mục tiêu (hard ≥ 80%) (YC-7, §6.4, §6.5)

## 8. Rủi ro & giả định

| Rủi ro | Giảm thiểu |
|--------|-----------|
| Lệch PLAN vị trí (`aios/harness/` → `backend/src/aios_core/harness/`) bị xem là phá PLAN | Tường minh §2 với 3 lý do codebase thực (packaging, arch_scan SRC_ROOT, convention flat); H2–H5 theo cùng vị trí; critic phản biện trước khi implement |
| `runner` trở thành God Object (orchestrate + evidence + persist + report) | §6.2 no_god_object: runner KHÔNG chứa transition logic (dùng `HarnessLifecycle`), không ThreadPool; registry không invoke hook; lifecycle/contracts/errors thuần; test AST bắt |
| Evidence lưu lệch (quên artifact khi FAILED — INV-018) | Runner tự động build evidence TRONG finally-style sau vòng lifecycle (không phụ thuộc status); AST pin `HarnessArtifact(` + `"events.json"`/`"report.json"`; behavioral test cả 2 nhánh success/fail |
| StateService in-memory — run records mất khi restart | Giả định tường minh v1: run record trong StateService (in-memory — như graph/scheduler 027/028); evidence FILE durable trên disk (ArtifactService) — phần quan trọng nhất (INV-018) vẫn bền; persistence run index = task API sau |
| Hook callable lưu trong pydantic model (sink) gây lỗi serialize/deepcopy | `PrivateAttr` (pydantic v2) — sink không vào `model_dump`; test AC4 bắt |
| Duplicate run_id khi caller truyền | Runner giữ tập run_id đã execute (RLock); duplicate → `HarnessError`; mặc định uuid4 → xác suất trùng ~0 |
| Nhầm lẫn "harness kernel" với "test runner" (H3) | Docstring rõ: H1 = nền tảng contract/lifecycle/registry/runner chung; H3 (TASK-031) xây Scenario/Simulation TRÊN H1; allow-list cấm harness import H3/H4/H5 |
| `verify()` raise sau khi run đã có side effect — status nào? | VERIFYING → FAILED (D4) — run ghi nhận FAILED + evidence đầy đủ; verdict chi tiết (INV-019) = TASK-030 |
| EventType không mở rộng → audit kernel không thấy harness events | HarnessEvent + sink + evidence events.json là nguồn audit v1; nối EventBus = task API sau (D5 — critic phản biện) |
| Runner inject service sai instance (không shared) | Wiring note (pattern 028): `container.resolve(StateService)`/`resolve(ArtifactService)` — test AC10 bắt shared instances |

**Giả định**:
- Runner v1 synchronous, single-run (không thread pool, không async) — chạy đủ nhanh cho H2–H5 (verification/test/eval gọi tuần tự); parallel harness runs = task sau
- `HarnessResult.metrics` v1 = `{duration_ms, phase_count}` — evaluation metrics (score/threshold) thuộc H4 (TASK-032)
- `verify` hook v1 raise-or-pass — verdict model (PASS/FAIL/INCONCLUSIVE, post-conditions) thuộc TASK-030 (INV-019)
- DIAGNOSED = "đã chạy post-mortem" (on_failure + diagnose hook, kể cả no-op khi `diagnose_on_failure=True`); chạy diagnose riêng theo lệnh = task sau (D6)
- Registry v1 lưu harness in-memory (đăng ký lúc wiring/startup); persistence registry = task sau
- `harness:{run_id}` key state không đụng namespace kernel khác (`graph:*`, `gnode:*`, `plan:*`)
- Hook không bị timeout/kill v1 (timeout/budget = H3/H4 — harness bọc scenario, không bọc kernel)
- Determinism tuyệt đối về outcome; run_id/timestamp/duration_ms là ngoại lệ đo lường (pattern 027/028)
- M6 close-out: sau TASK-034 `done` → đối chiếu DoD M6 (PLAN §M6-12) — việc của orchestrator, không nằm trong scope implement 029

## 9. Expected artifacts

| File | Loại | Nội dung |
|------|------|----------|
| `backend/src/aios_core/harness/contracts.py` | NEW | `HarnessRunStatus` + `HarnessRun`/`HarnessEvent`/`HarnessResult`/`HarnessArtifact`/`HarnessReport` — pydantic `extra="forbid"`, leaf (không import package khác) |
| `backend/src/aios_core/harness/context.py` | NEW | `HarnessContext` — run-scoped (target/version/environment/config/run_id) + `PrivateAttr _sink` + `attach_sink()`/`emit_event()` |
| `backend/src/aios_core/harness/lifecycle.py` | NEW | `HarnessLifecycle` — `TRANSITIONS` + `can_transition`/`transition`/`is_terminal` — thuần, deterministic, import tuyệt đối |
| `backend/src/aios_core/harness/registry.py` | NEW | `Harness` (ABC — 7 hooks no-op default) + `HarnessRegistry` (RLock; register/get/require/list sorted/count) |
| `backend/src/aios_core/harness/runner.py` | NEW | `HarnessRunner` — `create_context()` + `execute()` (lifecycle qua hooks + event sink + result + evidence INV-018 + report) + `get_run`/`get_result`/`get_evidence` — import tuyệt đối toàn bộ |
| `backend/src/aios_core/harness/errors.py` | NEW | `HarnessError` + `HarnessRegistrationError`/`HarnessNotFoundError`/`HarnessLifecycleError`/`HarnessHookError` |
| `backend/src/aios_core/harness/__init__.py` | NEW | Re-export (Harness/HarnessRegistry/HarnessRunner/HarnessContext/HarnessRun/HarnessRunStatus/HarnessEvent/HarnessResult/HarnessArtifact/HarnessReport/HarnessLifecycle + errors) |
| `backend/src/aios_core/config.py` | MOD | `HarnessSettings` (`extra="forbid"`: `diagnose_on_failure: bool = True`) + `Settings.harness` (additive) |
| `backend/config.yaml` | MOD | Block `harness` (`diagnose_on_failure: true`) |
| `backend/src/aios_core/kernel/runtime_kernel.py` | MOD | Wiring block `HarnessRegistry` + `HarnessRunner` cuối `create()` (additive — shared StateService/ArtifactService) |
| `backend/tests/test_harness_kernel.py` | NEW | Unit (contracts/lifecycle/registry/context/runner happy+fail) + INV-017 behavioral (duck-typed stub) + INV-018 (evidence success+fail, file trên disk) + determinism + integration (RuntimeKernel e2e) |
| `backend/tests/test_architecture.py` | MOD | `test_inv017_harness_import_allowlist` + `test_inv017_harness_no_kernel_impl` + `test_inv017_harness_call_sites` + `test_inv017_harness_no_private_access` + `test_inv017_harness_no_god_object` + `test_inv017_no_harness_in_kernel` + `test_inv018_runner_builds_evidence` |
| `backend/tests/test_config.py` | MOD | Settings parse block `harness` + env override + validator (additive) |
| `backend/tests/test_runtime_kernel.py` | MOD | `test_harness_wired` (additive — pattern `test_graph_scheduler_wired` + shared instances) |
| `aios/progress/tasks/TASK-029/` | — | critique-1/2, tasks.md, review.md, test.md, evaluation.md (theo workflow gate) |

## 10. Ghi chú thiết kế (cho critic phản biện)

- **Vị trí (§2)**: `backend/src/aios_core/harness/` flat 7 file vs PLAN `aios/harness/contracts/ + kernel/`. Lập luận: 1 Python root duy nhất (packaging/pytest/coverage), arch_scan SRC_ROOT chỉ quét dưới `backend/src`, convention flat (graph/, scheduler/). Critic: nếu giữ `aios/harness/` root — giải quyết packaging/scan thế nào? Nếu giữ `harness/contracts/`+`harness/kernel/` 2 cấp — lợi ích so với flat?
- **D1 — Evidence qua ArtifactService** (thêm allow-list `kernel.services.artifacts` + `contracts.artifact`) vs file IO stdlib: reuse M1 (checksum/sidecar/ARTIFACT_CREATED/path guard) vs giữ allow-list tối thiểu
- **D2 — `ended_at`/`error` additive trên HarnessRun**: cần cho report/evidence error path; PLAN chỉ liệt kê 6 field gốc
- **D4 — FAILED từ PREPARING/VALIDATING/VERIFYING**: PLAN literal chỉ RUNNING → FAILED; hook fail ở phase khác state machine sẽ kẹt — spec mở rộng; critic: strict hay extended?
- **D5 — EventType v1 không mở rộng**: harness events nội bộ qua sink + evidence; nối EventBus/audit = task API sau
- **D6 — DIAGNOSED tự động** (`diagnose_on_failure`): "fail" và "đã chẩn đoán" gộp trong 1 execute — hay tách `runner.diagnose(run_id)` riêng?
- **D7 — verify raise-or-pass v1**: contract `verify(ctx, payload) -> None` — verdict model (INV-019) để TASK-030; đưa `HarnessVerdict` sớm có ổn định contract hơn không?
- **D8 — sink = PrivateAttr trong context** vs tham số execute: context tự chứa sink giúp hook gọi `ctx.emit_event(...)` trực tiếp (chạy giữa chừng log được); tham số execute = context thuần serialize
- **Registry chỉ nhận `Harness` instance** (không `HarnessDefinition`): metadata từ attrs — register(harness) đơn giản; định nghĩa serializable metadata khi cần (task sau)
- **Runner sync v1**: H2–H5 gọi tuần tự; parallel harness runs/async = task sau — tránh ThreadPoolExecutor ngay từ H1 (no_god_object giữ nhẹ)
