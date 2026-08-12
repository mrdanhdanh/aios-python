# TASK-011 — M1/P3: Remediation 9 P3 findings từ M1 v2 independent review

> **Loại task**: M1 follow-up hardening (P3). Mở sau khi M1 ĐẠT, trước khi vào M2 Orchestrator (TASK-010) để runtime vững chắc. Không đổi phạm vi deliverable M1 — chỉ closing gaps phát hiện bởi re-review v2.

## Mục tiêu
Khắc phục 9 finding P3 được phát hiện trong `M1-review-independent-v2.md` (re-review M1 theo brief v2). Các finding đều là **hardening sâu** của runtime M1 (không chặn milestone, nhưng nâng tầm architecture correctness, observability và test-depth). Mục tiêu: đưa M1 runtime từ "hoạt động đúng phạm vi" → "vững chắc theo 8 nguyên tắc AIOS + observability + test-depth".

## Phạm vi
Remediation ánh xạ 1-1 với 9 finding:

| # | Finding | Module/Location | Hành động |
|---|---------|-----------------|----------|
| F-001 | CLI thiếu subcommands | `workflow/cli.py` | Thêm `doctor`, `catalog`, `workflow validate`, `contract validate` subparsers |
| F-002 | Contract field-evolution chưa test | `tests/test_contracts.py` + `contracts/` | Thêm test mức field: add field / remove required / rename / optional→required (dùng sample contract schema + `extra="forbid"`) |
| F-003 | Resource thiếu queue | `kernel/services/resource.py` | Thêm queue FIFO: `acquire_slot` đầy → enqueue; `release_slot` → next acquires; API `pending()` |
| F-004 | Context thiếu inheritance | `kernel/services/context.py` | Thêm optional parent-scope fallback: `get(scope, key, inherit=True)` lookup scope cha |
| F-005 | Thiếu emit Tool/Snapshot events | `kernel/events.py`, `state.py`, `execution.py` | Thêm event type `SNAPSHOT_SAVED`; emit khi `state.snapshot()`; emit `TOOL_STARTED`/`TOOL_FINISHED` tại execution node level (surrogate tool) |
| F-006 | Catalog thiếu rebuild/stale | `catalog/catalog.py` | Thêm `rebuild(entries)` + stale guard: `index_entry` ghi `revision`; `search` warn nếu revision lỗi thời |
| F-007 | CLI bypass DI container | `workflow/cli.py` | Dùng `RuntimeKernel.create()` resolve services thay tự instantiate |
| F-008 | Thiếu `docs/adr/` | `docs/adr/` | Tạo ≥3 ADR: engine-independence, capability-first, policy-first |
| F-009 | Thiếu benchmark harness | `tests/test_benchmark.py` | Thêm đo: catalog search <5ms, workflow compile <50ms, capability lookup O(1) |

- **In**: 9 mục trên.
- **Out (không làm)**: thay đổi semantic của M1 deliverable; real LangGraph execution (M2); Tool Registry thật (M2); jinja2 (M4).

## Yêu cầu chi tiết
1. **CLI (F-001, F-007) — nested subparsers, DI đúng chỗ**:
   - `doctor`: runtime health (services registered, bus alive, audit path) → `kernel = RuntimeKernel.create()` rồi `kernel.container.resolve(EventService)` / `EventBus` để check. In JSON/text.
   - `catalog list`: liệt kê `SystemCatalog` entries. `SystemCatalog` **CHƯA** register trong `RuntimeKernel.create()` (chỉ 12 service) → quyết định: `catalog` subcommand **tự build `SystemCatalog()`** (không qua kernel) để tránh đổi kernel contract. **Data source**: index từ `catalog/catalog_data/*.json` (nếu có) hoặc in ra "<empty> — no indexed entries" nếu rỗng (không crash). **Accessor**: dùng `catalog.search("")` (Catalog không có `list()`; `search("")` trả về mọi entry). Document rõ.
   - `workflow validate <yaml>`: static parse + `validate_dag()` (engine-agnostic, **KHÔNG** cần kernel — chỉ read yaml + schema).
   - `contract validate <json>`: validate `ContractMetadata` (hoặc generic contract payload) — static, không kernel.
   - **GIỮ cô lập + DI**: `run --simulate` refactor thành `kernel = RuntimeKernel.create(settings)` với `settings.audit.db_path = f"{tmp}/audit.db"` (temp) → lấy services qua `kernel.container.resolve(...)`. Thỏa mãn CẢ (a) không còn `ExecutionService(...)` trực tiếp trong cli path (AC2) VÀ (b) cô lập temp audit DB. `workflow validate`/`contract validate` static (không kernel); `catalog` tự build `SystemCatalog()`.
   - Mỗi subcommand có test (smoke + functional).
