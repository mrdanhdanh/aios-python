# TASK-011 — Critique 2 (independent critic #2, verify revision)

> Đọc kỹ spec đã sửa + critique-1 + source thực tế. Xác nhận 3 defekt đả sửa, còn 1 mâu thuẫn (N1) + 3 gap API (N2–N4) cần fix trước implement.

## Verdict: YES-WITH-MINOR
Tất cả 10 điểm critique-1 đã được giải quyết về nội dung. Spec đã sẵn sàng implement SAU KHI sửa N1 (mâu thuẫn 1 dòng, không redesign). Còn N2–N4 (pin API) + N5–N7 (minor) cần làm rõ.

## Critique-1 resolution table
| # | Điểm | Trạng thái | Bằng chứng |
|---|------|-----------|-----------|
| 1 | F-003 non-blocking `acquire_slot` + `acquire_slot_wait` + `pending()` | RESOLVED | §2 F-003 match `resource.py:52-58` (đã return False khi đầy) |
| 2 | F-007 run --simulate+doctor qua kernel; catalog tự build; static validates; temp DB | PARTIAL (N1) | §1/AC2 mâu thuẫn: "chỉ doctor/catalog dùng kernel" vs AC2 "không còn ExecutionService(...) trong cli path" |
| 3 | F-002 dual pydantic, KHÔNG CompatibilityChecker | RESOLVED | §2 F-002 đúng (compatibility.py chỉ semver) |
| 4 | F-005 emit SNAPSHOT_SAVED từ ExecutionService, TOOL_* đã có, M1-only | RESOLVED | §2; events.py:16-17 TOOL_* exist; state.py:28 không có bus |
| 5 | F-009 benchmark get() O(1)<5ms; search() O(N) documented; sizes; skippable | RESOLVED | §2; search O(N) catalog.py:64-72; tools_for O(1) registry.py:66 |
| 6 | F-004 PARENT map explicit; get_context/get_all inherit | RESOLVED | §2 match ContextScope context.py:11-17 |
| 7 | F-006 rebuild/revision/is_stale pinned | RESOLVED (nhưng N2) | §2; catalog.py chưa có rebuild (net-new) nhưng sig dùng `EntryKind` không tồn tại |
| 8 | F-001 nested subparsers; define contract validate type | RESOLVED | §1 |
| 9 | Risks R1→optional; R2→defect; R3 chain; R4 structural; R5–R8 | RESOLVED | Risks R1–R8 present |
| 10 | AC backward-compat, run --simulate regression, rebuild thread-safe, event payload, ADR link | RESOLVED | AC2/AC4/AC6/AC7/AC8 |

**Tóm lại**: 9/10 fully resolved; #2 resolved trừ N1.

## Remaining / new issues
- **N1 (contradiction F-007 ↔ AC2) — MUST FIX**: §1 ghi "chỉ doctor/catalog dùng kernel" + "run --simulate GIỮ temp audit DB" → ngụ ý run giữ direct-instantiation. Nhưng `cli.py:47-50` hiện làm `ExecutionService(EventService(bus, tmpdb), PolicyService(bus), StateService(), ResourceService())` trực tiếp, và AC2 đòi "không còn ExecutionService(...) trực tiếp trong cli path". Hai câu mâu thuẫn. **Fix**: run --simulate dùng `RuntimeKernel.create(settings)` với `settings.audit.db_path = f"{tmp}/audit.db"` (container.resolve tại container.py:94) → thỏa mãn CẢ DI VÀ cô lập temp DB. Đây chính là ý critique-1 #2.
- **N2 (F-006 undefined type)**: `rebuild(entries: list[tuple[EntryKind, str, dict]])` — `EntryKind` KHÔNG tồn tại (grep 0 match). `CatalogEntry.kind` là `str` (catalog.py:18). Đổi thành `list[tuple[str, str, dict[str, Any]]]` hoặc define enum.
- **N3 (F-001 catalog list không có data source)**: `catalog list` tự build `SystemCatalog()` → 0 entries (chỉ populate qua index_entry). Phải định nghĩa source (scan disk / registry snapshot / hoặc mark stub). Không thì AC1 "catalog list chạy được" là fake-pass (4.12).
- **N4 (F-001 catalog list accessor)**: `SystemCatalog` không có `list()`/`entries`/`__iter__` (grep 0; chỉ get/search/index_entry/remove_entry/count). Để list all → `search("")`. Phải pin accessor.
- **N5 (F-003 wake primitive)**: §2 ghi "release_slot pop queue → wake next" nhưng không pin primitive. Cần `threading.Condition(lock)` + `notify()`. Recommend thêm 1 câu để test AC4 ("running never >1") deterministic.
- **N6 (F-007 doctor resolve call)**: §1 ghi "dùng RuntimeKernel.create() resolve EventBus/EventService" nhưng không tên call. `Container.resolve(EventService)` tồn tại (container.py:94) → pin `kernel.container.resolve(EventService)`.
- **N7 (F-002 sample base)**: §2 ghi "2 pydantic model" nhưng không nói subclass `ContractMetadata` hay `BaseModel`. Subclass `ContractMetadata` kéo theo semver validators (base.py:71-86) → nhiễu field-evolution asserts. Pin: standalone `pydantic.BaseModel` + `ConfigDict(extra="forbid")`.

## Verified correct (no issue)
- run --simulate DÙNG temp audit DB (`cli.py:51`) → isolation requirement thực và đã đúng.
- RuntimeKernel.create() register đúng 12 service, KHÔNG có SystemCatalog/CapabilityRegistry (runtime_kernel.py:58-87) → quyết định tự build catalog đúng.
- acquire_slot return False khi đầy (resource.py:52-58) → non-blocking preserved.
- TOOL_STARTED/TOOL_FINISHED đã có (events.py:16-17); SNAPSHOT_SAVED thiếu (sẽ add).
- KHÔNG có exhaustive `match event.type:` trong backend/src → R8 pre-merge gate an toàn.
- StateService.snapshot(execution_id) không bus (state.py:45) → emit từ ExecutionService (có self._events, execution.py:55,209) là site ít xâm lấn đúng.
- tools_for O(1) dict (registry.py:66) → benchmark valid.
- docs/PLAN.md không có "Architecture Decisions" → F-008 link là net-new, scoped đúng.

## Final recommendation
Spec sẵn sàng implement SAU KHI sửa N1 (1 dòng, không redesign). Trước code, implementer nên:
1. **N1 (blocking)**: rewrite run --simulate bullet → `RuntimeKernel.create(settings)` với temp `settings.audit.db_path`, thỏa mãn AC2 + isolation. Giữ workflow/contract validate static, catalog tự build.
2. **N2 (blocking cho F-006 test)**: đổi `EntryKind` → `str` (hoặc define enum) trong rebuild sig.
3. **N3/N4 (blocking cho AC1)**: define catalog list data source + pin accessor (`search("")` hoặc thêm `list()`).
4. **N5–N7 (non-blocking, làm lúc impl)**: pin queue wake (`Condition`), doctor `container.resolve(EventService)`, standalone `BaseModel` cho F-002 fixtures.

Với N1–N4 fixed, 9 remediations implementable + verifiable, AC1–AC11 testable. KHÔNG còn critique-1 defect hay principle violation mới.
