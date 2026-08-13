# Review — TASK-013 (M2-P3c: Assistants)

> Ngày: 2026-08-13 | Reviewer: reviewer agent | Giai đoạn: REVIEW TRƯỚC KHI IMPLEMENT
> Spec đã qua critique ×2 (25 vấn đề resolved). Reviewer verify code thật: baseline 502+2, EventType strings khớp, DEFAULT_MAP 4 cặp khớp, ModelContract.chat khớp, collect_imports resolve relative → phát hiện 2 mâu thuẫn nội tại.

## Kết luận

- [x] **CHANGES REQUESTED** — 2 blocking + 1 Major + 6 Minor (đã sửa vào spec):

**R1.1 (Blocking) — AC9 KB-miss dead code**: extractor union(active KB, DANGER) — keyword match không có trong KB bắt buộc là danger → emergency (AC8c), không bao giờ see_doctor. **Fix (a)**: keyword nguồn = `union(DEFAULT_KB keys, active KB keys, DANGER_KEYWORDS)` — KB inject chỉ thay lookup, không thu hẹp extractor. Test AC9: inject KB chỉ `{"ho": ...}` + text "tôi bị đau đầu" → "đau đầu" match (từ default KB) → lookup miss → conditions=[] + risk=low + `see_doctor` + `need_more_info=True`.

**R1.2 (Blocking) — Allow-list test fail với intra-package imports**: `from .base import X` resolve thành `aios_core.agents.base` — nằm trong aios_mods → subset check fail. **Fix**: loại trừ `aios_core.agents*` khỏi aios_mods TRƯỚC khi check subset (chỉ kiểm imports RA NGOÀI agents/).

**R2 (Major) — `DoctorAssessment.risk` default "low" mâu thuẫn (d) "assessment rỗng"**: field risk luôn có giá trị. Fix: test AC8(d) assert trên response text + metadata (không có key risk/conditions/recommendation), KHÔNG assert field `assessment.risk`.

**R3 (Minor)**: (1) empty-text path không emit event — chốt trong test; (2) AC8(b) assert "không chứa tên thuốc" phải nhắm tên cụ thể (paracetamol/mg), không assert từ "thuốc"; (3) "degraded" không tồn tại trong probe contract `{"ok", "detail"}` — viết lại "entry thiếu ok (vd chỉ có status='degraded') → coi fail"; (4) `aios_core/__init__.py` thêm `agents` SAU `models`; (5) step contract ghi rõ step unit/integration PHẢI trả key "passed"; (6) cosmetic.

## Phần 1: AC ↔ test

12/12 AC có test tương ứng khả thi sau fix R1.1/R1.2 (bảng đầy đủ trong quá trình review: AC1-12 ↔ test files).

## Phần 2: Rủi ro top 3

1. R1.1 KB-miss dead code → fix extractor union 3 nguồn
2. R1.2 allow-list intra-package → exclude aios_core.agents*
3. R2 risk default → assert tầng response/metadata

## Phần 3: Ràng buộc

- Baseline 502 passed + 2 skipped (verify thật) — không regression
- 0 skip sau task (INV-001/002 tự bật khi agents/ tồn tại)
- Coverage agents/ ≥ 80% — 5 file test phủ 7 module
- Không model mặc định — chỉ GeneralAssistant optional (MockModel)
