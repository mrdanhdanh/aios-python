# TASK-077 ΓÇö tasks.md (breakdown)

> Hard gate: spec Γ£à (critique-1: C1-01..04 resolved; critique-2: C2-11..22 resolved). Review tr╞░ß╗¢c implement.

## Checklist

### P1 ΓÇö Khung project & core logic (testable)
- [x] Tß║ío th╞░ mß╗Ñc `games/yuniebel/` + `src/` + `test/`
- [ ] `src/core.js` ΓÇö UMD module, logic thuß║ºn:
  - [ ] Dß╗» liß╗çu: scenes (map size, walls, zones, spawn), phases, tasks (text), dialogues
  - [ ] `resetGame()` ΓÇö trß║ú state mß╗¢i, reset to├án bß╗Ö (scene, phase, flags, scare counter, darkness, timers, audio flags)
  - [ ] Di chuyß╗ân: `stepPlayer(state, dx, dy, dt)` ΓÇö clamp dt Γëñ 50ms, speed 120 px/s, collision slide (t├ích X/Y), bi├¬n map
  - [ ] Trigger: `checkTriggers(state, player)` ΓÇö zone active theo phase, fire-once, ╞░u ti├¬n knockback tr╞░ß╗¢c chuyß╗ân cß║únh
  - [ ] State machine: `updateGame(state, dt, input)` ΓÇö xß╗¡ l├╜ phase timers (accumulator), transitions, GARDEN chuß╗ùi 4 phase, KITCHEN 2 nh├ính, HAUNTED knockback, HALLWAY 5 scare fire-once + counter, DINING cutscene phases
  - [ ] Light radius: `computeLight(state, x, y)` ΓÇö 90px, chß╗ë HAUNTED/HALLWAY
  - [ ] B╞░ß╗¢m AI: `updateButterfly(state, dt)` ΓÇö pattern sin, tr├ính m├¿o < 60px (85 px/s), bi├¬n map
- [ ] `test/core.test.js` ΓÇö node test (assert thß╗º c├┤ng, exit code):
  - [ ] 4 h╞░ß╗¢ng di chuyß╗ân + bi├¬n map + clamp
  - [ ] Collision vß║¡t cß║ún kh├┤ng xuy├¬n + tr╞░ß╗út dß╗ìc t╞░ß╗¥ng + knockback kh├┤ng xuy├¬n
  - [ ] Chuß╗ùi GARDEN: G_INIT ΓåÆ G_BUTTERFLY (cß╗¡a kh├│a) ΓåÆ G_CHASE ΓåÆ G_DARK (darkness 0ΓåÆ1 trong 5s) ΓåÆ G_DOOR ΓåÆ LIVING
  - [ ] KITCHEN: K_BLOOD ΓåÆ K_VOICE ΓåÆ K_CHOICE; [1] ΓåÆ K_RUN ΓåÆ HAUNTED; [2] ΓåÆ K_OBEY ΓåÆ GAMEOVER; ─æi v├áo v├╣ng tß╗æi = K_OBEY
  - [ ] HAUNTED: cß╗¡a tr╞░ß╗¢c knockback + kh├┤ng chuyß╗ân cß║únh; cß╗¡a h├ánh lang ΓåÆ HALLWAY
  - [ ] HALLWAY: 5 scare fire-once (kh├┤ng fire lß║╖p), sau 5 ΓåÆ W_DONE mß╗ƒ cß╗¡a
  - [ ] DINING: chuß╗ùi cutscene D_APPROACH ΓåÆ D_JUMP ΓåÆ D_HUG ΓåÆ D_CAKE ΓåÆ D_END
  - [ ] resetGame 2 lß║ºn li├¬n tß╗Ñc kh├┤ng lß╗ùi + reset sß║ích mß╗ìi state
  - [ ] Kh├┤ng dt ΓåÆ kh├┤ng transition (timer chß╗ë t─âng khi step)

