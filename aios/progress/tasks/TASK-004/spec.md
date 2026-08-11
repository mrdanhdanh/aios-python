# TASK-004 — M1/P0.5b: Kernel Services I (Context, Event+Audit, Artifact, Permission, Policy)

## Mục tiêu
Xây 5 service đầu của Runtime Kernel (theo PLAN: Context Service, Event Service + audit log, Artifact Service, Permission Service, Policy Service) — mỗi service là module độc lập, đăng ký được vào DI Container, dùng chung EventBus/Container/contracts từ TASK-003. Là nền cho TASK-005 (Scheduler/State/Resource/Execution) + RuntimeKernel.

## Phạm vi
- **In** (thuộc `backend/src/aios_core/kernel/services/`):
  1. `context.py` — `ContextScope` enum (SYSTEM, USER, WORKFLOW, AGENT, EXECUTION, SHARED), `Context` dataclass **frozen** (scope, key, value, ttl_s, created), `ContextService` (set/get/delete/get_all, TTL eviction lazy qua **injectable clock** `clock: Callable[[], float] = time.monotonic`, validate key non-empty)
  2. `events.py` — `EventService`: wrapper EventBus — `emit(event_type, payload, source) -> Event` (publish + **audit log SQLite**: table `audit_events` id=event.id PK, type, timestamp, source, payload_json; index (type, timestamp); **connection-per-call** + `PRAGMA busy_timeout=5000`; `db_path.parent.mkdir(parents=True, exist_ok=True)`; insert lỗi → log warning, emit không crash); `query_audit(limit=100, event_type=None)` — DESC theo timestamp; `json.dumps(..., default=str)`
  3. `artifacts.py` — `ArtifactService`: `store(contract, content) -> ArtifactContract` (ghi file theo base_dir, verify/tự tính sha256 + refresh updated, **sidecar JSON** `storage_path + ".aios.json"` chứa contract, emit ARTIFACT_CREATED), `load(contract) -> bytes` (verify checksum → `ArtifactCorruptedError`), `delete` idempotent, `list(artifact_type=None) -> list[ArtifactContract]` (quét base_dir đọc sidecar, filter type); **path guard (store+load+delete)**: `path = base_dir / storage_path` nếu tương đối, giữ nguyên nếu tuyệt đối → `resolved = path.resolve()` → `not resolved.is_relative_to(base_dir.resolve())` → ValueError
  4. `permissions.py` — `PermissionScope` enum (filesystem, network, docker, shell, clipboard, git, browser, camera), `PermissionDecision` enum (ALLOW, DENY, ASK), `PermissionRequest` dataclass (scope, resource, reason, request_id, created), `PermissionService`: `request() -> PermissionDecision` (default filesystem=ALLOW, còn lại ASK; request luôn tạo request_id; **pending CHỈ cho decision ASK**), `set_policy(scope, decision)` (validate enum), `grant(request_id)`/`deny(request_id)` → emit GRANTED/DENIED; `on_ask` callback (sync — docstring: phải nhanh, M2 chuyển async; raise → log warning + fallback ASK; **trả ALLOW/DENY → xóa pending + emit kết quả ngay; trả ASK → giữ pending + emit PERMISSION_REQUESTED — không double emit**); emit PERMISSION_REQUESTED payload kèm `service: "permission"` + request_id
  5. `policy.py` — `Policy` model (allow_scopes, deny_scopes, require_approval, sandbox_required, allow_internet, max_tokens, **max_concurrent — chở giá trị cho TASK-005, KHÔNG evaluate**, version semver), `PolicyService.evaluate(request: PolicyRequest) -> PolicyDecision(approved, requires_approval, sandbox_required, allow_internet, policy_version, reason)`; **precedence deny > approval > allow**: deny bất kỳ scope → rejected, reason liệt kê TẤT CẢ scope deny; max_tokens vượt → rejected; internet + !allow_internet → rejected; require_approval/scope ASK → requires_approval=True + emit PERMISSION_REQUESTED
  6. **Mở rộng `Settings`** (sửa `config.py`, `config.yaml`, `test_config.py`): `audit.db_path: str = "aios/data/audit.db"`, `artifacts.dir: str = "aios/data/artifacts"`
  7. Tests: test_context, test_events, test_artifacts, test_permissions, test_policy (5 file) + test_import cập nhật
