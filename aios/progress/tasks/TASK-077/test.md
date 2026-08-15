# Test results — TASK-077 (Webgame Yuniebel)

## Node test (logic thuần — core.js)
```
=== TASK-077 core tests ===
PASS: 58 / 58
```
**Exit code: 0** — PASS

## Smoke test (jsdom browser simulation)
```
=== TASK-077 smoke tests ===
PASS: 28 / 28
```
**Exit code: 0** — PASS

Covers: game loaded, START→GARDEN, task box, WASD input, resetGame (nút X), toggle UI, render 14 cảnh không crash.

## Manual checklist (cần test khi mở trình duyệt)
- [ ] Mở index.html bằng file:// → chơi được
- [ ] Title: bầu trời xanh + mây + mặt trời + START
- [ ] Mèo orange tóc hồng, di chuyển WASD
- [ ] Cảnh 1: vườn → cửa → bướm → đuổi → tối → vào nhà
- [ ] Cảnh 2: phòng khách → cửa bếp
- [ ] Cảnh 3: máu → lời gọi → chọn [1] → HAUNTED; [2] → GAME OVER
- [ ] Cảnh 4: ma → knockback cửa trước → cửa hành lang
- [ ] Cảnh 5: 5 scare → phòng ăn
- [ ] Cảnh 6: cutscene → sinh nhật → END
- [ ] Nút X → Title (reset sạch)
- [ ] D-pad mobile hiện khi touch
- [ ] DevTools → Network: không có external request

## Kết quả
- **Node test: 58/58 PASS**
- **Smoke test: 28/28 PASS**
- **Manual: cần test khi mở browser**
- **Không có lỗi syntax (VS Code linter check: 0 errors)**
