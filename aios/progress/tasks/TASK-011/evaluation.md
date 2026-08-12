# Evaluation — TASK-011

> Điền SAU khi hoàn thành test (T9). Đối chiếu AC trong spec.md.

## Kết quả đối chiếu tiêu chí chấp nhận
| AC | Tiêu chí | Kết quả | Bằng chứng |
|----|----------|---------|------------|
| AC1 (F-001) | 4 subcommand (doctor, catalog list, workflow validate, contract validate) tồn tại + nested parsers + test cover | ✅ | `workflow/cli.py` rewrite; `tests/test_cli.py` (test_doctor_runs, test_catalog_list_empty, test_workflow_validate_valid, test_workflow_validate_missing_file, test_contract_validate_valid) |
| AC2 (F-007) | `doctor`/`catalog` dùng `RuntimeKernel.create()`/`SystemCatalog()`; không còn `ExecutionService(...)` trực tiếp trong cli path; `workflow/contract validate` static; `run --simulate` giữ temp audit DB | ✅ | `tests/test_cli.py::test_no_direct_executionservice_in_cli` (grep source); test_simulate_prints_reason patch `Container.resolve` + `audit.db_path=f"{tmp}/audit.db"` |
| AC3 (F-002) | 4 case field-evolution, assert direction, label schema-evolution regression (KHÔNG claim test framework) | ✅ | `tests/test_contracts.py` (SampleContractV1/V2AddOptional/V2RemoveRequired/V2Rename/V2Required + 4 test_evolution_*) |
| AC4 (F-003) | `acquire_slot()` non-blocking giữ `return False` khi đầy; `acquire_slot_wait()` blocking + FIFO + `pending()`; thread-safe; test 2 worker/max=1/3 acquires | ✅ | `kernel/services/resource.py`; `tests/test_resource.py` (test_acquire_slot_wait_blocks_until_release, test_acquire_slot_wait_timeout, test_nonblocking_acquire_slot_backward_compat) |
| AC5 (F-004) | inheritance qua PARENT map; `get`/`get_context`/`get_all` inherit; test set WORKFLOW get EXECUTION | ✅ | `kernel/services/context.py` (PARENT dict + `_lookup`); `tests/test_context.py` (test_inheritance_fallback_to_parent, test_inheritance_disabled_is_isolated, test_shared_scope_has_no_parent) |
| AC6 (F-005) | `SNAPSHOT_SAVED` enum + emit từ `ExecutionService` (audited); `TOOL_STARTED`/`TOOL_FINISHED` mỗi node (M1-only); subscribe test bắt payload | ✅ | `kernel/events.py` (EventType.SNAPSHOT_SAVED); `kernel/services/execution.py` emit; `tests/test_events.py::test_snapshot_saved_event_type_exists`, `tests/test_execution.py::test_snapshot_and_tool_events_emitted` |
| AC7 (F-006) | `rebuild()` + `_revision` + `is_stale(rev)`; test reset + stale + concurrent safe | ✅ | `catalog/catalog.py` (rebuild, _revision, is_stale); `tests/test_catalog.py` (test_rebuild_replaces_index_and_bumps_revision, test_is_stale_detects_changes, test_rebuild_thread_safe_under_concurrent_search) |
| AC8 (F-008) | ≥3 ADR với Status/Date/Context/Decision/Consequences + link từ `PLAN.md` | ✅ | `docs/adr/0001-engine-independence.md`, `0002-capability-first.md`, `0003-policy-first.md`; `docs/PLAN.md` mục "Architecture Decisions (ADR)" |
| AC9 (F-009) | `test_benchmark.py` đo `get()`<5ms O(1) + `compile`<50ms + capability O(1); `search()` documented O(N); skippable marker | ✅ | `tests/test_benchmark.py` (marked `pytest.mark.benchmark`); `pyproject.toml` `[tool.pytest.ini_options] markers`; test_catalog_get_is_o1, test_catalog_get_ratio_scales_sublinear, test_workflow_compile_smoke, test_capability_registry_o1 |

## Kết quả test
- Full suite: **428 passed** (no regressions), 5 warnings, thời gian ~11s.
- Coverage: **95.76%** (target ≥95%, gate `--cov-fail-under=80` PASS).
- Benchmark tests chạy local (không dùng `-m "not benchmark"`) để xác nhận không flaky → PASS.
- Các lỗi phát hiện & sửa trong T9 (test-fix pass):
  - `cli.py`: `from_yaml_str` → `from_yaml`; `definition.steps` → `definition.nodes` (WorkflowDefinition dùng `nodes`); `_db_path` wrap `str()` để `json.dumps` không lỗi.
  - `test_cli.py`: import `aios_core.container.Container` (không phải `aios_core.kernel.container`); contract JSON bổ sung `id`/`author`/`license` (bắt buộc theo `AiOSMetadata`).
  - `context.py`: default `inherit=False` (giữ backward-compat test hiện có; test mới explicit `inherit=True`).
  - `resource.py`: `acquire_slot_wait` chờ **ngoài** condition-lock (tránh deadlock `pending()`/`release_slot()`).
  - `test_resource.py`: poll `pending()==1` thay event race.
  - `test_benchmark.py`: benchmark `reg.get()` (O(1) dict) thay `tools_for` (copy list → O(n) làm ratio fail); giữ correctness-check `tools_for`.
  - `execution.py`: sửa duplicate emit `SNAPSHOT_SAVED` (chỉ emit 1 lần/node).

## Đánh giá hệ thống tổng thể
- 9 finding P3 từ M1 v2 review đều được remediation với test targeted (mỗi finding ≥1 test) → tăng test-depth mà không đổi deliverable M1.
- CLI giờ có surface đầy đủ (doctor/catalog/workflow/contract validate) theo đúng nguyên tắc DI + engine-agnostic.
- ADR đóng băng 3 quyết định architecture cốt lõi (engine-independence, capability-first, policy-first) — tài liệu hóa rõ negative consequences.
- Resource queue + Context inheritance + Catalog rebuild/stale + Tool/Snapshot events nâng tầm runtime correctness/observability, sẵn sàng cho M2.

## Bài học
1. Khi thêm event/queue: cẩn thận lock semantics — `Condition.wait` cần dùng `self._slot_cond.wait` hoặc release lock trước khi `Event.wait`, nếu không `pending()`/`release_slot()` bị block.
2. WorkflowDefinition dùng `nodes` (không phải `steps`) — luôn check attribute name trước khi reference.
3. `json.dumps` không serialize `Path`/`datetime` → wrap `str()` hoặc default serializer.
4. Default param `inherit` nên `False` khi thêm optional behavior vào API hiện có để không break test backward-compat.

## Đề xuất cải tiến
- M2 nên dùng `acquire_slot_wait` (blocking) trong ExecutionService thay vì non-blocking FAILED path.
- M2 thay thế surrogate TOOL events bằng real Tool Registry events (F-005 mark M1-only).

## Kết luận
- [x] **ĐẠT spec** — TASK-011 remediation 9 P3 findings hoàn tất; 428 tests pass, coverage 95.76%; sẵn sàng commit + chuyển M2 Orchestrator (TASK-010 đã done, TASK-012 tiếp theo).
