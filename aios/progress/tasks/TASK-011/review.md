# TASK-011 — Review (pre-implementation)

> Review độc lập của spec sau critique-1 + critique-2. Mục đích: xác nhận spec implementable, nguyên tắc được giữ, và không còn defekt trước khi code.

## Kết luận: APPROVED (implementable)
Spec đã qua 2 critique độc lập. Tất cả 3 defekt đúng (F-003/F-007/F-002) đã sửa. Còn 1 mâu thuẫn (N1) + 3 gap API (N2–N4) — **đã được apply vào spec** (xem lịch sử edit). Không còn principle violation.

## Nguyên tắc được giữ (8 principles)
- **Engine-independence (4.8)**: `workflow validate` static parse + `validate_dag`, không cần engine. ✔
- **DI (4.3)**: `doctor`/`run --simulate` dùng `RuntimeKernel.create()`; `catalog` tự build (vì SystemCatalog chưa register — quyết định đúng, không đổi kernel contract). ✔
- **Event (4.7)**: SNAPSHOT_SAVED emit qua EventService (audited, đồng bộ WORKFLOW_*). Surrogate TOOL_* mark M1-only. ✔
- **Capability-first (4.2)**: F-009 benchmark capability O(1) align. ✔
- **Contract-first (4.1)**: F-002 field-evolution test align. ✔
- **No fake test (4.12)**: F-002 assert direction (không chỉ assert pydantic raise); F-009 structural + ratio; F-009 skippable tránh flaky CI. ✔

## Critique resolution checklist
- [x] C1: F-003 non-blocking `acquire_slot` giữ + `acquire_slot_wait` blocking mới (không break ExecutionService).
- [x] C2: F-007 — `run --simulate` dùng `RuntimeKernel.create(settings)` temp audit.db_path (DI + cô lập). `catalog` tự build.
- [x] C3: F-002 — dual pydantic `BaseModel` standalone, KHÔNG CompatibilityChecker.
- [x] C4: F-005 — emit từ ExecutionService, TOOL_* enums đã có, SNAPSHOT_SAVED mới.
- [x] C5: F-009 — benchmark `get()` O(1), `search()` O(N) documented, sizes, skippable.
- [x] C6: F-004 — PARENT map explicit, SHARED root.
- [x] C7: F-006 — `rebuild`/`revision`/`is_stale` pinned; `EntryKind`→`str`.
- [x] C8: F-001 — nested subparsers; catalog list data source + `search("")` accessor pinned.
- [x] Risks R1–R8 present + reframed.

## Pre-merge gates (phải check trước commit)
1. **R8**: grep backend/src KHÔNG có exhaustive `match event.type` (đã verify). Thêm SNAPSHOT_SAVED an toàn.
2. **AC2**: code-review xác nhận không còn `ExecutionService(` trực tiếp trong `cli.py` (chỉ qua container.resolve).
3. **Coverage**: full pytest ≥95%, `test_import` pass.
4. **F-002**: test assert *direction* (compatible/breaking), không chỉ pydantic raise.
5. **F-009**: chạy với `-m "not benchmark"` trên CI; local chạy benchmark để confirm.

## Rủi ro còn lại (đã mitigate trong spec)
- N5 (queue wake primitive): pin `Condition` + `notify`.
- N6 (doctor resolve call): pin `kernel.container.resolve(EventService)`.
- N7 (F-002 base): standalone `BaseModel`.
- R6: surrogate TOOL_* M1-only → M2 remove (note trong execution.py comment).

## Sign-off
Spec đủ chi tiết để implement T1–T9. Không cần critique thêm. Có thể bắt đầu implement.