2. **Contract field-evolution (F-002) — TEST-ONLY, pydantic dual-class**:
   - **KHÔNG** dùng `CompatibilityChecker` (chỉ semver). Dùng 2 pydantic model standalone (`pydantic.BaseModel` + `model_config = ConfigDict(extra="forbid")`) `SampleContractV1`/`V2`.
   - 4 case, assert **direction**: (a) add optional v2 → v1 payload parse under v2 ⇒ compatible; (b) remove required v2 → v1 payload thiếu field ⇒ breaking (ValidationError); (c) rename field → v1 payload under v2 ⇒ breaking (extra="forbid"); (d) optional→required v2 → v1 payload thiếu ⇒ breaking.
   - Label rõ "schema-evolution regression test" (test pydantic contract semantics — M1 chưa có field-evolution engine, nên KHÔNG claim test AIOS framework).
3. **Resource queue (F-003) — FIX API defect**:
   - Giữ `acquire_slot()` **non-blocking**: `True` nếu acquire được, `False` nếu đầy (backward-compat; `ExecutionService._run` tiếp tục dùng: `if not self._resources.acquire_slot(): return FAILED`).
   - Thêm `acquire_slot_wait(timeout=None)` (**blocking**): đầy → enqueue FIFO `_queue`, block đến khi grant (hoặc timeout). Dùng `threading.Condition(lock)` + `notify()` để wake next (`release_slot()` pop queue → `notify()`).
   - Thêm `pending() -> int` (số đang chờ).
   - Thread-safe (lock). M1 execution giữ non-blocking; M2 sẽ dùng `acquire_slot_wait`.
   - Test: 2 worker thread, max_concurrent=1, 3 acquires qua `acquire_slot_wait` → 1 chạy, 2 queue, release → next chạy; assert `running` never > 1; assert non-blocking `acquire_slot()` vẫn `return False` khi đầy.
4. **Context inheritance (F-004) — explicit PARENT map**:
   - `PARENT: dict[ContextScope, ContextScope | None] = {EXECUTION: AGENT, AGENT: WORKFLOW, WORKFLOW: USER, USER: SYSTEM, SHARED: None, SYSTEM: None}` (SHARED root-shared, không kế thừa lên).
   - `get(scope, key, inherit=True)` thiếu trong scope → duyệt chain cha; `get_context`/`get_all` cũng inherit (default `inherit=True`).
   - Test: set WORKFLOW, get EXECUTION inherit=True → thấy; get EXECUTION inherit=False → không thấy (isolated).
5. **Events (F-005) — emit từ ExecutionService (audited, ít xâm lấn)**:
   - Thêm `SNAPSHOT_SAVED = "state.snapshot_saved"` vào `EventType` (TOOL_STARTED/TOOL_FINISHED ĐÃ tồn tại).
   - Emit `SNAPSHOT_SAVED` từ `ExecutionService._run` ngay sau `self._state.snapshot(execution_id)` (dùng `self._events.emit` → audited, đồng bộ với WORKFLOW_STARTED/COMPLETED). **KHÔNG** inject bus vào `StateService` (tránh R1 + audit gap).
   - Emit `TOOL_STARTED`/`TOOL_FINISHED` bọc mỗi node run (node = surrogate tool), payload `{execution_id, node_id, node_name}`. **Mark M1-only** (M2 real tool thay thế).
   - Test: subscribe bắt được SNAPSHOT_SAVED + TOOL_STARTED/FINISHED với payload đúng.
6. **Catalog rebuild (F-006) — pin API**:
   - `rebuild(entries: list[tuple[str, str, dict[str, Any]]])` (`kind: str`, `id: str`, `metadata: dict`) → clear `_entries` + re-index; bump `_revision`.
   - `_revision: int` tăng mỗi `index_entry`/`remove_entry`/`rebuild`.
   - `revision` property + `is_stale(rev: int) -> bool` (`rev < _revision`).
   - Thread-safe (dùng lock sẵn có).
   - Test: rebuild reset entries; `is_stale` detect; concurrent search/get không crash.
