# TASK-023 — Test Results (Memory Coordinator)

**Ngày**: 2026-08-14 | **Runner**: pytest (backend/.venv)

## Kết quả tổng
- **Full suite**: `855 passed, 0 failed` (baseline M4: 809 → +46 test mới)
- **Coverage**: 95.16% (threshold 80% cứng — pass)
- **Arch tests**: 22/22 pass (gồm `test_inv_memory_import_allowlist` + `test_inv011_memory_isolation` mới)

## Test mới (46)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_memory_coordinator.py` | 41 | contracts (extra=forbid, Field constraints, defaults, ValidationError), 7 strategies + ma trận source×strategy, filter + since + top_k, rank (weights/tie-break/fake clock/naive UTC/clamp), compress (C2-08), dedup + regression prefix dài (C2-03), budget AC5 4K + overflow + short-circuit, inject (EXECUTION scope, overwrite, inherit), determinism 2 lần chạy, list_chunks additive, session str() |
| `tests/test_config.py` | +2 | budget 6 field default (tổng 20K), env override `AIOS_MEMORY__BUDGET__KNOWLEDGE` |
| `tests/test_runtime_kernel.py` | +1 | resolve MemoryCoordinator + inject end-to-end (tmp settings) |
| `tests/test_architecture.py` | +2 | allow-list memory/ (C2-01 — cấm knowledge kể cả TYPE_CHECKING), INV-011 explicit (agents không import memory/knowledge) |

## Kiểm chứng AC (10/10)
- **AC1** ✅ Contracts 5 models extra=forbid; ValidationError đúng (thừa field, top_k≤0, min_importance ngoài [0,1], strategy lạ)
- **AC2** ✅ 7 strategies test riêng; hybrid gộp ≥2 nguồn; embedder None → semantic rỗng; ValidationError thay ValueError (C3-01)
- **AC3** ✅ Ranking deterministic: weights đổi → reorder; tie-break 4 cấp; fake clock; naive → UTC; 2 lần chạy model_dump() bằng nhau
- **AC4** ✅ Dedup cùng nội dung 2 source → 1 candidate; khác nội dung → giữ cả 2
- **AC5** ✅ Budget 4K: 100 memories (40 conv + 30 knowledge + 20 session + 10 artifact), mỗi category vượt cap, total ≤ 4000, per-kind ≤ cap, dropped = min total trong category, truncated=True; overflow 1 category riêng
- **AC6** ✅ Compress đúng max_chars (1999 + "…" = 2000); content ngắn giữ nguyên
- **AC7** ✅ Inject EXECUTION scope; overwrite; `get(AGENT, inherit=True) is None`; INV-011 arch test pass
- **AC8** ✅ Budget settings default + env override; config.yaml load không lỗi
- **AC9** ✅ Wiring resolve được; test dùng tmp settings (make_settings + test_api fixture override cả 2 db); coverage 95.16% ≥ 80%
- **AC10** ✅ Allow-list memory/ pass (không import knowledge kể cả TYPE_CHECKING); git diff additive only (ngoại trừ BOM removal — xem dưới)

## Ghi chú / Deviations
1. **AC5 artifacts cap 100 thay vì 500 trong spec v4**: tên artifact > 200 ký tự vượt giới hạn filename Windows (~255) khi ArtifactService.store ghi file → dùng name 60 ký tự (15 tokens × 10 = 150 > cap 100). Tổng budget test = 3600 ≤ 4000 (tiêu chí `total_tokens ≤ 4000` vẫn đạt).
2. **Short-circuit C2-02 điều chỉnh**: text rỗng chỉ trả selection rỗng khi KHÔNG có strategy RECENCY/IMPORTANCE (2 strategy này không cần text — "lấy N mới nhất" hợp lệ với text rỗng). Recency/importance vẫn chạy với text rỗng.
3. **HYBRID expansion**: coordinator mở rộng HYBRID → {semantic, keyword, recency} trước khi gọi source (source không khai báo hỗ trợ HYBRID).
4. **MemoryBudget local trong memory/contracts.py** (schema giống MemoryBudgetSettings): tránh memory → config dependency (allow-list); RuntimeKernel.create map `MemoryBudget(**settings.memory.budget.model_dump())`.
5. **BOM removal**: conversation.py + vector.py (file M1) có UTF-8 BOM → ast.parse fail khi arch scan toàn dir memory/ → bỏ BOM (chỉ đổi encoding, không đổi nội dung — git diff xác nhận 1 dòng BOM char).

## Kết luận
- [x] Tất cả 10 AC pass
- [x] Full suite 855 pass, coverage 95.16%
- [x] Determinism verified (2 lần chạy y hệt, fake clock)
