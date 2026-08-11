# Critique vòng 1 — TASK-004

## Đánh giá chung
Spec có cấu trúc tốt, không creep sang TASK-005. Nhưng 2 P1 (path traversal startswith SAI — bypass thật; list() không có cơ chế persist contract) + 6 P2 + 3 P3. **Sẵn sàng: 2.5/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — Path traversal guard dùng startswith → bypass + mâu thuẫn R2
- **Resolution**: bỏ startswith; thuật toán: (1) `path = base_dir / storage_path` nếu tương đối, giữ nguyên nếu tuyệt đối; (2) `resolved = path.resolve()`; (3) `if not resolved.is_relative_to(base_dir.resolve()): raise ValueError`; (4) thao tác file. Áp dụng **store + load + delete**. AC6 thêm case sibling-prefix `<base_dir>2/evil`.

### P1-2 — list(artifact_type) không có cơ chế persist contract
- **Resolution**: **sidecar JSON** — store ghi `storage_path + ".aios.json"` chứa toàn bộ contract (model_dump json); `list()` quét base_dir đọc sidecar → `list[ArtifactContract]`, filter theo type. Persist qua restart, dùng cho Artifact Browser M3.

### P2-1 — TTL monotonic khó test + trộn timebase
- **Resolution**: `ContextService(..., clock: Callable[[], float] = time.monotonic)` — test inject fake clock, không sleep; `Context`: `created: datetime` + `ttl_s: float | None`; `is_expired(clock)` tính qua clock; sửa R4: "TTL dùng monotonic clock (không phụ thuộc system clock)".

### P2-2 — SQLite audit thread-safety + mkdir + correlation
- **Resolution**: connection-per-call (mở/ghi/đóng mỗi emit) + `PRAGMA busy_timeout=5000`; init `db_path.parent.mkdir(parents=True, exist_ok=True)`; `id` = event.id (PK) + index (type, timestamp); `emit` trả về Event.

### P2-3 — Settings không có audit/artifacts + extra=forbid
- **Resolution**: mở rộng `Settings` với `audit.db_path: str = "aios/data/audit.db"` + `artifacts.dir: str = "aios/data/artifacts"` — vào In scope (sửa config.py, config.yaml, test_config.py) + AC12.

### P2-4 — max_concurrent field chết
- **Resolution**: **defer** — Policy chở giá trị `max_concurrent`, PolicyService KHÔNG evaluate (TASK-005 Resource Service enforce); ghi rõ.

### P2-5 — Policy precedence chưa định nghĩa
- **Resolution**: precedence **deny > approval > allow**; deny bất kỳ scope → rejected ngay, reason liệt kê TẤT CẢ scope bị deny; require_approval + deny cùng tồn tại → deny thắng; thêm case AC8.

### P2-6 — PermissionService pending flow không cơ chế + không AC
- **Resolution**: `PermissionRequest` dataclass (scope, resource, reason, request_id, created); `request()` luôn tạo request_id + đăng ký pending (dù có callback); `grant(request_id)`/`deny(request_id)` → emit GRANTED/DENIED; callback raise → log warning + fallback ASK; thêm AC13 (pending flow).

### P3 — (áp vào spec)
1. on_ask sync — ghi docstring "callback phải nhanh, M2 Permission Broker chuyển async" (quyết định có chủ đích)
2. Thêm AC: PolicyService emit PERMISSION_REQUESTED khi requires_approval; Context frozen (scope không đổi); load/delete guard path; AC12 config keys
3. `get_all(scope)` → `dict[str, Any]`; `set_policy` validate scope/decision enum; audit `json.dumps(..., default=str)`; query_audit DESC; store tự tính checksum → refresh `updated`; Out ghi rõ "context access control (quyền truy cập riêng) → task sau"; `PolicyDecision` kèm `policy_version`

## Kết luận
- [x] **Resolve toàn bộ (2 P1 + 6 P2 + 3 P3)** — cập nhật spec, chuyển critique vòng 2.