7. **ADR (F-008)**: `docs/adr/0001-engine-independence.md`, `0002-capability-first.md`, `0003-policy-first.md` — format: Status (accepted), Date, Context, Decision, Consequences (gồm negative). Link từ `docs/PLAN.md` (thêm mục "Architecture Decisions").
8. **Benchmark (F-009) — honest + non-flaky**:
   - `tests/test_benchmark.py` marked `@pytest.mark.benchmark` (skippable CI qua `-m "not benchmark"`).
   - (a) `get()` O(1): catalog ≥500 entries, `get(kind,id)` p95 < 5ms + **structural assert** (dict-backed) + ratio `median@10k / median@1k < 5x`.
   - (b) `compile`: `MockCompiler.compile` ≥50-node workflow < 50ms.
   - (c) capability `tools_for` O(1): ≥1000 caps, timing constant vs N (structural + ratio).
   - Document `search()` là O(N) (không đo <5ms).

## Input / Output
- Input: M1 codebase (TASK-002..009), `M1-review-independent-v2.md`.
- Output: 9 fixes + tests + ADRs + commit; coverage giữ ≥95%.

## Tiêu chí chấp nhận (AC)
- [ ] AC1 (F-001): 4 subcommand (doctor, catalog list, workflow validate, contract validate) tồn tại + chạy được (nested parsers); test_cli cover từng cái (smoke + functional).
- [ ] AC2 (F-007): `doctor`/`catalog` dùng `RuntimeKernel.create()` (nơi applicable) hoặc `SystemCatalog()`; **code-review xác nhận không còn `ExecutionService(...)` trực tiếp trong cli path**; `workflow validate`/`contract validate` explicit static (no kernel). `run --simulate` GIỮ temp audit DB (regression test).
- [ ] AC3 (F-002): 4 case field-evolution có test, assert direction compatible/breaking; label schema-evolution regression (KHÔNG claim test AIOS framework).
- [ ] AC4 (F-003): `acquire_slot()` non-blocking giữ `return False` khi đầy (backward-compat); `acquire_slot_wait()` blocking + FIFO queue + `pending()`; thread-safe; test 2 worker/max=1/3 acquires.
- [ ] AC5 (F-004): inheritance qua PARENT map; `get`/`get_context`/`get_all` inherit; test set WORKFLOW get EXECUTION.
- [ ] AC6 (F-005): `SNAPSHOT_SAVED` enum + emit từ `ExecutionService` (audited); `TOOL_STARTED`/`TOOL_FINISHED` emit mỗi node (M1-only); subscribe test bắt payload `{execution_id, node_id}` / `{execution_id}`.
- [ ] AC7 (F-006): `rebuild()` + `_revision` + `is_stale(rev)`; test reset + stale + concurrent safe.
- [ ] AC8 (F-008): ≥3 ADR với Status/Date/Context/Decision/Consequences + link từ `PLAN.md`.
- [ ] AC9 (F-009): `test_benchmark.py` đo `get()`<5ms O(1) + `compile`<50ms + capability O(1); `search()` documented O(N); skippable marker.
- [ ] AC10: `pytest` toàn bộ pass, coverage ≥95% (không regress); `test_import` pass.
- [ ] AC11: LOG.md + PROGRESS.md cập nhật (task lifecycle); git sạch trước commit.

## Phụ thuộc
- TASK-002..009 (M1 runtime).
- Không dependency mới (benchmark dùng `time` chuẩn; KHÔNG thêm dep mới).

## Rủi ro
- R1 (F-005): emit từ `ExecutionService` → `StateService` constructor KHÔNG đổi → callers backward-compat tự động; risk thật là audit-consistency (đã xử lý bằng emit qua `EventService`).
- R2 (F-003): API defect đã sửa — giữ non-blocking `acquire_slot` (`False` khi đầy) + thêm blocking `acquire_slot_wait`. `ExecutionService` giữ non-blocking.
- R3 (F-004): `PARENT` map explicit; SHARED root không kế thừa lên; không sibling/reverse leak.
- R4 (F-009): benchmark flaky → specify sizes, structural O(1) assertion + ratio bound, `@pytest.mark.benchmark` skippable.
- R5 (F-007): `run --simulate` audit DB path thay đổi → GIỮ temp DB, chỉ `doctor`/`catalog` dùng kernel.
- R6 (F-005): M1 surrogate `TOOL_*` double-emit với M2 → mark M1-only, M2 remove.
- R7 (F-006): `rebuild` thread-safety → dùng lock sẵn có.
- R8 (F-005 enum): thêm `SNAPSHOT_SAVED` an toàn (verify KHÔNG có exhaustive `match event.type`) → pre-merge gate.