- **Out (không làm)**: Scheduler/State/Resource/Execution + RuntimeKernel → TASK-005; persist permission decisions DB (in-memory v1); policy storage (hardcoded defaults + override dict); **context access control (quyền truy cập riêng từng loại) → task sau**

## Constructor & signature (DI-compatible — type hints + defaults)
- `ContextService(clock: Callable[[], float] = time.monotonic)`
- `EventService(bus: EventBus, db_path: Path | str)`
- `ArtifactService(base_dir: Path | str, bus: EventBus)`
- `PermissionService(bus: EventBus, on_ask: Callable[[PermissionRequest], PermissionDecision] | None = None)`
- `PolicyService(bus: EventBus, policy: Policy | None = None)`
- `query_audit(...) -> list[Event]` (tái dựng Event từ row); thứ tự emit: **audit trước, publish sau**
- Path relative trong settings: resolve so với CWD (nhất quán `logging.file_path`)

## Yêu cầu chi tiết
1. **ContextService**: TTL trên monotonic timebase duy nhất — `Context` frozen: `created: datetime` (UTC, metadata audit/hiển thị, KHÔNG dùng TTL) + `_created_mono: float` (init qua service: `Context(..., _created_mono=self.clock())` — **KHÔNG dùng init=False** để mọi fake clock hoạt động); `is_expired(clock)` = `clock() - _created_mono >= ttl_s`; **`ttl_s=None` → không bao giờ hết hạn**; get trả None nếu hết hạn (lazy eviction); delete idempotent; get_all(scope) → `dict[str, Any]`
2. **EventService**: emit không throw khi audit insert lỗi (log warning — event vẫn publish); connection-per-call + busy_timeout; mkdir parent; audit id = event.id (PK) + index (type, timestamp); query_audit DESC; json.dumps default=str; emit trả về Event
3. **ArtifactService**: store — mkdir base_dir trước, path guard (is_relative_to), sidecar JSON contract, **luôn tự tính checksum + ghi đè + refresh updated (mutate in-place contract caller + trả contract đã cập nhật)**, emit ARTIFACT_CREATED payload `{"artifact": contract.model_dump(mode="json")}`; load — checksum None → skip verify, checksum mismatch → ArtifactCorruptedError, file missing → FileNotFoundError; delete idempotent + xóa sidecar; list — quét base_dir **rglob** đọc sidecar (`ArtifactContract.model_validate`), **sidecar hỏng/lạ → logger.warning + skip, không raise**, không verify checksum, filter type; **base_dir chưa tồn tại → list trả []**
4. **PermissionService**: default filesystem=ALLOW, còn lại ASK; set_policy validate enum; request tạo request_id; **pending CHỈ cho decision ASK** (ALLOW/DENY → emit kết quả luôn); grant/deny theo request_id → emit; **id không tồn tại → no-op + log warning**; on_ask sync (docstring: phải nhanh, M2 chuyển async), raise → fallback ASK; emit PERMISSION_REQUESTED payload kèm `service: "permission"` + request_id
5. **PolicyService**: `PolicyRequest(scopes: list[PermissionScope], tokens: int | None = None, internet: bool = False, sandbox: bool = False)`; precedence deny > approval > allow; scope trong deny → rejected + reason liệt kê tất cả; trong allow → allow; **không nằm trong allow → ASK (default-deny)**; max_tokens vượt → rejected; internet + !allow_internet → rejected; require_approval + deny → deny thắng; require_approval/ASK → requires_approval=True + emit PERMISSION_REQUESTED payload kèm `service: "policy"` + request_id (tự sinh uuid); PolicyDecision kèm policy_version; Policy version semver validate; **max_concurrent + sandbox_required: chở giá trị, KHÔNG evaluate (TASK-005 enforce)**; **Default Policy: allow_scopes=[filesystem], deny_scopes=[], require_approval=False, sandbox_required=False, allow_internet=False, max_tokens=None, version="0.1.0"**
6. Mọi service nhận config qua constructor (settings hoặc dict) — không đọc env trực tiếp; mọi test dùng tmp_path cho db/artifacts
7. Code tiếng Anh, docstrings, type hints; mỗi module có test riêng; coverage ≥ 80% (giữ addopts)

