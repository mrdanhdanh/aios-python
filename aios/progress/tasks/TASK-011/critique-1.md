# TASK-011 — Critique 1 (independent critic)

> Đọc kỹ spec + source thực tế. Phát hiện 3 defekt đúng (sẽ gây rework/bug) + nhiều API chưa định nghĩa rõ → risk test giả (nguyên tắc 4.12).

## Verdict (phải sửa trước implement)
1. **F-003 API tự mâu thuẫn + break `ExecutionService`** — spec ghi `acquire_slot()` đầy → return `True` (queued), nhưng caller duy nhất `ExecutionService._run` làm `if not self._resources.acquire_slot(): return FAILED`. Return `True` khi queued → execution chạy dù chỉ mới queue → vi phạm invariant concurrency. Test mô tả ("1 chạy, 2 queue, release → next") lại cần **blocking** semantics, mâu thuẫn với API non-blocking.
2. **F-007 giả định `RuntimeKernel.create()` resolve mọi service, nhưng `SystemCatalog`/`CapabilityRegistry` KHÔNG được register** (`runtime_kernel.py:58-74` chỉ có 12 service). → `catalog` subcommand không thể lấy catalog qua kernel.
3. **F-002 bảo "dùng `CompatibilityChecker`" — sai**: class này chỉ làm semver (`is_compatible`/`check_upgrade`), không có API field-level. Field-evolution test chỉ làm được bằng pydantic dual-class fixture.

## 2. Technical feasibility (verified against source)
- **F-001/F-007**: `cli.py:14-26` chỉ có `run`; `cli.py:50-53` instantiate trực tiếp `ExecutionService(EventService(bus, tmpdb), PolicyService(bus), StateService(), ResourceService())` → findings valid. NHƯNG `RuntimeKernel.create()` không register `SystemCatalog` → `catalog` subcommand gap. THÊM: `run --simulate` hiện dùng temp audit DB (`cli.py:51`); chuyển sang kernel → đổi path thành `settings.audit.db_path` (mất cô lập test) → chưa được nhắc đến.
- **F-002**: `contracts/compatibility.py` chỉ semver. `contracts/base.py` có `Contract` ABC + `ContractMetadata` pydantic `validate()`. → "use CompatibilityChecker" sai. Phải dùng dual-class pydantic (`extra="forbid"`).
- **F-003**: `services/resource.py:52-58` `acquire_slot` return `False` khi đầy (reject), không queue. Defekt như trên.
- **F-004**: `services/context.py:55-62` `get(scope,key)` chỉ check scope đó, không inheritance → valid. NHƯNG `_store` là `dict[ContextScope, dict]` (1 dict per scope *type*, share toàn cục) → inheritance là across scope *types*, không per-entity. Chain "SYSTEM←USER←WORKFLOW←AGENT←EXECUTION←SHARED" mơ hồ hướng + vị trí SHARED.
- **F-005**: `events.py:11-30` ĐÃ có `TOOL_STARTED`(16)/`TOOL_FINISHED`(17); chỉ `SNAPSHOT_SAVED` thiếu. `state.py:28-32` `StateService.__init__` không có bus; `snapshot()` chỉ nhận `execution_id`. Inject raw **bus** → SNAPSHOT_SAVED KHÔNG được audit (các lifecycle event khác qua `EventService` → SQLite). Khuyến nghị: emit từ `ExecutionService` (đã gọi `snapshot()` + có `self._events`, audited) thay inject bus vào StateService (ít xâm lấn, giải quyết R1).
- **F-006**: `catalog.py:32-86` không có `rebuild`/`_revision` → valid. `search` (`:64-72`) là **linear O(N) scan**. `is_stale` phải qua `is_stale(rev)` hoặc `search(since_revision=)`, không tự `search` biết revision người gọi.
- **F-008**: `docs/` chỉ có `PLAN.md`/`README.md` → valid. Yêu cầu mỗi ADR có Status/Date/Consequences + link từ PLAN.
- **F-009**: `capabilities/registry.py` `tools_for` O(1) → valid. NHƯNG `SystemCatalog.search` O(N) → assert `<5ms` size-dependent, flaky trên CI. Benchmark `get()` (O(1) indexed) cho mục <5ms; `search()` document O(N) + bound lỏng; specify size.

