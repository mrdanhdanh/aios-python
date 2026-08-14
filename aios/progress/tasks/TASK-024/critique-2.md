# Critique vòng 2 — TASK-024 (Context Optimizer)

**Critic**: subagent critic | **Ngày**: 2026-08-14 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
C1-01 ⚠️ MÂU THUẪN MỚI (merge dead code → C2-02 P2) · C1-02 ✅ RESOLVED ĐÚNG · C2-01 ✅ RESOLVED ĐÚNG · C2-02 ⚠️ RESOLVED có lỗ hổng (container bệnh lý → C2-03 P2) · C2-03 ⚠️ RESOLVED MỘT PHẦN (không carry vào YC-5 L3 → C2-05 P2) · C2-04 ⚠️ RESOLVED MỘT PHẦN (tokens=0 chưa ghi YC-1/YC-2 → C2-12 P3) · C3-05 ✅ · C3-06 ✅ · C3-07 ✅ · C3-08 ✅ · C3-09 ✅

## Mục B — Vấn đề mới

### P1
**C2-01**: `json` thiếu trong external allow-list §5.2 — YC-2 bắt buộc `json.dumps` nhưng allow-list không có → AC11 chắc chắn fail.
→ **Resolution**: thêm `"json"` vào external allowed §5.2.

### P2
**C2-02**: Merge stage (L1.3) là dead code — source per-key unique → không bao giờ có 2 section cùng (tier, source) từ input thật.
→ **Resolution**: chọn (a): ghi rõ "với mapping source per-key hiện tại, merge không fire trên input thật — giữ hàm thuần + unit test như defensive (PLAN §6 yêu cầu merge); sửa AC3 + YC-3 test chú thích pure-function test".

**C2-03**: `_serialize_value` crash trên container bệnh lý (dict key hỗn hợp kiểu + sort_keys → TypeError; self-reference → ValueError; str(set) phụ thuộc hash seed).
→ **Resolution**: wrap `json.dumps` trong try/except (TypeError, ValueError) → fallback `f"<{type(v).__name__}>"`; set/frozenset → `str(sorted(v))`. Test: dict key int+str, set, self-reference → không crash.

**C2-04**: Thứ tự nội bộ P2 (state keys vs session memory) chưa định nghĩa → cut mơ hồ.
→ **Resolution**: "P2 = state keys theo insertion order `get_all`, SAU ĐÓ session items theo rank desc → cắt từ cuối = session score thấp nhất trước, rồi state keys cuối". Thêm assert test.

**C2-05**: Re-token sau L3 không được carry vào YC-5.
→ **Resolution**: thêm YC-5 "sau L3, re-token mọi section (C2-03)" + test compressor đổi content dài gấp đôi → token cập nhật → cut đúng.

**C2-06**: Test INV-012 seeding tự mâu thuẫn (usable 2000 không nêu budget; P5 bị per-tier cap loại trước khi total cut; test P0-vượt-cap cần usable ≥ 3300).
→ **Resolution**: nêu budget cụ thể từng scenario. Scenario thứ tự: `system 400 / task 500 / knowledge 600 / history 800 / artifacts 500 / reserve 800` → usable 2000; seed P4 400 + P5 300 = 700 ≤ 800 ✓; total 3000 → drop P6(500) → P5(300) → P4(400) → 1800 ✓. Scenario P0-vượt-cap dùng budget riêng (usable ≥ 3400).

**C2-07**: Section đơn vượt cap bị drop trắng — mất toàn bộ state P2 (không truncate ngẫu nhiên — PLAN §5).
→ **Resolution**: với section đơn > cap tier: giữ prefix `content[:X-1] + "…"` (X chars = cap_tokens × 4) thay vì drop — deterministic.

### P3
- **C2-08**: AC3 thêm "merge trừ source `memory.*`" + "P0/P1 không là victim dedup".
- **C2-09**: Test `force_extractive=True` + terms rỗng → no-op, `levels_used == [1]`.
- **C2-10**: Pre-check chạy SAU L2/L3 trên token đã re-token — ghi rõ.
- **C2-11**: `levels_used` thêm khả năng `[1,3]`.
- **C2-12**: YC-1 comment "tokens set tại build (content rỗng → 0)"; YC-7 render P1 rỗng: header vẫn emit, không có dòng content.
- **C2-13**: `TierBudgetReport.cap=None` comment rõ "uncapped (P1) hoặc shared cap ghi ở tier khác (P5 → P4)".
- **C2-14**: Edge test "vượt đúng 2 token sau re-token → cut dừng đúng, không cắt thừa".
- **C2-15**: `truncated` chỉ phản ánh drop section (force_extractive không làm truncated=True) — ghi 1 dòng.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C2-01 (P1) + C2-02..C2-07 (P2) + P3 → spec v3. Sau vòng này **approve** (không cần critique vòng 3 — không có vấn đề thiết kế lại).