## Input / Output
- Input: TASK-003 (Container, EventBus, EventType, ArtifactContract, contracts), config.py Settings
- Output: 5 service modules + 5 test files + exports, commit

## Tiêu chí chấp nhận (Acceptance Criteria)
- [ ] AC1: ContextService: set/get/delete; TTL hết hạn (fake clock) → get None; get_all(scope) → dict; key empty → ValueError; delete idempotent; Context frozen (có test)
- [ ] AC2: EventService.emit → event đến EventBus subscriber + audit row được ghi (query_audit thấy); emit trả Event (có test)
- [ ] AC3: query_audit: filter type + limit; DESC; audit insert lỗi không crash emit (mock db lỗi) (có test)
- [ ] AC4: store: ghi file + sidecar JSON + **tự tính checksum + ghi đè + refresh updated** + emit ARTIFACT_CREATED; **base_dir chưa tồn tại → tự mkdir thành công** (có test)
- [ ] AC5: load đúng content; checksum mismatch → ArtifactCorruptedError; file missing → FileNotFoundError; delete idempotent (xóa cả sidecar); list theo type; **file lạ/sidecar hỏng → list không crash (skip + warning)** (có test)
- [ ] AC6: Path guard (store+load+delete): "../outside" → ValueError; **sibling-prefix `<base_dir>2/evil` → ValueError**; **absolute path ngoài base_dir → ValueError**; path tương đối → nằm trong base_dir (có test 4 case)
- [ ] AC7: PermissionService: filesystem default ALLOW; network default ASK; set_policy validate enum (typo → ValueError); request trả đúng decision (có test)
- [ ] AC8: PolicyService: deny scope → rejected (reason liệt kê tất cả); max_tokens vượt → rejected; internet + !allow → rejected; require_approval + deny → deny thắng; require_approval → requires_approval=True; **scope không trong allow/deny → requires_approval=True** (có test 6 case)
- [ ] AC9: Policy version invalid semver → ValidationError (có test)
- [ ] AC10: pytest pass (backend/) + coverage ≥ 80%; test_import: `from aios_core.kernel.services import ContextService, EventService, ArtifactService, PermissionService, PolicyService` pass
- [ ] AC11: Mọi test dùng tmp_path — git status sạch sau test (verify trong test.md)
- [ ] AC12: Settings mở rộng: `audit.db_path` + `artifacts.dir` load được từ config.yaml + default (có test trong test_config)
- [ ] AC13: Permission pending flow: request ASK → pending có request_id; **request ALLOW/DENY → không vào pending**; grant/deny(request_id) → emit GRANTED/DENIED; **grant id không tồn tại → no-op không crash**; on_ask raise → fallback ASK không crash; PolicyService emit PERMISSION_REQUESTED (service: policy) khi requires_approval (có test)

## Phụ thuộc
- TASK-003 done (Container, EventBus, EventType, ArtifactContract, config)
- Python 3.13.14, venv backend

## Rủi ro
- R1: SQLite audit insert lỗi (disk full/lock) → emit không crash (wrap try/except + log warning); busy_timeout 5000 giảm lock
- R2: Path traversal guard → Path.is_relative_to sau resolve (cả 2 vế), áp store+load+delete; py3.13 resolve() đã chặn symlink trỏ ngoài — hardening bổ sung (cấm symlink hoàn toàn) → task sau
- R3: Policy over-engineer → model tối thiểu, max_concurrent defer TASK-005
- R4: TTL dùng monotonic clock inject (không phụ thuộc system clock, test không sleep)
