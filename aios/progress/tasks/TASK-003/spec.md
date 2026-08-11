# TASK-003 — M1/P0.5a: Kernel Foundations (Contracts + DI + Event Bus + Execution Plan)

## Mục tiêu
Xây 4 nền móng của Runtime Kernel — mọi thứ TASK-004 (9 services) và toàn bộ AIOS sau này đều dựa trên:
1. **Contracts version hóa** — nền "Contract-First": mọi component khai báo contract có `contract_version`/`schema_version`/`compatibility`, có CompatibilityChecker để nâng cấp không phá plugin cũ
2. **DI Container** — Runtime → Container → Agent; đăng ký service, lazy resolve, scope singleton/scoped/transient, lifecycle hooks, test bằng mock
3. **Event Bus** — pub/sub bất đồng bộ (in-process): mọi sự kiện hệ thống (AgentStarted, ToolStarted, WorkflowCompleted, SkillInstalled, PermissionRequested, ArtifactCreated, ErrorOccurred...) đi qua đây; dashboard sau này subscribe qua WebSocket
4. **ExecutionPlan model** — Request → Planner → ExecutionPlan (artifact): nodes dự kiến, resource estimate, permission pre-scan, cost estimate; xem được trên Dashboard, chạy được Simulation

## Phạm vi
- **In** (thuộc `backend/src/aios_core/`):
  1. `semver.py` — helper: `parse_version() -> VersionInfo`, `compare(a, b)` (precedence chuẩn semver, identifier số học)
  2. `contracts/base.py` — `ContractVersion` (contract_version, schema_version, compatibility enum), `ContractMetadata(AiOSMetadata, Contract)` (flat fields: contract_version, schema_version, compatibility), `Contract` ABC (validate() -> bool abstract)
  3. `contracts/artifact.py` — `ArtifactType` enum (markdown, json, python_file, patch, image, zip, test_report, coverage), `ArtifactContract(ContractMetadata)` (type, storage_path, metadata; kế thừa checksum/version/created/updated; validate() implement)
  4. `contracts/compatibility.py` — `CompatibilityChecker` (is_compatible 5-rule, check_upgrade), `CompatibilityResult`
  5. `contracts/__init__.py` — exports
  6. `container.py` — `Container`, `ContainerError`, `Scope` enum (SINGLETON/SCOPED/TRANSIENT): register/register_instance/resolve/resolve_all/has/clear, constructor injection (registration thắng default), RLock, lifecycle start()/stop()
  7. `kernel/events.py` — `Event` dataclass (+to_dict), `EventType` enum, `EventBus` (subscribe/publish/flush, _pending lock-protected, snapshot dưới lock, async trong loop → task / ngoài loop → daemon thread)
  8. `kernel/execution_plan.py` — `ExecutionPlan`, `PlanNode`, `PlanNodeType`, `ExecutionPlanStatus`, `ExecutionPlanBuilder.from_dict` (wrapper model_validate, extra=forbid, cycle detect model_validator)
  9. `kernel/__init__.py` — exports
  10. Tests: test_semver, test_contracts, test_container, test_event_bus, test_execution_plan (5 file) + test_import cập nhật (AC14)
- **Out (không làm)**:
  - 9 services (Context, Event Service wrapper, Artifact, Permission, Policy, Scheduler, State, Resource, Execution) → TASK-004
  - Các contract khác (Agent/Tool/Workflow/Skill/Model/Capability) → task tương ứng P1/P2/P3
  - Event Bus persistence (audit log DB) → TASK-004 (Event Service) + P8
  - ExecutionPlan → thực thi (Executor) → TASK-004 (Execution Service)

