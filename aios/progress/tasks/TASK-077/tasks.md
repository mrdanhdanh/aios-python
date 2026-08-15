# TASK-077 — tasks.md (breakdown)

> Hard gate: spec ✅ (critique-1: C1-01..04 resolved; critique-2: C2-11..22 resolved). Review trước implement.

## Checklist

### P1 — Khung project & core logic (testable)
- [x] Tạo thư mục `games/yuniebel/` + `src/` + `test/`
- [ ] `src/core.js` — UMD module, logic thuần:
  - [ ] Dữ liệu: scenes (map size, walls, zones, spawn), phases, tasks (text), dialogues
  - [ ] `resetGame()` — trả state mới, reset toàn bộ (scene, phase, flags, scare counter, darkness, timers, audio flags)
  - [ ] Di chuyển: `stepPlayer(state, dx, dy, dt)` — clamp dt ≤ 50ms, speed 120 px/s, collision slide (tách X/Y), biên map
  - [ ] Trigger: `checkTriggers(state, player)` — zone active theo phase, fire-once, ưu tiên knockback trước chuyển cảnh
  - [ ] State machine: `updateGame(state, dt, input)` — xử lý phase timers (accumulator), transitions, GARDEN chuỗi 4 phase, KITCHEN 2 nhánh, HAUNTED knockback, HALLWAY 5 scare fire-once + counter, DINING cutscene phases
  - [ ] Light radius: `computeLight(state, x, y)` — 90px, chỉ HAUNTED/HALLWAY
  - [ ] Bướm AI: `updateButterfly(state, dt)` — pattern sin, tránh mèo < 60px (85 px/s), biên map
- [ ] `test/core.test.js` — node test (assert thủ công, exit code):
  - [ ] 4 hướng di chuyển + biên map + clamp
  - [ ] Collision vật cản không xuyên + trượt dọc tường + knockback không xuyên
  - [ ] Chuỗi GARDEN: G_INIT → G_BUTTERFLY (cửa khóa) → G_CHASE → G_DARK (darkness 0→1 trong 5s) → G_DOOR → LIVING
  - [ ] KITCHEN: K_BLOOD → K_VOICE → K_CHOICE; [1] → K_RUN → HAUNTED; [2] → K_OBEY → GAMEOVER; đi vào vùng tối = K_OBEY
  - [ ] HAUNTED: cửa trước knockback + không chuyển cảnh; cửa hành lang → HALLWAY
  - [ ] HALLWAY: 5 scare fire-once (không fire lặp), sau 5 → W_DONE mở cửa
  - [ ] DINING: chuỗi cutscene D_APPROACH → D_JUMP → D_HUG → D_CAKE → D_END
  - [ ] resetGame 2 lần liên tục không lỗi + reset sạch mọi state
  - [ ] Không dt → không transition (timer chỉ tăng khi step)

### P2 — Sprites & render (browser)
- [ ] `src/sprites.js` — pixel maps 16×16 (palette ≤ 16 màu): mèo tóc hồng (idle/walk 2 frame, mirror trái/phải), bướm 2 frame, chủ (idle/ôm), hồn ma 2 frame, bánh kem 2 frame, cửa khóa/mở, bàn, vết máu, mây 2 frame, mặt trời, cây, hoa, heart 2 frame, mũi tên, vùng tối; hàm `drawSprite(ctx, name, x, y, frame, flip)`
- [ ] Render scenes: TITLE (bầu trời xanh + mây bay + mặt trời), GARDEN (cỏ, nhà, cửa, cây, hoa), LIVING (sofa, thảm, TV, cửa sổ, 2 cửa), KITCHEN (tủ, bàn, chậu rửa, vết máu, vùng tối), HAUNTED (LIVING tối + sương + hồn ma canh cửa + mũi tên), HALLWAY (hành lang dài, cửa 2 đầu, scare props), DINING (bàn, chủ ngồi, nến)
- [ ] Camera follow + clamp; vẽ walls/zones debug (tắt mặc định)

### P3 — Audio (browser)
- [ ] `src/audio.js` — WebAudio: meow (2 tone), scare (noise burst + low boom), chime (3 note); init sau gesture đầu; mute nếu lỗi; `ctx.resume()` khi gesture

### P4 — Game loop & UI (browser)
- [ ] `src/game.js` — rAF loop + dt accumulator (clamp 50ms), key state Set (bỏ e.repeat, preventDefault WASD/arrows, clear on blur/visibilitychange), d-pad ảo (touchstart/touchend, hiện khi ontouchstart, ẩn hint bàn phím), camera, vẽ scenes + sprites + darkness/light radius, fade 0.5s, inputLocked per phase, phím 1/2 chỉ khi K_CHOICE, nút X luôn hoạt động → resetGame
- [ ] UI overlay (HTML/CSS): khung nhiệm vụ (góc trên trái + nút X), nút bật/tắt UI (góc trên phải), hộp thoại/bubble, hộp lựa chọn [1]/[2], counter "Bị hù: x/5", Game Over screen, END screen, title START
- [ ] `index.html` + `style.css`: script classic + relative path, canvas 480×270 letterbox, image-rendering: pixelated, font monospace

### P5 — Deploy & tài liệu
- [ ] `.github/workflows/pages.yml` (trigger [master, main] paths games/** + workflow_dispatch, permissions pages, upload path games)
- [ ] `README.md` ngắn trong games/yuniebel/ (cách chơi, link Pages)
- [ ] `test.md` — kết quả node test + manual checklist 15 bước
- [ ] `evaluation.md` — đối chiếu AC1..17
- [ ] Cập nhật LOG.md + PROGRESS.md + commit
