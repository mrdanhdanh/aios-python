# Review — TASK-024 (Context Optimizer) — spec v3 trước implement

**Reviewer**: subagent reviewer | **Ngày**: 2026-08-14

## Kết luận
- [x] **CHANGES REQUESTED** — 2 R1 blocking (số liệu budget) + 2 R2 + 5 R3. Sau resolve → đủ điều kiện implement (không cần critique vòng 3).

## Kiểm chứng trọng tâm (đối chiếu code thật + chạy thật)
- `estimate_tokens` re-export qua `memory/__init__.py` ✓ — allow-list khớp (`aios_core.memory.coordinator`)
- `render()` deterministic ✓; pre-check ValueError khả thi ✓ (lưu ý `estimate_tokens("")=1`)
- Allow-list context/ khớp cơ chế `_resolve_relative` ✓; `collect_imports` đếm TYPE_CHECKING ✓
- `MemoryContext.selection.items` sorted total desc ✓ (verify `_rank` 4-key sort)
- `MemoryBudget` trùng schema `MemoryBudgetSettings` ✓; lazy wiring + make_settings ✓; không cycle ✓

## Vấn đề
### R1 (blocking)
- **R1-1**: `total = sum(budget)` raise TypeError — pydantic v2 `BaseModel.__iter__` trả (key, value) tuples (đã chạy thật verify).
  → **Resolution**: `total = sum(budget.model_dump().values())`.
- **R1-2**: Scenario C2-06 "usable = 2000" sai công thức — `MemoryBudget(system=400, task=500, knowledge=600, history=800, artifacts=500, reserve=800)` → sum 3600 → usable = **2800**. Seed 3000 → chỉ drop P6 → assert thứ tự P6→P5→P4 fail.
  → **Resolution**: giữ công thức YC-6, sửa scenario: seed P0 400 + P1 300 + P2 500 + P3 600 + P4 800 + P5 600 + P6 500 = 3700; per-tier P4+P5 = 1400 > 800 → loại P5 (600) → 800 = cap; total 3100 > 2800 → loại P6 (500) → 2600 ≤ 2800 ✓. Assert: P5 loại ở per-tier, P6 ở total, P4 sống, `total_tokens ≤ 2800`, P0/P1 nguyên vẹn.

### R2 (major)
- **R2-1**: Semantics `truncated`/`dropped_by_budget` cho prefix-truncate section đơn > cap (C2-07) chưa chốt.
  → **Resolution**: "prefix-truncate = compression trong budget stage — KHÔNG set truncated, phần cắt KHÔNG tính dropped_by_budget (chỉ section bị drop); re-token sau truncate".
- **R2-2**: `levels_used` khi L2 kích hoạt nhưng no-match (terms ≠ ∅) chưa chốt.
  → **Resolution**: "L2 KÍCH HOẠT (vượt budget/force_extractive) → `levels_used` có 2 kể cả no-match theo content"; thêm assert test.

### R3 (minor)
- **R3-1**: Thêm `context` vào `aios_core/__init__.py` (eager import + `__all__`, vị trí sau `contracts` — an toàn, 1 chiều context→memory).
- **R3-2**: `isinstance` check value của `context.get(EXECUTION, "memory.context")` là `MemoryContext` → sai type coi như None (tránh AttributeError cứng).
- **R3-3**: `str(sorted(v))` cho set hỗn hợp kiểu vẫn TypeError → `sorted(v, key=str)` hoặc bọc try/except.
- **R3-4**: YC-7 bổ sung 1 dòng: "P1 section rỗng vẫn emit header (C2-12) — ngoại lệ của 'tier rỗng → bỏ header'".
- **R3-5**: Scenario "P0 vượt cap": cần usable ≥ P0+P1 ≈ 3700 (không phải 3400). VD budget (system 3500, task 500, knowledge 600, history 800, artifacts 500, reserve 800) → usable 5900; seed P0 3600 + P1 100 → giữ nguyên, tier_reports ghi used > cap.

## Resolution ghi nhận (phản ánh trong spec v4 + implement)
- R1-1, R1-2 → spec v4 YC-6/§3 + test scenarios
- R2-1, R2-2 → spec v4 YC-6/YC-4
- R3-1..R3-5 → spec v4 (§8 artifacts, YC-2, YC-7) + implement
