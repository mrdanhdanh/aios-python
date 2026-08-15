# TASK-079 — evaluation.md

> Ngày: 2026-08-15 · Đối chiếu tiêu chí chấp nhận spec.md §5

## Kết quả: 10/10 AC ĐẠT

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC-1 | Mèo hiển thị sau START tại spawn (pixel #f5a623 ≥ 30 px trong region 231..279, 210..258) | ✅ PASS |
| AC-2 | Mèo di chuyển bằng WASD (hold d 1s → x tăng > 10) | ✅ PASS |
| AC-3 | Chơi hết game title→sinh nhật + title→game over (không hook) | ✅ PASS (45s / 22s) |
| AC-4 | Background khớp walls: nhà vẽ 267..320, wallCream/roofRed hiện khi cam=160 | ✅ PASS |
| AC-5 | 17 shot chụp được + mèo hiện diện 6 shot có player | ✅ PASS |
| AC-6 | core.test.js 27/27 | ✅ PASS |
| AC-7 | smoke.test.js 4/4 | ✅ PASS |
| AC-8 | Playwright 28/28 | ✅ PASS |
| AC-9 | Không crash console/pageerror | ✅ PASS |
| AC-10 | Camera scroll GARDEN + HALLWAY scare5 | ✅ PASS |

## Quy trình hard gate

- [x] Plan → plan.md
- [x] Spec → spec.md (10 AC)
- [x] Critique ×3 → critique-1.md (5 P1 + 10 P2 + 6 P3 resolved) → critique-2.md (2 P1 + 1 P2 + 6 P3 resolved) → critique-3.md xác nhận (1 P1 + 1 P2 + 3 P3 resolved) — **đủ 3 vòng, không còn P1/P2**
- [x] Task → tasks.md (P0-P4, 20 checkbox)
- [x] Review trước → review.md (CHANGES REQUESTED: R1 moveTo oscillation blocking → resolved hai tầng 120/40ms; R2 camX guard → resolved; R3-R5 → resolved) → APPROVED
- [x] Implement → core.js/sprites.js/game.js + 3 test files
- [x] Test → test.md + 59/59 PASS
- [x] Review sau → review-post.md (Code APPROVED — 10/10 AC)

## Ghi nhận lệch spec (cosmetic — review-post R2/R3)

1. Owner vẽ khi `G_INIT && dialogue` (spec: "khi G_INIT") — giữ hành vi gốc TASK-078: chủ nhân xuất hiện trong hội thoại đầu rồi biến mất khi hết thoại. Cosmetic.
2. Hàng rào GARDEN trải x 8..280 (16 cọc) thay vì 0..320 — khi cam=160 đoạn 280..320 không có rào. Cosmetic.
3. Mắt vùng tối (25,19) thay vì (23,19) — đối xứng quanh tâm, chấp nhận.
4. Cửa tối vẽ y 36..60 (hở 3px so wall y 30..33) — decorative.
5. `drawBlood` còn định nghĩa + export (dead code — không còn chỗ gọi) — giữ tương thích.
6. Kệ LIVING (126,62,12,24) cao hơn spec (126,70,12,17) — bao phủ wall đủ.

## Bài học

1. **Test "so với chính nó" là vô nghĩa**: TASK-078 tuyên bố "17/17 khớp brief" nhưng brief không có ảnh ref — `toHaveScreenshot` bị skip. Bài học: mọi visual test phải có baseline độc lập hoặc pixel assertion cụ thể (màu + region).
2. **Scale mismatch là class bug âm thầm**: khi sprite scale (GX=3) khác world scale — mọi thứ render lệch nhưng logic test vẫn xanh. Bài học: luôn có 1 unit test đối chiếu tọa độ render vs collision (AC-4 pixel test).
3. **Critique ×3 + review 2 vòng bắt được lỗi tinh vi**: moveTo oscillation (bước 4.7px vs tolerance 2), wall chặn đường (đáy 50 vs landing y<48), camera guard cũ giết camera — chỉ có số học kiểm tra kỹ mới ra. Giá trị của hard gate được chứng minh.
4. **E2E phải mô phỏng động học thật**: "chạm zone" ≠ "đi được tới zone" — phải trace đường đi với hitbox + thuật toán điều khiển.

## Thống kê

- File thay đổi: 6 (core.js, sprites.js, game.js, core.test.js, e2e.spec.js, visual.spec.js)
- Test: 54/54 (cũ) → **59/59 (mới)** — +5 test (AC-2, AC-1, AC-4, AC-10, AC-5 pixel)
- Chụp ảnh xác nhận: mèo hiện sau START ✓, nhà hiện khi cam=160 ✓, skull scare5 ✓
