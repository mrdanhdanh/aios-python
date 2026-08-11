# Critique vòng 1 — TASK-003

## Đánh giá chung
Spec khung tốt, scope sạch (9 services → TASK-004 đúng). Nhưng 2 P1 về cơ chế kỹ thuật (CompatibilityChecker sai chiều backward-compat; EventBus async fire-and-forget không test được) + 8 P2 + 8 P3. **Sẵn sàng: 3/5 — cần sửa.**

## Vấn đề + Resolution

### P1-1 — CompatibilityChecker rule SAI chiều backward-compat (AC2 case 2 sai)
- Vấn đề: `required minor > installed minor → compatible` là forward-compat tự gán, sai tinh thần. Component khai báo `required` (cái nó CẦN), runtime có `installed` (cái ĐANG CÓ) → required mới hơn installed → KHÔNG có API → phải reject. Case 0.x chưa có policy. Installed 2.0.0 + required 1.5.0 mâu thuẫn luận điểm "major = breaking". Pre-release chưa định nghĩa.
- **Resolution**: rule chuẩn semver:
  ```
  is_compatible(installed, required):
    - required.pre-release và installed là release → incompatible
    - required.major > installed.major → incompatible (cần major mới)
    - required.major < installed.major → incompatible (runtime đã breaking — chọn policy strict)
    - cùng major → compatible iff required.minor <= installed.minor (patch bỏ qua)
    - 0.x: minor bump trong 0.x = breaking → incompatible
  ```
  AC2 sửa: `(1.0.0, 1.2.0) → incompatible`; `(1.0.0, 0.9.0) → incompatible` (semver strict 0.x policy); thêm case pre-release. Invariant: `breaking implies not compatible`.

### P1-2 — EventBus async: fire-and-forget không test được + task leak + exception nuốt
- Vấn đề: `create_task` không trả task, không flush; exception trong task không ai await → nuốt; thread không có loop → loop mới mỗi event (stateful handler vỡ).
- **Resolution**: EventBus giữ `_pending: set[asyncio.Task]`; mỗi task có done_callback → log exception (qua get_logger) + discard; thêm `async def flush()` (await toàn bộ pending). AC10 sửa: publish trong `asyncio.run` → `await bus.flush()` → assert handler nhận đúng payload. Thêm AC: async handler ném exception → publish không crash, lỗi được log (caplog). Ghi chú: handler async trong thread mới = loop riêng, chỉ dành stateless; Event Service (TASK-004) marshal vào main loop.

### P2-1 — Container injection: Optional/Union/default/*args chưa có luật
- **Resolution** (pin luật v1):
  - `Optional[X]`/`X | None` default None: resolve X nếu đăng ký, else None (không lỗi)
  - Param có default ≠ None: dùng default nếu hint chưa đăng ký
  - Union nhiều loại không None: ContainerError ("Union unsupported in v1")
  - `*args`/`**kwargs`/param không hint: ContainerError kèm tên param
  - Hint interface đã đăng ký → resolve impl theo registration

### P2-2 — Container: register trùng / resolve_all / register_instance chưa định nghĩa
- **Resolution**: v1 mỗi interface 1 impl; register lại → **overwrite** + warning qua logger (cần cho test mock override — PLAN yêu cầu); `resolve_all` = [impl] (1 phần tử, dành tương lai); `register_instance` → scope singleton bắt buộc. Thêm AC: register 2 lần → resolve ra impl mới nhất.

### P2-3 — Container lock + lazy singleton → deadlock tự thân
- **Resolution**: dùng `threading.RLock` (đơn giản, đủ v1); ghi rõ trong spec; thêm test resolve A→B (singleton) trong 2 thread — không deadlock.

### P2-4 — check_upgrade không có AC
- **Resolution**: thêm AC: `(1.0.0→2.0.0)` → compatible=False, breaking=True, reason non-empty; `(1.0.0→1.2.0)` → compatible=True, breaking=False; `(0.1.0→0.2.0)` → breaking=True (policy 0.x); `(1.0.0→0.9.0)` → incompatible (downgrade). Pin invariant `breaking implies not compatible`.

### P2-5 — ArtifactContract kế thừa chưa pin + AC3 thiếu case fail
- **Resolution**: `class ArtifactContract(ContractMetadata)` — checksum/created/updated/version kế thừa, KHÔNG redeclare; checksum = sha256 64 hex lower; version bắt buộc semver; `storage_path: str`; `metadata: dict[str, Any] = {}`. AC3 thêm 3 case fail: checksum sai format, version không semver, storage_path empty.

### P2-6 — ExecutionPlan chưa pin pydantic + PlanNodeType + strict
- **Resolution**: `ExecutionPlan`/`PlanNode` = **pydantic BaseModel** (ValidationError có sẵn); thêm enum `PlanNodeType` (TASK/TOOL/LLM/DECISION) + validator; `from_dict` `extra="forbid"`; validators: nodes ≥ 1, estimated_cost ≥ 0, estimated_tokens ≥ 0; detect cycle: 3-color DFS (đủ v1) + case self-dependency trong test. AC11 ghi rõ exception = `pydantic.ValidationError`.

### P2-7 — EventBus thread-safe concurrent publish chưa có AC
- **Resolution**: handler list **snapshot dưới lock, iterate trên snapshot** (tránh "Set changed size during iteration"); thêm AC: 2 thread publish đồng thời 50 event → không lỗi, tổng handler nhận = 100; unsubscribe trong handler → không crash.

### P2-8 — AC mơ hồ (AC10 "hoạt động", AC14 hedge, AC1 chỉ thị implement)
- **Resolution**: AC14 pin: `from aios_core import contracts, Container, EventBus, ExecutionPlan` + `from aios_core.contracts import ArtifactContract, CompatibilityChecker, ContractVersion` pass trong test_import; AC10 theo P1-2; AC1 tách: extract semver helper → Yêu cầu chi tiết, AC giữ "ContractVersion validate semver 2 field + pre-release/build metadata".

### P3 — (nhẹ, áp vào spec/implement)
1. `Contract.validate() -> bool` (trả False thay vì raise); verify `class X(BaseModel, ABC)` trên pydantic v2
2. ContractVersion: v1 chỉ ghi chú ý nghĩa, không ràng buộc chéo contract_version vs schema_version
3. `Event.payload: dict[str, Any]`, `source: str`; thêm `to_dict()` (cho dashboard WebSocket M3)
4. storage_path: validate non-empty + không chứa NUL (KHÔNG regex charset — Windows unicode hợp lệ); test path unicode + space qua tmp_path
5. Thứ tự handler = thứ tự subscribe; subscribe cùng handler 2 lần → gọi 2 lần; unsubscribe 2 lần → no-op; handler sync chậm block publish (chấp nhận v1)
6. Interface = Protocol: v1 chỉ ABC/concrete class (`@runtime_checkable` ghi chú, không AC)
7. Mỗi module mới phải có test file riêng (4 test file đã trong In) — không dồn aggregate
8. Thêm R5 (task leak/exception nuốt), R6 (pydantic kế thừa field conflict), R7 (path unicode Windows)

## Kết luận
- [x] **Resolve toàn bộ (2 P1 + 8 P2 + 8 P3)** — spec cập nhật theo resolution, chuyển critique vòng 2.

*(Nội dung phản biện gốc do subagent critic; resolution bởi AIOS Orchestrator.)*
