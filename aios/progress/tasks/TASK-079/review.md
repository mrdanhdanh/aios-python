# Review — TASK-079 (trước implement)

> Ngày: 2026-08-15 · Reviewer: AIOS reviewer agent · Đối tượng: spec.md (sau critique ×3) + tasks.md
> Kết quả: **CHANGES REQUESTED → RESOLVED (R1-R5) → APPROVED**

## Tổng quan

Spec chẩn đoán đúng nguyên nhân gốc và hướng sửa đúng. Reviewer đã kiểm chứng lại toàn bộ tọa độ §3.1 (chia 3 từ code thật), 5 vị trí scare với camX mới (screen 130/110..150/107..147/103..143/140 — đều trong viewport), AC-1 region (cam=30 → canvas 231..279 ✓), 27 core test tọa độ — tất cả khớp.

## Đối chiếu AC (mức spec)

- AC-1 ✓ (catBody thực tế ~100px, region 30px an toàn)
- AC-2 ✓ (test e2e mới P3-3)
- AC-3 ✓ (2 e2e không hook giữ nguyên)
- AC-4 ✓ (chuyển visual pixel test)
- AC-5 ⚠ **thiếu trong tasks.md** (R4)
- AC-6/7/8/9 ✓ (P4-1/2/3)
- AC-10 ✓ (verify GARDEN cam=160 nhà screen 107..160; HALLWAY skull 140)
- **AC-14a/14b ⚠ cơ chế moveTo lỗi toán học (R1 — Blocking)**

## Các vấn đề

### R1 (Blocking) — moveTo Y-tolerance |dy|>2 với hold 120ms ≈ 4.7px → oscillation vô hạn + dải hạ cánh kẹt wall
- Bước lượng tử 4.7px vs tolerance 2 → d ∈ (2, 2.7) nhảy qua lại vĩnh viễn (Y luôn ưu tiên, X không di chuyển); dải [47.3, 48) chạm wall nhà (đáy 50) → kẹt.
- **Resolve**: moveTo HAI TẦNG — `|dy| > 12` → hold 120ms; `|dy| > 2` → hold **40ms** (≈1.6px < 2 → hội tụ |dy'| ≤ 2, y ∈ [48,52] ⊂ [48,66]); dừng khi |dx|<2 && |dy|<2; X hai tầng tương tự. ✅ spec §3.4.

### R2 (Major) — camX() phải thay TOÀN BỘ thân hàm
- Giữ guard `sc.w <= CW` (CW=480) → 320 ≤ 480 → camera chết (luôn 0); bỏ guard `!sc` → crash TITLE frame đầu.
- **Resolve**: thay toàn bộ — giữ `if (!sc) return 0;`, BỎ `sc.w <= CW`, công thức `max(0, min(player.x - 80 + 3, sc.w - 160))`. ✅ spec §3.3.

### R3 (Minor) — sky() phải nằm TRONG translate (sao/mặt trời cuộn theo camera)
- **Resolve**: bọc cả sky() trong save/translate/restore; sao trải 0..w−10. ✅ spec §3.2.

### R4 (Minor) — AC-5 "mèo hiện diện" thiếu trong tasks.md
- **Resolve**: thêm pixel check catBody trong 6 shot có player vào P3-5. ✅ tasks.md (cập nhật kèm).

### R5 (Minor) — Đèn hiên overlay y 36 vs sprite 38 — lệch 2px dọc
- **Resolve**: overlay → `38 * S.GX`. ✅ spec §3.3.

## Kết luận

**CHANGES REQUESTED → đã resolve R1-R5 vào spec (R1/R2: spec §3.3/§3.4; R3: §3.2; R4: tasks.md; R5: §3.3). APPROVED — được phép implement.** Không còn blocking.