### P2 ΓÇö Sprites & render (browser)
- [ ] `src/sprites.js` ΓÇö pixel maps 16├ù16 (palette Γëñ 16 m├áu): m├¿o t├│c hß╗ông (idle/walk 2 frame, mirror tr├íi/phß║úi), b╞░ß╗¢m 2 frame, chß╗º (idle/├┤m), hß╗ôn ma 2 frame, b├ính kem 2 frame, cß╗¡a kh├│a/mß╗ƒ, b├án, vß║┐t m├íu, m├óy 2 frame, mß║╖t trß╗¥i, c├óy, hoa, heart 2 frame, m┼⌐i t├¬n, v├╣ng tß╗æi; h├ám `drawSprite(ctx, name, x, y, frame, flip)`
- [ ] Render scenes: TITLE (bß║ºu trß╗¥i xanh + m├óy bay + mß║╖t trß╗¥i), GARDEN (cß╗Å, nh├á, cß╗¡a, c├óy, hoa), LIVING (sofa, thß║úm, TV, cß╗¡a sß╗ò, 2 cß╗¡a), KITCHEN (tß╗º, b├án, chß║¡u rß╗¡a, vß║┐t m├íu, v├╣ng tß╗æi), HAUNTED (LIVING tß╗æi + s╞░╞íng + hß╗ôn ma canh cß╗¡a + m┼⌐i t├¬n), HALLWAY (h├ánh lang d├ái, cß╗¡a 2 ─æß║ºu, scare props), DINING (b├án, chß╗º ngß╗ôi, nß║┐n)
- [ ] Camera follow + clamp; vß║╜ walls/zones debug (tß║»t mß║╖c ─æß╗ïnh)

### P3 ΓÇö Audio (browser)
- [ ] `src/audio.js` ΓÇö WebAudio: meow (2 tone), scare (noise burst + low boom), chime (3 note); init sau gesture ─æß║ºu; mute nß║┐u lß╗ùi; `ctx.resume()` khi gesture

### P4 ΓÇö Game loop & UI (browser)
- [ ] `src/game.js` ΓÇö rAF loop + dt accumulator (clamp 50ms), key state Set (bß╗Å e.repeat, preventDefault WASD/arrows, clear on blur/visibilitychange), d-pad ß║úo (touchstart/touchend, hiß╗çn khi ontouchstart, ß║⌐n hint b├án ph├¡m), camera, vß║╜ scenes + sprites + darkness/light radius, fade 0.5s, inputLocked per phase, ph├¡m 1/2 chß╗ë khi K_CHOICE, n├║t X lu├┤n hoß║ít ─æß╗Öng ΓåÆ resetGame
- [ ] UI overlay (HTML/CSS): khung nhiß╗çm vß╗Ñ (g├│c tr├¬n tr├íi + n├║t X), n├║t bß║¡t/tß║»t UI (g├│c tr├¬n phß║úi), hß╗Öp thoß║íi/bubble, hß╗Öp lß╗▒a chß╗ìn [1]/[2], counter "Bß╗ï h├╣: x/5", Game Over screen, END screen, title START
- [ ] `index.html` + `style.css`: script classic + relative path, canvas 480├ù270 letterbox, image-rendering: pixelated, font monospace

### P5 ΓÇö Deploy & t├ái liß╗çu
- [ ] `.github/workflows/pages.yml` (trigger [master, main] paths games/** + workflow_dispatch, permissions pages, upload path games)
- [ ] `README.md` ngß║»n trong games/yuniebel/ (c├ích ch╞íi, link Pages)
- [ ] `test.md` ΓÇö kß║┐t quß║ú node test + manual checklist 15 b╞░ß╗¢c
- [ ] `evaluation.md` ΓÇö ─æß╗æi chiß║┐u AC1..17
- [ ] Cß║¡p nhß║¡t LOG.md + PROGRESS.md + commit
