# TASK-011 — Tasks (breakdown theo AC)

> Mỗi task map 1-1 với 1 finding + AC tương ứng. Thứ tự: infra-before-feature (events/resource/context trước CLI/catalog dùng chúng).

## T1 — F-005: SNAPSHOT_SAVED event + emit từ ExecutionService (AC6, R1/R6/R8)
- **Files**: `kernel/events.py` (thêm `SNAPSHOT_SAVED = "state.snapshot_saved"`), `kernel/services/execution.py` (emit `SNAPSHOT_SAVED` sau `snapshot()`; emit `TOOL_STARTED`/`TOOL_FINISHED` bọc mỗi node, payload `{execution_id, node_id, node_name}`).
- **Tests**: `test_events.py` — enum có SNAPSHOT_SAVED; `test_execution.py` — subscribe bắt SNAPSHOT_SAVED + TOOL_STARTED/FINISHED với payload đúng.
- **Gate R8**: grep KHÔNG có exhaustive `match event.type` (đã verify). Thêm comment `# M1-only surrogate` cho TOOL_* emit.

## T2 — F-003: Resource queue (AC4, R2)
- **Files**: `kernel/services/resource.py` — giữ `acquire_slot()` non-blocking (False khi đầy); thêm `acquire_slot_wait(timeout=None)` (blocking, FIFO `_queue`, dùng `threading.Condition(lock)` + `notify()`); `pending() -> int`.
- **Tests**: `test_resource.py` — 2 worker thread, max_concurrent=1, 3 acquires qua `acquire_slot_wait` → 1 chạy 2 queue, release→next; running never >1; non-blocking `acquire_slot` vẫn False khi đầy.

## T3 — F-004: Context inheritance (AC5, R3)
- **Files**: `kernel/services/context.py` — `PARENT: dict[ContextScope, ContextScope|None]`; `get(scope,key,inherit=True)` fallback chain; `get_context`/`get_all` inherit default True.
- **Tests**: `test_context.py` — set WORKFLOW, get EXECUTION inherit=True thấy; inherit=False không thấy.

## T4 — F-006: Catalog rebuild + revision (AC7, R7)
- **Files**: `catalog/catalog.py` — `rebuild(entries: list[tuple[str,str,dict[str,Any]]])`; `_revision: int` tăng mỗi index_entry/remove_entry/rebuild; `revision` property; `is_stale(rev:int)->bool`; thread-safe (lock sẵn có).
- **Tests**: `test_catalog.py` — rebuild reset; is_stale detect; concurrent search/get không crash.

## T5 — F-001 + F-007: CLI subcommands + DI (AC1, AC2, R5)
- **Files**: `workflow/cli.py` — nested subparsers: `doctor`, `catalog list`, `workflow validate <yaml>`, `contract validate <json>`, `run` (giữ).
  - `doctor`: `kernel = RuntimeKernel.create()` → `kernel.container.resolve(EventService)`/`EventBus` → in health JSON.
  - `catalog list`: tự build `SystemCatalog()`; index từ `catalog/catalog_data/*.json` nếu có, else "<empty>"; accessor `search("")`.
  - `workflow validate`: static parse + `validate_dag()` (NO kernel).
  - `contract validate`: static validate `ContractMetadata` (NO kernel).
  - `run --simulate`: refactor thành `RuntimeKernel.create(settings)` với `settings.audit.db_path = f"{tmp}/audit.db"` (temp, DI, cô lập).
- **Tests**: `test_cli.py` — mỗi subcommand smoke + functional; assert không còn `ExecutionService(` string trong cli module source (grep).

## T6 — F-002: Contract field-evolution test (AC3)
- **Files**: `tests/test_contracts.py` — 2 pydantic `BaseModel` standalone (`ConfigDict(extra="forbid")`) `SampleContractV1`/`V2`; 4 case assert direction (add optional⇒compatible; remove required⇒breaking; rename⇒breaking; optional→required⇒breaking). Label "schema-evolution regression".

## T7 — F-008: ADRs (AC8)
- **Files**: `docs/adr/0001-engine-independence.md`, `0002-capability-first.md`, `0003-policy-first.md` — Status(accepted)/Date/Context/Decision/Consequences(negative). Link từ `docs/PLAN.md` (thêm mục "Architecture Decisions").

## T8 — F-009: Benchmark harness (AC9, R4)
- **Files**: `tests/test_benchmark.py` `@pytest.mark.benchmark` — (a) `get()` O(1): ≥500 entries, p95<5ms + structural + ratio median@10k/median@1k<5x; (b) `MockCompiler.compile` ≥50-node <50ms; (c) capability `tools_for` O(1): ≥1000 caps constant vs N. Document `search()` O(N).
- CI: chạy thường với `-m "not benchmark"`.

## T9 — Integration + coverage + docs (AC10, AC11)
- Chạy full pytest (expect ≥358 pass, coverage ≥95%); `test_import` pass.
- Update `PROGRESS.md` (TASK-011 → in-progress/done), `LOG.md` (lifecycle entry).
- Verify R8 gate (no exhaustive match).

## Order
T1 → T2 → T3 → T4 (infra) → T5 (CLI dùng infra) → T6/T7/T8 (tests/docs) → T9 (integration).