## Yêu cầu chi tiết
1. **Semver helper** (`aios_core/semver.py`): `parse_version() -> VersionInfo(major, minor, patch, prerelease, build)` + `compare(a, b)` — precedence chuẩn semver, identifier số học (alpha.10 > alpha.2); dùng cho contracts (KHÔNG dùng regex match-only).
2. **Contracts** (`aios_core/contracts/`):
   - `ContractVersion`: 3 field (contract_version, schema_version, compatibility enum MAJOR_BREAKING/MINOR_COMPATIBLE) — validate semver; v1 KHÔNG ràng buộc chéo 2 field
   - `ContractMetadata(AiOSMetadata, Contract)` — MRO: **BaseModel trước, ABC sau** (pydantic v2); flat fields: `contract_version: str (semver)`, `schema_version: str (semver)`, `compatibility: ContractCompatibility = MINOR_COMPATIBLE`; `validate() -> bool` = `@abstractmethod` (trả False thay vì raise)
   - `Contract` ABC: `validate() -> bool`
   - `CompatibilityChecker.is_compatible(installed: str, required: str)` — **5-rule tổng đối xứng**:
     ```
     1. Trạng thái pre-release khác nhau (1 bên pre, 1 bên release) → incompatible (cả 2 chiều)
     2. precedence(required) > precedence(installed) (semver chuẩn, identifier số học) → incompatible
     3. required.major < installed.major → incompatible (policy strict)
     4. installed.major == 0 → compatible iff required.major == 0 VÀ required.minor == installed.minor (patch bỏ qua)
     5. Còn lại → compatible
     ```
   - `check_upgrade(old, new) -> CompatibilityResult(compatible: bool, breaking: bool, reason: str)`:
     - `compatible = is_compatible(installed=new, required=old)` (**ĐẢO tham số**)
     - `breaking = (new.major != old.major) or (new.major == 0 and new.minor != old.minor)`
     - `reason` luôn non-empty (mô tả rule vi phạm)
     - invariant: `breaking implies not compatible`
   - `ArtifactContract(ContractMetadata)`: `type: ArtifactType`, `storage_path: str` (non-empty, không NUL), `metadata: dict[str, Any] = {}`; **kế thừa** checksum/created/updated/version (KHÔNG redeclare); checksum `str | None = None` — None hợp lệ, str → phải sha256 64 hex lower (validator ở subclass); `validate()` implement (version/checksum/storage_path sai → False, else True)
   - Protocol interface: v1 chỉ ABC/concrete class (ghi chú `@runtime_checkable`, không AC)
3. **DI Container** (`aios_core/container.py`):
   - `register(interface, impl, scope=SINGLETON)` — `issubclass(impl, interface)` lúc register, sai → TypeError sớm; **register trùng → OVERWRITE + warning qua logger**; v1 mỗi interface 1 impl
   - `register_instance(interface, instance)` — scope singleton bắt buộc; `resolve_all(interface) -> [impl]`; `has(interface) -> bool`; `clear()` — xóa registry VÀ instance singleton đã tạo (resolve lại tạo mới)
   - Constructor injection rules (pin): **registration luôn thắng default**; `Optional[X]`/`X | None` default None → resolve X nếu đăng ký else None; Union không None → ContainerError ("Union unsupported in v1"); `*args`/`**kwargs`/param không hint → ContainerError kèm tên; param không default + hint chưa đăng ký → ContainerError
   - Scope: singleton / scoped (v1 = per-container, ghi chú) / transient; lazy instantiation
   - Lifecycle: `start()`/`stop()` gọi `on_startup()`/`on_shutdown()` của instance đã tạo; instance KHÔNG có method → bỏ qua im lặng; idempotent
   - **`threading.RLock`** (chống deadlock resolve lồng nhau); circular → ContainerError (set đang resolve)
4. **Event Bus** (`aios_core/kernel/events.py`):
   - `Event` dataclass: `id` (uuid4), `type: EventType`, `timestamp` (aware UTC), `payload: dict[str, Any]`, `source: str`; `to_dict()`
   - `EventType` enum: AGENT_STARTED, AGENT_FINISHED, TOOL_STARTED, TOOL_FINISHED, WORKFLOW_STARTED, WORKFLOW_COMPLETED, WORKFLOW_FAILED, SKILL_INSTALLED, SKILL_UPDATED, SKILL_REMOVED, UPGRADE_COMPLETED, PERMISSION_REQUESTED, PERMISSION_GRANTED, PERMISSION_DENIED, ARTIFACT_CREATED, MODEL_CALL_STARTED, MODEL_CALL_FINISHED, ERROR_OCCURRED
   - `subscribe(event_type=None, handler) -> Subscription` — None = tất cả; thứ tự = thứ tự subscribe; cùng handler 2 lần → gọi 2 lần; unsubscribe 2 lần → no-op
   - `publish(event)` — **handler list snapshot dưới lock, iterate trên snapshot**; handler sync lỗi → bắt + log warning, không ảnh hưởng handler khác
   - Async handler: (a) trong running loop → `create_task` + `_pending: set[asyncio.Task]` (lock-protected), done_callback bắt **CancelledError trước** `task.exception()` → log + discard; (b) ngoài loop (sync thread) → `asyncio.run(handler(event))` trong **daemon thread** fire-and-forget, exception log trong thread; `_pending`/`flush()` chỉ phủ path (a)
   - `async def flush()` — await toàn bộ pending
   - Handler sync chậm block publish (chấp nhận v1, ghi chú)
