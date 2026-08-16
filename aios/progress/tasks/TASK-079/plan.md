# TASK-079 — plan.md

> Tạo: 2026-08-15 · Trạng thái: **DONE**

## Yêu cầu người dùng

"ấn start xong thì mèo biến mất, không tương tác tiếp được" — bug game Yuniebel (TASK-078): sau START, nhân vật mèo không hiển thị, mọi scene không tương tác đúng.

## Chẩn đoán (bằng chứng)

- `sprites.js`: vẽ logical 160×90 (×3 → canvas 480×270). `core.js`: world gấp 3 (GARDEN/HALLWAY 960, còn lại 480). `drawPlayer` truyền world coords vào `drawCat` (logical) → mèo vẽ tại x ≈ world×3 → ngoài canvas 480px → biến mất.
- Background vẽ cố định 160 logical không khớp walls/zones world.
- Test 54/54 "PASS" vì test visual không có ảnh ref (brief chỉ có COMPARISON.md) → "17/17 khớp" là so với chính ảnh vừa chụp.

## Giải pháp

Chuyển toàn bộ core về logical grid (÷3): GARDEN/HALLWAY 320×90 (camera scroll), 5 scene còn lại 160×90. Mở rộng drawGarden/drawHallway với camera translate + save/restore. Sửa camX() (bỏ guard sc.w<=CW, giữ !sc). Cập nhật test (core/e2e/visual) + thêm 4 pixel tests chống tái phát.

## Kế hoạch

1. Hard gate: spec → critique ×3 (5+2+1 P1 resolved) → tasks → review trước implement (CHANGES REQUESTED → resolved R1-R5) → APPROVED
2. Implement: core.js (scene logical) → sprites.js (background khớp) → game.js (camera) → test (÷3 + pixel tests)
3. Test: 59/59 PASS (core 27 + smoke 4 + Playwright 28)
4. Review sau implement: Code APPROVED (10/10 AC)
5. Đóng checklist + commit

## Kết quả

**TASK-079 DONE** — mèo hiển thị sau START, chơi được trọn 6 cảnh, background khớp walls/zones, camera scroll hoạt động. 59/59 test PASS.
