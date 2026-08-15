# Critique vòng 1 — TASK-079 (critic độc lập)

> Ngày: 2026-08-15 · Critic: AIOS critic agent · Đối tượng: `spec.md` (bản trước cập nhật)
> Trạng thái sau khi resolve: **TẤT CẢ đã resolve — không còn P1/P2 chưa xử lý** (cập nhật vào spec.md)

## Tổng hợp phản biện

Chẩn đoán nguyên nhân gốc (world vs logical, test "màu xanh") chính xác. Hướng sửa đúng. Tuy nhiên spec ban đầu chỉ chia tọa độ, chưa thiết kế lại hình học chơi được: 3 spawn kẹt, 2 cửa trái không đến được bằng `moveTo`, camera chưa nối vào background.

## P1 — Chặn implement (5)

### P1-1 — KITCHEN spawn (80,77) ngoài biên → kẹt cứng
- Hitbox `(83,79,10,12)` → bottom 91 > 90 (map h=90) → mọi hướng bị chặn; ở 60fps (dt≈16.7ms, di chuyển 0.67px < 1px) mèo kẹt vĩnh viễn → e2e fail.
- **Resolve**: spawn → `(80,73)` (hitbox bottom 87 ≤ 90; vẫn chồng blood zone (50,78,40,8) → K_INIT auto-fire giữ nguyên). ✅ Đã cập nhật spec §3.1.

### P1-2 — HAUNTED spawn (80,63) nằm TRONG wall bàn (67,68,20,4)
- Hitbox `(83,65,10,12)` chồng x 83..93 vs 67..87, y 65..77 vs 68..72 → kẹt 4 hướng, không thoát được.
- **Resolve**: spawn → `(90,63)` (hitbox x 93..103 > 87 — clear bàn). ✅ spec §3.1 + shot visual haunted (P2-5).

### P1-3 — Cửa trái LIVING (3,30,11,20) / HAUNTED (2,30,11,20) sát đỉnh sofa → moveTo kẹt
- Từ spawn, `moveTo` ưu tiên Y dừng tại y≈48.6/45.6 → hitbox chồng sofa (y 53..68) → chặn ngang, 60 bước hết → fail.
- **Resolve**: giữ zone, đổi target e2e lên lối trên: LIVING `(7,20)` (mèo dừng y≈29.4, hitbox 31.4..43.4 clear sofa, chạm door_kitchen y 30..50 ✓); HAUNTED `(3,20)` (tương tự, chạm door_side ✓). Đã verify hitbox 10×12 + thuật toán moveTo. ✅ spec §3.4.

### P1-4 — Camera không nối vào drawGarden/drawHallway → nền 320 không scroll
- `drawScene` gọi `S.drawGarden(ctx, state, time)` — không có cam; nếu vẽ 0..320 cố định thì chỉ hiện 0..160 → nhà (267..320) và scare (160..300) không bao giờ hiện — tái phạm đúng loại bug đang sửa.
- **Resolve**: `drawGarden(ctx, state, time, cx)` + `drawHallway(ctx, state, time, cx)` — `ctx.translate(-cx*GX, 0)` trước khi vẽ, clip tự nhiên. `drawScene` truyền `cx`. ✅ spec §3.2/§3.3.

### P1-5 — `S.drawBlood(ctx, 68, 66, ...)` trong game.js bị bỏ sót
- Sau khi dời máu về (50,78) trong drawKitchen, dòng này vẫn vẽ vệt máu thừa tại (68,66).
- **Resolve**: XÓA dòng trong `drawScene` (drawKitchen đã vẽ máu + drip). ✅ spec §3.3.

## P2 — Nên sửa (10)

| # | Vấn đề | Resolve |
|---|--------|---------|
| P2-1 | Spawn bướm (700,140) + debug setButterfly (700,150) chưa đặc tả chia 3 | Spawn bướm `(233,47)`; debug default `(233,50)` ✅ |
| P2-2 | AC-2 không có test tương ứng | Thêm test e2e: hold "d" 1s → player.x tăng ✅ |
| P2-3 | AC-4 hứa "unit test mới" nhưng §3.4 không plan | Chuyển AC-4 thành visual pixel test (wallCream/roofRed hiện khi player x=300) ✅ |
| P2-4 | Visual kitchen (73,77) ngoài biên, mèo cắt đáy | → `(73,70)` (hitbox bottom 84 ≤ 90, vẫn trong blood zone) ✅ |
| P2-5 | Visual haunted (80,63) mèo đè bàn | → `(90,63)` ✅ |
| P2-6 | Không AC kiểm camera scroll | Thêm AC-10: GARDEN player(300,50) → pixel nhà hiện; HALLWAY player(300,45) → tường/scare hiện ✅ |
| P2-7 | Test "Không xuyên tường" (263,50) mất ý nghĩa (hitbox y 52..64 không chồng wall y 7..50) | → `(263,30)` (hitbox y 32..44 chồng ✓); ghi chú gap thiết kế: mèo có thể đi sát chân tường dưới hiên (chấp nhận) ✅ |
| P2-8 | Vùng tối vẽ (5,5,34,38) lệch DARK_RECT mới (7,7,31,33) | Vẽ đúng `(7,7,31,33)` + mắt (17,19)/(23,19) ✅ |
| P2-9 | Scare2 tại 170 chỉ lộ 1px khi kích hoạt (cam≈11 → screen 159) | → `160` (screen 150 khi trigger) ✅ |
| P2-10 | Risk section math sai (300/183/130 vs scare4=260) | Viết lại: cam max 160; scare1 cam 0 → 130; scare2 cam 10 → 150; scare3 → 104..144; scare4 → 100..140; scare5 cam 160 → 140 ✅ |

## P3 — Góp ý (6)

| # | Ý kiến | Resolve |
|---|--------|---------|
| P3-1 | AC-1 cần rect pixel + số pixel tối thiểu | Canvas region (321..369, 210..258) ≥ 30 px `#f5a623` ✅ |
| P3-2 | Comment e2e "120px/s đuổi 60px/s" | → 40/20 ✅ |
| P3-3 | Core.test "Chạm vết máu" (63,80) bất hợp pháp | → `(63,73)` ✅ |
| P3-4 | Đèn hiên 287 vs 288 lệch 1px | Thống nhất 287 (cả sprites lẫn overlay game.js) ✅ |
| P3-5 | sky sao "w % 310" mơ hồ | → `sx = (i*37+13) % (w-10)` ✅ |
| P3-6 | Bụi3 (207,85,9,4) đáy 89 — đừng làm tròn h=5 | Giữ h=4 ✅ |

## Kết luận

**Vòng 1: RESOLVED 5/5 P1 + 10/10 P2 + 6/6 P3** — spec đã được cập nhật theo từng mục. Chuyển sang vòng critique 2.
