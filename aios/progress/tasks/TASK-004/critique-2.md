# Critique vòng 2 — TASK-004

## Đánh giá chung
7/9 resolution v1 áp đúng. Nhưng P2-1 v1 áp SAI tạo mâu thuẫn timebase mới (P1-1) + 6 P2 + 8 P3. **Sẵn sàng: 3/5 — vá trước khi implement.**

## Vấn đề + Resolution

### P1-1 — Mâu thuẫn timebase: `created: datetime` vs `clock` monotonic
- **Resolution**: tách vai trò: `created: datetime` (UTC) = metadata audit/hiển thị, KHÔNG dùng TTL; `_created_mono: float = field(default_factory=time.monotonic, init=False, repr=False, compare=False)` — dùng TTL; `is_expired(clock)` = `clock() - self._created_mono >= ttl_s`. Ghi rõ vào spec.

### P2-1 — list() sidecar hỏng/thiếu
- **Resolution**: `list()` dùng `ArtifactContract.model_validate(json.loads(...))`; sidecar corrupt/JSON lỗi/thiếu field/file không có sidecar → `logger.warning` + **bỏ qua (skip)**, không raise; `list()` không verify checksum (verify khi load). AC5 thêm test: file lạ/sidecar hỏng → list không crash.

### P2-2 — store() không tạo base_dir
- **Resolution**: store() `mkdir(parents=True, exist_ok=True)` base_dir trước khi ghi; AC4 thêm test base_dir chưa tồn tại → thành công.

### P2-3 — store() checksum có sẵn
- **Resolution**: **luôn tự tính + ghi đè checksum + refresh updated** (deterministic, không nhánh lỗi); bỏ chữ "verify" khỏi AC4 (đổi thành "tự tính checksum + refresh updated").

### P2-4 — PolicyRequest fields + quy tắc ASK
- **Resolution**: `PolicyRequest(scopes: list[PermissionScope], tokens: int | None = None, internet: bool = False, sandbox: bool = False)`; quy tắc: scope trong deny_scopes → deny; trong allow_scopes → allow; **không nằm trong allow → ASK** (default-deny). AC8 thêm case: scope không trong allow/deny → requires_approval=True.

### P2-5 — Constructor signature + return type
- **Resolution**: thêm mục "Constructor & signature": mỗi service `__init__(...)` type hints + defaults (DI-compatible): `ContextService(clock=time.monotonic)`, `EventService(bus: EventBus, db_path: Path | str)`, `ArtifactService(base_dir: Path | str, bus: EventBus)`, `PermissionService(bus: EventBus, on_ask: Callable[[PermissionRequest], PermissionDecision] | None = None)`, `PolicyService(bus: EventBus, policy: Policy | None = None)`; `query_audit() -> list[Event]` (tái dựng Event từ row); thứ tự: **audit trước, publish sau**.

### P2-6 — Pending lifecycle
- **Resolution**: pending CHỈ lưu request decision ASK (ALLOW/DENY → emit kết quả luôn, không pending); `grant/deny` id không tồn tại → **no-op + log warning**; payload PERMISSION_REQUESTED kèm `service: "permission" | "policy"` + `request_id`. AC13 bổ sung: grant id lạ → no-op không crash.

### P3 — (áp vào spec)
1. AC6 thêm case: absolute path ngoài base_dir → ValueError
2. `load()` checksum None → skip verify
3. `load()` file missing → `FileNotFoundError` (không phải ArtifactCorruptedError)
4. `on_ask` signature: `Callable[[PermissionRequest], PermissionDecision]`
5. Payload chuẩn: ARTIFACT_CREATED = `{"artifact": contract.model_dump(mode="json")}`; audit payload sau json.dumps(default=str)
6. R2 symlink: py3.13 resolve() đã chặn symlink trỏ ngoài — sửa ghi chú
7. Quy ước path relative trong settings: resolve so với CWD (nhất quán logging.file_path)
8. Test mock db lỗi (AC3): db_path trỏ tới directory đã tồn tại → sqlite3.connect raise OperationalError (không cần monkeypatch)

## Kết luận
- [x] **Resolve toàn bộ (1 P1 + 6 P2 + 8 P3)** — cập nhật spec, sẵn sàng tasks.md.
