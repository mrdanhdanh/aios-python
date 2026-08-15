# TASK-078 — Làm lại hoàn toàn game "Yuniebel's Cat" theo kịch bản chi tiết + 5 ảnh tham khảo

> Trạng thái: `in-progress` (plan + spec) → critique ×2 → tasks → review → implement → test (chụp ảnh so brief) → evaluate

## Lý do

- TASK-077 (game cũ) bị người dùng đánh giá **"làm xấu quá"** → yêu cầu **làm lại từ đầu**.
- Người dùng gửi **kịch bản chi tiết** (6 cảnh + title/game over) + **5 ảnh tham khảo** (title screen, sân vườn 3 mốc thời gian, phòng khách + nhà bếp, phòng khách ma ám, hành lang 5 jump scare).
- Yêu cầu test: **chụp ảnh màn hình thật và đối chiếu với brief/ảnh tham khảo** (không test hời hợt).

## Phạm vi

- Viết lại TOÀN BỘ `games/yuniebel/` (index.html, style.css, src/core.js, src/sprites.js, src/audio.js, src/game.js, test/*).
- Game chạy 100% static, 0 dependency, file:// + GitHub Pages.
- Đồ họa: canvas primitives theo palette 5 ảnh tham khảo (không dùng ma trận ký tự 16×16 như bản cũ).
- Âm thanh: WebAudio synth đầy đủ theo kịch bản (nhạc nền theo mood từng cảnh + SFX).
- Test: Node unit test (logic thuần) + Playwright e2e chụp screenshot từng cảnh, đối chiếu brief, ảnh lưu trong task folder.

## Tiêu chí chấp nhận (sẽ chi tiết hóa trong spec.md)

1. Đủ 8 màn hình: title / garden (ngày→hoàng hôn→đêm) / living / kitchen (lựa chọn) / haunted / hallway (5 jump scare) / birthday / game over.
2. Hội thoại đúng 100% từ ngữ kịch bản (tiếng Việt).
3. Nhiệm vụ hiển thị đúng từng phase.
4. Đồ họa bám sát 5 ảnh tham khảo (palette, bố cục, vật thể).
5. Âm thanh đầy đủ theo kịch bản.
6. Screenshot test: chụp thật mọi cảnh → đối chiếu brief → lưu ảnh + kết quả.
