# test/brief — Hướng dẫn đối chiếu ảnh tham khảo (AC-12)

## Cách hoạt động

1. **Đặt ảnh ref** (nếu có): đặt ảnh chụp màn hình từ brief người dùng vào thư mục này, tên khớp ảnh chụp: `title.png`, `garden-day.png`, `garden-dusk.png`, `garden-night.png`, `living.png`, `kitchen-blood.png`, `kitchen-choice.png`, `haunted-ghost.png`, `haunted-block.png`, `hallway-scare1..5.png`, `birthday.png`, `gameover.png`, `end.png`.
2. **Chạy**: `npx playwright test` — visual.spec.js sẽ:
   - Chụp 17 ảnh từ game vào `test-results/shots/` (luôn chạy — AC-11)
   - Nếu ảnh ref tồn tại trong `test/brief/` → so sánh pixel bằng `toHaveScreenshot` (maxDiffPixelRatio 0.02)
   - Nếu THIẾU ảnh ref → **test.skip** (không fail) — theo C1-12
3. **Bảng kết quả** được ghi tay vào `COMPARISON.md` sau khi xem ảnh chụp (bắt buộc — gate cuối P3, không thể bỏ).

## Lưu ý

- Ảnh chụp = canvas 480×270 (clip đúng canvas — C2-13), vị trí camera theo state set trong bảng §8.1.
- Ảnh ref gốc là file đính kèm chat người dùng (không nằm trong repo) — mô tả chuẩn nằm ở `aios/progress/tasks/TASK-078/implementation/brief-visuals.md`.
- Ảnh chụp đã copy vào `aios/progress/tasks/TASK-078/shots/` làm bằng chứng.