## 3. AC gaps
- AC2 verification yếu (khó assert DI trong unit test) → dùng smoke test + code review; AC2 bất khả thi cho `catalog` đến khi fix gap register.
- AC4 test cần blocking API (chưa có trong spec).
- AC7 API names chưa pin (`rebuild`, `revision`, `is_stale`).
- AC9 flaky (size unspecified, O(N) search).
- **Thiếu AC**: backward-compat `acquire_slot()` (non-blocking vẫn return False khi đầy); `run --simulate` regression (audit DB path); `rebuild` thread-safety; event payload schema; ADR linkage to PLAN.

## 4. Risk assessment
- R1 overstated: optional `bus/events: EventService|None = None` → callers cũ backward-compat tự động; ExecutionService nhận `state_service` qua param nên constructor không đổi. Risk thật là **audit-consistency** + **emit-site**.
- R2 KHÔNG phải risk — là **defekt** (phải sửa).
- R3: store đã global per scope-type → leak inherent; risk thật là parent-map order sai.
- R4 insufficient: timing O(1) noise trên CI → thêm structural assertion (dict-backed) + ratio bound + `--benchmark` skip.
- **Thiếu R5-R8**: audit DB path change; M1 surrogate TOOL_* double-emit với M2; rebuild thread-safety; enum exhaustive match (đã verify không có `match event.type` exhaustive → an toàn, note thành pre-merge gate).

## 5. Process fit
- DI: F-007 đúng hướng nhưng "all subcommands use kernel" overengineered + bất khả thi cho `catalog`. `workflow validate`/`contract validate` là static parse → không cần kernel.
- Engine-independence: `workflow validate` phải giữ engine-agnostic (parse + `validate_dag` only).
- Event: F-005 OK nếu surrogate tool events mark M1-only.
- Không fix nào vi phạm principle, nhưng F-007 blanket + F-003 break là regression thực tế.

## 6. Test strategy
- F-002: test chỉ assert pydantic raise = test pydantic không test AIOS → risk fake (4.12). Phải assert *direction* compatibility (v1 payload parse under v2 ⇒ compatible; v2-required missing under v1 ⇒ breaking; rename/remove ⇒ breaking qua `extra="forbid"`).
- F-003: test dùng threads + **blocking** acquire; assert running never > max_concurrent, queue FIFO drain, non-blocking vẫn return False khi đầy.
- F-009: specify sizes (catalog ≥500, compile ≥50 nodes, caps ≥1000); benchmark `get()` cho <5ms; search() document O(N) + bound lỏng; structural O(1) assertion + `--benchmark` skip.
- F-004/F-006: pin chain map + `rebuild`/`revision`/`is_stale` signatures trước khi viết test.

## Actionable (phải sửa trong spec revision)
1. F-003: giữ `acquire_slot()` non-blocking (return False khi đầy, backward-compat); thêm `acquire_slot_wait()` (blocking, queue+FIFO) + `pending()`. Test dùng threads + blocking call.
2. F-007: `run --simulate` + `doctor` dùng `RuntimeKernel.create()`; `catalog` register `SystemCatalog` vào kernel HOẶC tự build; `workflow validate`/`contract validate` static (không kernel). Giữ cô lập audit DB cho simulate (temp), không đổi sang settings.audit.db_path.
3. F-002: frame là pydantic dual-class schema-evolution regression test; KHÔNG dùng CompatibilityChecker; label rõ là test-only.
4. F-005: emit SNAPSHOT_SAVED từ ExecutionService (audited, ít xâm lấn); TOOL_* enums đã có; mark surrogate M1-only.
5. F-009: benchmark `get()` O(1) <5ms; search() O(N) document; specify sizes; skippable.
6. F-004: định nghĩa explicit `PARENT: dict[ContextScope, ContextScope|None]`; quyết định get_context/get_all có inherit.
7. F-006: pin `rebuild(entries)`, `revision` property, `is_stale(rev)`.
8. F-001: nested subparsers; định nghĩa contract validate type.
9. Risks: R1 make optional; R2→defect fixed; R3 chain; R4 add structural; thêm R5-R8.
10. AC: thêm backward-compat, run --simulate regression, rebuild thread-safety, event payload, ADR linkage.
