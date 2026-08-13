# Review — TASK-016 (Architecture Hardening)

> Ngày: 2026-08-13 | Reviewer: reviewer agent | Giai đoạn: REVIEW TRƯỚC KHI IMPLEMENT
> Spec đã qua critique ×2 (23 vấn đề resolved). Reviewer đã verify trên code thật: planner.py import đúng allow-list (models.base + models.errors), execution.py có call-site `_policy.evaluate` (dòng 138), 4 business services emit EventType, baseline 490 passed / 95.96%, gap sandbox thật (execution.py:153-154 logger.warning), ADR 0001-0003 format.

## Kết luận

- [x] **CHANGES REQUESTED** — 1 blocking + 2 khuyến nghị (đã sửa vào spec):

**R1 (Blocking):** `SRC_ROOT = Path(__file__).resolve().parents[2] / "src"` từ `backend/tests/` → `AIAGENT/src` (không tồn tại). **Fix: `parents[1] / "src"`** (= `backend/src`) + guard `assert (SRC_ROOT / "aios_core").is_dir()` fail-fast (không bao giờ skip âm thầm).

**R2 (Major):** Absolute import `import aios_core.models` nếu lưu top-level `aios_core` sẽ MISS dot-boundary target `aios_core.models`. **Fix: `aios_core_modules` lưu FULL dotted name cho cả absolute lẫn relative; `assert_no_imports` check 2 chiều** (`mod == target or mod.startswith(target + ".") or target.startswith(mod + ".")`); external_top_level chỉ cho target ngoài (langgraph/openai/ollama).

**R5 (Minor):** Section 8 còn text cũ "5 service emit" — đồng bộ: **4 business services** (execution/artifacts/permissions/policy), events.py = infrastructure.

## Ghi chú khác (đã áp dụng khi implement)

- INV-007 call-site: dùng `ast.walk` tìm `ast.Attribute` (`_policy` + `.evaluate`), không regex text
- Relative resolve theo module_rel của từng Import node
- Loại `module == "__future__"` khỏi kết quả
- architecture.md: thêm §7 sau §6, giữ mermaid, sửa 4 chỗ stale (151, 156, 176-177, 194), T5→T6→T7 thành 1 chiều
- ADR-0004: format 0001-0003, không copy architecture.md, ghi gap sandbox
- Ngoại lệ lưu ý: `kernel/runtime_kernel.py` import `from ..models import MockModel` (models trần) — ngoài phạm vi mọi rule (kernel = infra); nếu mở rộng rule kernel/ phải exclude file này
