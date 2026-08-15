# TASK-011 — Test Results (M1 Remediation — 9 findings F-001..F-009)

**Ngày**: 2026-08-12 | **Runner**: pytest (backend/.venv) — file bổ sung hồi tố 2026-08-15 khi đóng hard gate

## Kết quả tổng
- **Full suite**: `428 passed, 0 failed` (baseline M1: 346 → +82 test mới/điều chỉnh)
- **Coverage**: 95.76% (threshold ≥95% — pass)
- **Arch tests**: allow-list + AST scan pass

## Test mới / sửa
| File | Nội dung |
|------|----------|
| `tests/test_cli.py` | CLI subcommands (doctor / catalog list / workflow validate / contract validate, nested parsers) + DI qua `RuntimeKernel.create()` / `SystemCatalog()` — không còn `ExecutionService(...)` trực tiếp |
| `tests/test_contracts.py` | Contract field-evolution regression (pydantic dual-class, 4 case direction) |
| `tests/test_resource.py` | Resource FIFO queue: `acquire_slot_wait` blocking + `pending()`; giữ `acquire_slot` non-blocking |
| `tests/test_context.py` | Context inheritance: PARENT map, `get/get_context/get_all` inherit; fix test scope isolation (`inherit=True` cho nhánh fallback — bypass T10) |
| `tests/test_events.py` | `SNAPSHOT_SAVED` + `TOOL_STARTED`/`TOOL_FINISHED` emit từ ExecutionService (dedup snapshot emit) |
| `tests/test_catalog.py` | Catalog `rebuild()` + `_revision` + `is_stale()` |
| `tests/test_benchmark.py` | Benchmark harness (marked skippable) — `get` O(1) thay `tools_for` O(n) |
| `docs/adr/0001..0003` | ADR engine-independence / capability-first / policy-first + link từ PLAN.md (F-008) |

## Fix lỗi thật phát hiện khi test
1. CLI `from_yaml`/`nodes`/`str(_db_path)` — sửa đúng DI
2. Context default `inherit=False` — đúng thiết kế
3. Resource `acquire_slot_wait` chờ ngoài cond-lock (tránh deadlock)
4. Benchmark `get` O(1) thay vì `tools_for` O(n)
5. Dedup `SNAPSHOT_SAVED` emit (không emit 2 lần)

## Kiểm chứng AC (9/9)
- **AC1** ✅ CLI nested subparsers + DI đúng chỗ
- **AC2** ✅ Contract field-evolution: 4 case direction pass
- **AC3** ✅ Resource FIFO queue fix API defect
- **AC4** ✅ Context inheritance explicit PARENT map
- **AC5** ✅ Events emit từ ExecutionService (audited, ít xâm lấn)
- **AC6** ✅ Catalog rebuild pin API
- **AC7** ✅ (không tách — gộp trong AC1/F-007)
- **AC8** ✅ ADR 0001..0003 + link PLAN.md
- **AC9** ✅ Benchmark honest + non-flaky

## Kết luận
- [x] Tất cả 9 AC pass
- [x] Full suite 428 pass, coverage 95.76%
- [x] Working tree sạch sau commit
