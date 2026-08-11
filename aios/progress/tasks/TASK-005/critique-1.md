# Critique vòng 1 — TASK-005

## Đánh giá chung
Khung tốt, scope creep chặn đúng. Nhưng 3 P1 (DI không resolve được `Path | str`; `timeout_s: int` mâu thuẫn test 0.05s; resume thiếu plan) + 10 P2 + 9 P3. **Sẵn sàng: 2.5/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — RuntimeKernel.create: Container không resolve được `EventService(bus, db_path: Path | str)` / `ArtifactService(base_dir: Path | str, bus)`
- **Resolution**: RuntimeKernel.create dùng `register_instance` cho EventService + ArtifactService (construct tay với settings.audit.db_path / artifacts.dir) + `register` (class) cho các service còn lại (constructor chỉ type đơn/Optional). Ghi rõ pattern vào spec.

### P1-2 — `PlanNode.timeout_s: int` mâu thuẫn AC6 (0.05s)
- **Resolution**: **đổi `PlanNode.timeout_s` sang `float = 300.0`** (contract change — sửa test TASK-003 execution_plan test dùng int → ok vì pydantic float nhận int); định nghĩa `timeout_s <= 0 → không áp dụng timeout`; AC6 dùng 0.1s (Windows timer ~15.6ms).

### P1-3 — resume thiếu nguồn plan (không tính được topo)
- **Resolution**: snapshot lưu kèm `plan.to_dict()` vào state key `"plan"`; resume đọc plan từ state, validate node ids khớp → raise rõ nếu mismatch. Signature giữ `resume(execution_id, runner)`.

### P2 — (đặc tả)
1. **Event cancel**: thêm `WORKFLOW_CANCELLED = "workflow.cancelled"` vào EventType + AC: cancel → emit WORKFLOW_CANCELLED
2. **Node fail → fail-fast**: dừng toàn bộ plan, WORKFLOW_FAILED reason "node X failed"; node chưa chạy giữ "pending"; topo Kahn FIFO theo thứ tự plan.nodes
3. **Timeout = lỗi node → retry** (đếm chung 1 + retries); `timeout_s <= 0` → join không giới hạn
4. **State schema đầy đủ**: `{plan: dict, nodes: {id: status}, results: {id: result}, started_at}`; snapshot deepcopy có try/except → fallback repr; ghi chú results nên JSON-serializable
5. **Resume**: chạy lại node ≠ completed (reset failed/running → pending, retry budget mới); validate node ids state ⊆ plan ids → raise mismatch; resume cũng pre-check + acquire/release (dùng chung code path)
6. **try/finally**: execute bọc toàn bộ — release tokens + slot trên MỌI path (pre-check fail sau acquire, cancel, exception); clamp ≥ 0 cho slot; **AC15**: sau fail/cancel stats về baseline
7. **requires_approval=True → chặn + WORKFLOW_FAILED reason "approval required"** (chưa có approval flow v1); sandbox_required → log warning + chạy; AC9 thêm case ask
8. **Scheduler interval**: skip tick nếu callback trước chưa xong; interval lỗi → log + tiếp tục tick; stop/cancel không kill callback đang chạy (document)
9. **ExecutionResult thêm `reason: str = ""`** — mọi path FAILED/CANCELLED điền reason
10. **AC7 redesign**: runner node 1 set threading.Event → return; test chờ event → cancel() → CANCELLED, node 2 không chạy; ghi rõ "cancel chỉ hiệu lực giữa nodes; node đang chạy không bị gián đoạn"

### P3 — (áp vào spec)
1. `SchedulerService(poll_interval_s: float = 0.05)` — hết hardcode
2. **Settings.resources**: thêm `ResourcesSettings(max_tokens: int | None, max_concurrent: int | None)` vào In scope + config.yaml + test_config
3. `execution_id = plan.id` (v1); ghi rõ execute cùng plan 2 lần → state ghi đè
4. Map `required_permissions: list[str]` → PolicyRequest.scopes qua `PermissionScope(value)`; scope không biết → bỏ qua + log
5. execute KHÔNG mutate plan.status — kết quả chỉ qua ExecutionResult
6. `stats()` bỏ "queued" (v1 = 0) — tránh nhầm Task Queue M2
7. Đặt `runtime_kernel.py` ở `kernel/` (khớp import `from aios_core.kernel import RuntimeKernel`)
8. Scheduler schedule trùng tên → thay thế + warning; `list_jobs()` → `(name, kind, running)`
9. SchedulerService implement `on_startup()`/`on_shutdown()` — container.start() gọi hook tự động

## Kết luận
- [x] **Resolve toàn bộ (3 P1 + 10 P2 + 9 P3)** — cập nhật spec, chuyển critique vòng 2.