5. **ExecutionPlan** (`aios_core/kernel/execution_plan.py`): `ExecutionPlan`/`PlanNode` = **pydantic BaseModel**; `model_config extra="forbid"`; `PlanNodeType` enum (TASK/TOOL/LLM/DECISION); PlanNode fields: `id: str`, `type: PlanNodeType`, `name: str`, `agent: str`, `capabilities: list[str]`, `depends_on: list[str]`, `timeout_s: int` (≥0), `retries: int` (≥0); validators: nodes ≥ 1, estimated_cost ≥ 0, estimated_tokens ≥ 0; **cycle detect (kể cả self-dependency) = `model_validator(mode="after")`**; status enum (DRAFT, READY, RUNNING, COMPLETED, FAILED, CANCELLED); `ExecutionPlanBuilder.from_dict(cls, data)` = classmethod **wrapper gọi `ExecutionPlan.model_validate(data)`**; `to_dict() = model_dump(mode="json")`; **KHÔNG import contracts trong execution_plan** (tránh circular)
6. Tuân thủ: code tiếng Anh, docstrings, type hints; mọi test CWD-independent (tmp_path); **mỗi module mới có test file riêng** (4 file); không dồn aggregate
7. Coverage ≥ 80% trên `aios_core` (giữ nguyên addopts)

