# Critique vòng 2 — TASK-003

## Đánh giá chung
Spec cải thiện rõ so vòng 1, 16/18 resolution áp đúng. Nhưng resolution P1-1 tạo ra 2 P1 MỚI (AC2 case 6 mâu thuẫn rule list; quan hệ check_upgrade ↔ is_compatible chưa pin) + 8 P2 + P3. **Sẵn sàng: 3.5/5 — cần sửa.**

## Vấn đề + Resolution

### P1-A — AC2 case 6 MÂU THUẪN rule list (pre-release ngược chiều)
- Vấn đề: `(1.0.0-beta.1, 1.0.0)` — installed pre, required release → rule list bullet 4 → compatible, nhưng AC2 yêu cầu incompatible.
- **Resolution**: thay rule list bằng **5-rule tổng đối xứng**:
  1. Trạng thái pre-release khác nhau (1 bên pre, 1 bên release) → incompatible (cả 2 chiều)
  2. `precedence(required) > precedence(installed)` (so sánh semver chuẩn, identifier số học) → incompatible
  3. `required.major < installed.major` → incompatible (policy strict)
  4. `installed.major == 0` → compatible iff `required.major == 0` VÀ `required.minor == installed.minor` (patch bỏ qua)
  5. Còn lại → compatible

### P1-B — `check_upgrade` ↔ `is_compatible` quan hệ chưa định nghĩa (bẫy đảo tham số)
- **Resolution**: pin tường minh:
  - `check_upgrade(old, new).compatible = is_compatible(installed=new, required=old)` (ĐẢO tham số)
  - `breaking = (new.major != old.major) or (new.major == 0 and new.minor != old.minor)`
  - `reason` luôn non-empty (mô tả rule vi phạm)
  - 5 case verify: (1.0.0→2.0.0) F/T; (1.0.0→1.2.0) T/F; (0.1.0→0.2.0) F/T; (1.0.0→0.9.0) F/T; (1.2.0→1.0.0) F/F (ghi chú)

### P2-A — AC17 thiếu case + chưa pin compatible=False
- **Resolution**: AC17 đủ 4 case cả 3 trường: (1.0.0→2.0.0) F/T; (1.0.0→1.2.0) T/F; (0.1.0→0.2.0) **F**/T; (1.0.0→0.9.0) F/T; ghi chú (1.2.0→1.0.0) F/F.

### P2-B — Rule 0.x chiều ngược mâu thuẫn (bullet 4 vs 5 cũ)
- **Resolution**: rule 4 mới đã xử lý: trong 0.x compatible iff cùng major.minor → (0.2.0, 0.1.0) incompatible, (0.1.5, 0.1.2) compatible.

### P2-C — Async handler ngoài loop chưa pin cơ chế (nguy cơ silent no-op)
- **Resolution**: (a) trong running loop → `create_task` + `_pending`; (b) ngoài loop (sync thread) → `asyncio.run(handler(event))` trong **daemon thread** fire-and-forget, exception log trong thread; `_pending`/`flush()` chỉ phủ path (a). Thêm AC: publish async từ sync thread → handler vẫn chạy (threading.Event chờ).

### P2-D — Injection: luật tổ hợp `default ≠ None + hint ĐÃ đăng ký` chưa pin
- **Resolution**: nguyên tắc duy nhất: **registration luôn thắng default**. Thêm case AC6: default ≠ None + hint đã đăng ký → resolve registration. Param không default + hint chưa đăng ký → ContainerError.

### P2-E — ContractMetadata "contract fields" mơ hồ, không AC test
- **Resolution**: pin flat: `class ContractMetadata(AiOSMetadata): contract_version: str (semver); schema_version: str (semver); compatibility: ContractCompatibility = MINOR_COMPATIBLE`. Thêm AC: ArtifactContract contract_version không semver → ValidationError.

### P2-F — Contract ABC: ai implement validate() + MRO
- **Resolution**: `class ContractMetadata(AiOSMetadata, Contract)` (MRO: BaseModel trước, ABC sau); `validate()` = `@abstractmethod`; `ArtifactContract.validate() -> bool` implement (version/checksum/storage_path sai → False, else True). Thêm case AC3: `artifact.validate()` True cho hợp lệ.

### P2-G — AC11 vs AC12 API mâu thuẫn
- **Resolution**: `ExecutionPlanBuilder.from_dict(cls, data)` = classmethod **wrapper gọi `ExecutionPlan.model_validate(data)`**; `to_dict()` = `model_dump(mode="json")` (JSON-ready cho dashboard); AC12: to_dict → from_dict roundtrip + assert **equality đầy đủ**.

### P2-H — `has()`/`clear()` không AC — TASK-004 cần
- **Resolution**: thêm AC: `has(X)` True sau register, False trước/after clear; `clear()` xóa cả instance singleton đã tạo (resolve lại tạo mới).

### P3 — (nhẹ, áp vào spec/implement)
1. AC3: checksum `str | None = None` — None hợp lệ; str → phải sha256 64 hex lower (validator ở subclass)
2. Tạo `aios_core/semver.py` helper: `parse_version() -> (major, minor, patch, prerelease, build)` + `compare()` (precedence số học: alpha.10 > alpha.2); contracts dùng chung
3. AC2 thêm 2 case: `(1.0.0-alpha.10, 1.0.0-alpha.2)` → compatible (precedence số học); `(0.1.5, 0.1.2)` → compatible
4. AC14 thêm `ContainerError` + `ExecutionPlanBuilder`
5. EventBus `_pending` lock-protected; done_callback bắt CancelledError trước task.exception()
6. AC8 thêm: event_type=None nhận mọi event; subscribe 2 lần → gọi 2 lần; unsubscribe 2 lần → no-op
7. AC5 thêm: scoped → cùng instance (v1); register_instance enforce singleton
8. PlanNode pin fields: `agent: str`, `capabilities: list[str]`, `depends_on: list[str]`; validators `timeout_s >= 0`, `retries >= 0`; cycle detect = `model_validator(mode="after")`
9. Lifecycle: instance KHÔNG có on_startup/on_shutdown → bỏ qua im lặng
10. Ghi chú Protocol `@runtime_checkable` vào Yêu cầu 2 (không AC)

## Kết luận
- [x] **Resolve toàn bộ (2 P1 + 8 P2 + 10 P3)** — spec cập nhật theo resolution, sẵn sàng implement.

*(Nội dung phản biện gốc do subagent critic; resolution bởi AIOS Orchestrator.)*
