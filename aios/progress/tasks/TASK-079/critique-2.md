# Critique vòng 2 — TASK-079 (critic độc lập, spec đã cập nhật sau vòng 1)

> Ngày: 2026-08-15 · Critic: AIOS critic agent · Đối tượng: `spec.md` (bản sau vòng 1)
> Trạng thái sau resolve: **RESOLVED 2/2 P1 + 1/1 P2 + 6/6 P3 — không còn P1/P2** (cập nhật vào spec.md, ghi chú `C2-`)

## Verify các resolution vòng 1 (đều ĐÚNG)

- KITCHEN spawn (80,73): hitbox 83..93/75..87, đáy 87 ≤ 90 ✓; chồng blood zone (50..90, 78..86) → K_INIT auto-fire ✓
- HAUNTED spawn (90,63): hitbox x 93..103 > 87 (bàn) ✓; ≤ 144 (clamp) ✓
- Lối (7,20)/(3,20): mèo dừng y≈29.4, hitbox 31.4..43.4 clear sofa, chạm door_kitchen khi x<11 ✓
- 5 scare: trigger p.x≈34/87/140/194/247 → cam 0/10/63/117/160 → screen 130/150/147/143/140 — đều trong viewport ✓
- Mọi tọa độ core.test.js ÷3 đã tính lại — chạm đúng zone ✓
- AC-10: GARDEN (300,50) → cam 160 → nhà screen 107..160 ✓; HALLWAY (300,45) → scare5 screen 140 ✓

## Các vấn đề mới (vòng 2)

### P1-1 — AC-1 pixel region sai với chính camX() của spec
- Tại spawn (107,70): camX = clamp(107−77, 0, 160) = **30** → mèo screen x = 77 → canvas **231..279** (y 210..258 đúng). Region cũ (321..369) = screen 107..123 — không chứa mèo → AC-1 fail ngay lần đầu.
- **Resolve**: region → **(231..279, 210..258)**. ✅ spec §5 AC-1.

### P1-2 — ctx.translate(-cx*GX, 0) thiếu save/restore → transform rò rỉ toàn render
- Không restore: drawPlayer lệch kép (p.x−cx−cx), clearRect xóa lệch frame sau (bẩn tích lũy), overlay screen-space (dark/lamp/scare/flash) sai tọa độ — đúng class bug gốc.
- **Resolve**: ghi bắt buộc `ctx.save(); ctx.translate(-cx*S.GX, 0); ... ctx.restore();` quanh phần vẽ map trong drawGarden + drawHallway. ✅ spec §3.2.

### P2-1 — e2e cửa GARDEN (288,59) fail nếu catch bướm tại mèo y ∈ [66,74]
- `moveTo` chỉ sửa Y khi |dy| > 12: từ y=67..74 → đi ngang vĩnh viễn, hitbox top ≥ 68.2 > 68 (đáy door zone y 48..68) → không chạm zone → fail. Catch bướm leg đáy (180,63) cho touch tại y ≤ ~69 — trùng window → flaky thật.
- **Resolve**: target → **(288,50)** — verify mọi y ∈ [0,90] (y=67 → 57.4 hitbox 59.4..71.4 chạm ✓; y=30 → 39.6 hitbox 41.6..53.6 chạm ✓). Áp dụng cả AC-14a lẫn AC-14b. ✅ spec §3.4.

### P3 (6 — resolve vào spec)
| # | Ý kiến | Resolve |
|---|--------|---------|
| P3-1 | §3.2 đèn hiên (288,38) vs overlay 287 — lệch 1px | Thống nhất **(287,38)** ✅ |
| P3-2 | Nhánh máu (58,91,14,3) ngoài canvas (y 91..94 > 90) | → nhánh (54,86,26,3) + chấm (66,86,6,2) — tất cả y ≤ 90 ✅ |
| P3-3 | Risk scare3: cam 63..103 → screen 107..147 (không phải 66..106/104..144) | Sửa số liệu risk section ✅ |
| P3-4 | BUTTERFLY_CATCH 12→4 vô hiệu (hằng không dùng) | Ghi chú cosmetic trong bảng hằng số ✅ |
| P3-5 | AC-10 HALLWAY cần `setScareZone(5)` + freeze | Bổ sung rõ ✅ |
| P3-6 | drawKitchen tủ bếp trái (0,10,80,22) — đường mèo tới vùng tối chồng | Quyết định: GIỮ NGUYÊN (mèo vẽ đè — chấp nhận), ghi chú ✅ |

## Kết luận

**Vòng 2: RESOLVED 2/2 P1 + 1/1 P2 + 6/6 P3 — spec không còn P1/P2.**

Theo khuyến nghị critic, spec cần 1 vòng xác nhận cuối (vòng 3) trước khi implement.