## Input / Output
- Input: `docs/PLAN.md` (P0.5), `backend/src/aios_core/` (TASK-002 đã có config/logging/metadata/healthcheck), Python 3.13.14
- Output: `contracts/` (base, artifact, compatibility), `container.py`, `kernel/` (events, execution_plan), tests, commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: `ContractVersion` có 3 field + compatibility enum; validate semver cả 2 field (contract_version, schema_version) — pre-release/build metadata hợp lệ, "1.0" → ValidationError (có test)
- [ ] AC2: `CompatibilityChecker.is_compatible` đủ 8 case (có test): (1.0.0, 2.0.0) → incompatible; (1.0.0, 1.2.0) → incompatible (required mới hơn); (1.2.0, 1.0.0) → compatible (backward-compat); (1.0.0, 0.9.0) → incompatible (policy strict); (0.1.0, 0.2.0) → incompatible (0.x); (1.0.0-beta.1, 1.0.0) → incompatible (pre-release); (1.0.0-alpha.10, 1.0.0-alpha.2) → compatible (precedence số học); (0.1.5, 0.1.2) → compatible (0.x cùng minor)
- [ ] AC3: `ArtifactContract(ContractMetadata)` kế thừa (không redeclare); valid: checksum None hoặc sha256 64 hex lower, version semver, storage_path non-empty không NUL, contract_version semver, `validate()` → True; invalid: checksum sai format → ValidationError, version không semver → ValidationError, storage_path empty → ValidationError, contract_version không semver → ValidationError (có test)
- [ ] AC4: Container: register sai kiểu → TypeError; resolve chưa đăng ký → ContainerError (có test)
- [ ] AC5: singleton cùng instance; transient khác instance; scoped cùng instance (v1); register_instance enforce singleton (có test)
- [ ] AC6: Constructor injection: A→B tự tạo; circular → ContainerError; Optional[X] chưa đăng ký → None; default ≠ None + hint chưa đăng ký → dùng default; **default ≠ None + hint ĐÃ đăng ký → resolve registration (KHÔNG dùng default)**; Union không None → ContainerError; param không hint → ContainerError; param không default + hint chưa đăng ký → ContainerError (có test)
- [ ] AC7: Lifecycle: start()/stop() gọi hooks của instance đã tạo; instance không có hooks → bỏ qua im lặng; gọi 2 lần không lỗi (có test)
- [ ] AC8: EventBus: publish → handler nhận đúng event; filter type; event_type=None nhận mọi event; unsubscribe → không nhận; cùng handler 2 lần → gọi 2 lần; unsubscribe 2 lần → no-op; thứ tự = thứ tự subscribe (có test)
- [ ] AC9: handler sync ném exception → handler khác vẫn chạy, không crash (có test)
- [ ] AC10: async trong `asyncio.run`: publish → `await flush()` → handler nhận đúng payload; async handler ném exception → không crash + lỗi log (caplog); **async từ sync thread (không loop) → handler vẫn chạy (threading.Event chờ)** (có test)
- [ ] AC11: ExecutionPlanBuilder.from_dict: hợp lệ → plan đúng; id trùng → ValidationError; depends_on không tồn tại → ValidationError; cycle (kể cả self) → ValidationError; nodes rỗng → ValidationError; cost âm → ValidationError (có test 6 case, exception = pydantic.ValidationError)
- [ ] AC12: `ExecutionPlan.to_dict()` (= model_dump json) → `ExecutionPlanBuilder.from_dict()` roundtrip + assert **equality đầy đủ** (có test)
- [ ] AC13: pytest pass (backend/ + root) coverage ≥ 80%; mỗi module mới có test riêng (test_semver, test_contracts, test_container, test_event_bus, test_execution_plan)
- [ ] AC14: test_import: `from aios_core import contracts, Container, ContainerError, EventBus, ExecutionPlan, ExecutionPlanBuilder` + `from aios_core.contracts import ArtifactContract, CompatibilityChecker, ContractVersion, ContractMetadata` pass (pin tên chính xác)
- [ ] AC15: register trùng → overwrite (resolve ra impl mới nhất — mock override); resolve A→B (singleton) trong 2 thread → không deadlock (có test)
- [ ] AC16: 2 thread publish đồng thời 50 event → không lỗi, tổng handler nhận = 100; unsubscribe trong handler → không crash (có test)
- [ ] AC17: `check_upgrade` đủ 4 case (có test): (1.0.0→2.0.0) F/T; (1.0.0→1.2.0) T/F; (0.1.0→0.2.0) **F**/T; (1.0.0→0.9.0) F/T; reason non-empty; invariant `breaking implies not compatible`; ghi chú (1.2.0→1.0.0) F/F
- [ ] AC18: `Event.to_dict()` hoạt động; artifact storage_path chứa unicode + space hợp lệ (có test)
- [ ] AC19: Container `has()` True sau register / False trước + after clear; `clear()` xóa cả instance singleton đã tạo (resolve lại tạo mới) (có test — cho TASK-004)
- [ ] AC20: semver helper: `parse_version` + `compare` — (1.0.0 > 1.0.0-beta.1 > 1.0.0-alpha.10 > 1.0.0-alpha.2), (0.1.0 < 0.2.0) (có test)

## Phụ thuộc
- TASK-002 done (aios_core: metadata SEMVER_RE, config, logging) — reuse `SEMVER_RE` (extract ra `metadata.semver` helper nếu cần)
- Python 3.13.14, venv backend đã cài `.[dev]`

## Rủi ro
- R1: Async handler phức tạp trên Windows (event loop) → v1: handler async chạy thread mới (loop riêng), stateless; Event Service (TASK-004) marshal vào main loop; test với `asyncio.run` + `flush()`
- R2: Constructor injection có thể chậm với nhiều dep → v1 đủ dùng (resolve theo type hint), cache instance singleton
- R3: Over-engineer contracts (7 loại) → v1 CHỈ base + artifact + compatibility; agent/tool/workflow contract để task sau
- R4: Circular dependency detection → detect bằng set đang resolve + RLock chống deadlock, đủ cho v1
- R5: Task leak + exception nuốt ở EventBus async → `_pending` set + done_callback log + flush() (đã pin ở Yêu cầu 3)
- R6: Xung đột field khi kế thừa pydantic (ArtifactContract ← ContractMetadata ← AiOSMetadata) → kiểm tra field trùng lúc implement; KHÔNG redeclare checksum/created/updated/version
- R7: Path unicode/Windows (artifact storage_path) → chỉ validate non-empty + không NUL, không regex charset; test path unicode + space
- R8: Import circular (contracts/container/kernel) → execution_plan KHÔNG import contracts; contracts chỉ import metadata (không vòng)
