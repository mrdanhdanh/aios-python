# TASK-024 — Test Results (Context Optimizer)

**Ngày**: 2026-08-14 | **Runner**: pytest (backend/.venv)

## Kết quả tổng
- **Full suite**: `896 passed, 0 failed` (baseline 855 → +41 test mới)
- **Coverage**: 95.21% (threshold 80% cứng — pass)
- **Arch tests**: 23/23 pass (gồm `test_inv_context_import_allowlist` mới; INV-012 behavioral trong test_context_optimizer)

## Test mới (41)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_context_optimizer.py` | 39 | contracts (extra=forbid, render P1 rỗng, determinism), tier mapping (P0..P6, threshold P4/P5, memory.context None/sai type, serialize deterministic + pathological), L1 (dedup giữ tier cao, P0/P1 không victim, memory không merge, merge defensive, re-token), L2 (substring case-insensitive, punctuation, no-match giữ nguyên, empty terms no-op, truncate, chỉ P3..P6, levels [1,2] no-match, force_extractive empty no-op), L3 (default không chạy, compressor 1 lần, re-token, [1,3]), budget (scenario cut order R1-2, item-level, P0 exempt cap, ValueError, đủ budget, section đơn truncate, edge 2 token), determinism, integration MemoryCoordinator→Optimizer, INV-012 functional |
| `tests/test_architecture.py` | +1 | `test_inv_context_import_allowlist` (C2-01 — cấm models/knowledge/orchestrator/contracts kể cả TYPE_CHECKING; json trong allow-set) |
| `tests/test_runtime_kernel.py` | +1 | `test_context_optimizer_wired` (resolve + optimize E2E, usable 19000) |

## Kiểm chứng AC (11/11)
- **AC1** ✅ Contracts extra=forbid; render deterministic (P1 rỗng emit header — C2-12)
- **AC2** ✅ Tier mapping 7 nguồn; conversation theo relevant_threshold → P4/P5; memory.context None/sai type → rỗng không crash (R3-2)
- **AC3** ✅ L1: dedup (P0/P1 không victim), bỏ metadata thừa, merge defensive loại trừ memory.* (C1-01/C2-02)
- **AC4** ✅ L2: substring case-insensitive; no-match giữ nguyên; empty terms → no-op kể cả force_extractive (C2-09); truncate `max_chars-1 + "…"`; chỉ P3..P6; dư budget không chạy; levels [1,2] kể cả no-match (R2-2)
- **AC5** ✅ L3 stub: mặc định không chạy; compressor gọi 1 lần; re-token sau L3 (C2-05); levels [1,3] (C2-11)
- **AC6** ✅ INV-012: scenario usable 2800 seed 3700 → total ≤ 2800, P5 drop per-tier, P6 drop total, P4 sống; item-level (2 candidate → loại score thấp); P0 3600 > cap 3500 → giữ nguyên báo cáo (C1-02); section đơn > cap → truncate prefix (C2-07); ValueError P0+P1 > usable; edge 2 token (C2-14); đủ budget → truncated=False
- **AC7** ✅ FinalContext sort tier asc; render 7 header (P1 rỗng emit header); reports chính xác
- **AC8** ✅ Determinism: 2 lần chạy model_dump() bằng nhau
- **AC9** ✅ Integration: MemoryCoordinator.inject → optimize → 4 loại memory đúng tier (P2/P3/P4/P5-P6), không vượt budget
- **AC10** ✅ Wiring: resolve ContextOptimizer; optimize E2E tmp settings; 896 pass / 95.21%
- **AC11** ✅ Architecture: allow-list context/ pass; INV-012 behavioral pass; git diff additive only

## Ghi chú / Deviations
1. **R1-1 (review)**: `total = sum(budget.model_dump().values())` — `sum(budget)` với pydantic v2 iter trả (key, value) tuples → TypeError.
2. **R1-2 (review)**: Scenario budget usable thật = 2800 (sum 5 field không reserve) — seed/test điều chỉnh theo; assert P5 drop per-tier trước, P6 drop total sau.
3. **Session id**: `FinalContext.session_id` lấy từ `memory_context.session_id` nếu có, ngược lại "" (optimizer không nhận session_id tham số).
4. **Edge test tokens**: execution section content có prefix `"{key}: "` → tokens = ceil((len+5)/4) — seed test tính đúng.
5. **L2 kích hoạt**: levels_used có 2 kể cả no-match (R2-2); force_extractive + terms rỗng → no-op hoàn toàn (không thêm level).

## Kết luận
- [x] Tất cả 11 AC pass
- [x] Full suite 896 pass, coverage 95.21%
- [x] Determinism verified (2 lần chạy y hệt)
