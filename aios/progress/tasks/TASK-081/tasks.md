# TASK-081 — Tasks: Scaffold Phaser + Migrate Yuniebel's Cat

> Ngày: 2026-08-15 · Trạng thái: todo → in-progress khi implement · Spec: spec.md (v3)

## Checklist (đánh dấu khi xong)

### P0 — Verify môi trường & Phaser 4 API (P3-11, P3-B5, P3-B6)
- [ ] Tạo `games/yuniebel-phaser/` + `package.json` (`"type": "module"`, deps: phaser@4.2.1, vite, vitest, jsdom, @playwright/test)
- [ ] `npm install` — xác nhận phaser 4.2.1 cài OK
- [ ] Snippet verify API: `textures.createCanvas` + `texture.getContext()` + `texture.refresh()` + `add.image` + `cameras.main.setScroll` + `add.text` — chạy thật trong browser (Playwright console) → ghi kết quả vào implementation/NOTES.md
- [ ] Verify `canvas` config (element có sẵn) + hành vi resize không Scale Manager
- [ ] Chụp thử 1 frame WebGL screenshot — nếu rỗng → `render.preserveDrawingBuffer` / snapshot
- [ ] Verify vitest jsdom: import Phaser có crash ở module-load không (nếu crash → smoke chỉ assert config thuần)

### P1 — Vendor migrate (byte-identical — AC-16)
- [ ] Copy `games/yuniebel/src/core.js` → `src/vendor/core.js` (byte-identical)
- [ ] Copy `games/yuniebel/src/sprites.js` → `src/vendor/sprites.js` (byte-identical)
- [ ] Copy `games/yuniebel/src/audio.js` → `src/vendor/audio.js` (byte-identical)
- [ ] `diff --no-index` ×3 xác nhận sạch (ghi vào test.md)

### P2 — Scaffold project
- [ ] `index.html`: canvas#game 480×270 + overlay DOM (task-box, dialogue, choice-box, scare-counter, dpad, mute, ui-toggle, title/gameover/end screens, hint) — port từ vanilla index.html
- [ ] `style.css`: port từ vanilla (đổi id nếu cần, giữ pixel style + letterbox + overlay)
- [ ] `vite.config.js`: base './', server port 5175 strictPort, build.outDir dist, vitest environment jsdom
- [ ] `playwright.config.js`: webServer build+preview 4174 strictPort, baseURL, timeout 120s, autoplay flag, testMatch e2e|visual
- [ ] `.gitignore` (node_modules, dist, test-results)

### P3 — Scene Phaser
- [ ] `src/main.js`: Phaser.Game config (canvas:#game, 480×270, pixelArt, roundPixels, scene:[GameScene], KHÔNG Scale Manager) + window keydown/keyup port vanilla + oneShot + dpad + debug hook ?test=1 (`window.__yuniebel = {debug, getState, camX, core, audio}`)
- [ ] `src/ui/ui.js`: syncUI port vanilla (title/gameover/end/task/dialogue/choice/scare/mute/ui-toggle) + click handlers
- [ ] `src/scenes/GameScene.js`:
  - create(): 9 bg CanvasTexture (create-once) + image (origin 0,0) + player texture 144×96 + butterfly texture 96×96 + "!" Text + flash/fade rectangles + resize CSS handler; **depth: bg 0 < sprite 10 < "!" 20 < flash/fade 30 (R7)**
  - update(delta): core update delta/1000; re-render bg theo state.scene (drawGarden cx=0 + dark overlay + light pool world-space; drawHallway cx=0; drawLiving/drawKitchen/drawHaunted/drawBirthday; drawTitle/drawGameOver/drawEnd); sync player/butterfly; camera scroll; "!" text 30/42px; flash/fade; handleSoundFlags + mood + footstep + ambient; syncUI
  - Chuyển cảnh: đổi texture image + reset camera

### P4 — Tests
- [ ] `test/core.test.js` (vitest jsdom): migrate 27 assertion vanilla (import side-effect + window.AiosCore) — AC-2; **R3: bỏ `process.exit`/`require` cuối file (vitest ESM sẽ giết worker)**
- [ ] `test/smoke.test.js` (vitest jsdom): 3 vendor load + drawGarden mock ctx + config Phaser hợp lệ (không boot) — AC-3
- [ ] `test/e2e.spec.js` (Playwright): port helper vanilla (gotoGame/moveTo/hold/chaseButterfly — 120ms/40ms) + 2 playthrough no-hook (title→birthday, title→gameover) + camX assert (AC-7) + dialogue (AC-8) + choice (AC-9) + scare (AC-10) + audio mood/SFX (AC-11) + mute/UI-toggle/d-pad (AC-12)
- [ ] `test/visual.spec.js` (Playwright): ≥6 shot chuỗi đầy đủ (goto → START → chờ 500ms → setter → freeze → chờ 100ms → chụp ×2 cách 500ms) → test-results/shots/
- [ ] Copy 6 baseimg → `test/brief/refs/1..6.png` (P3-10)
- [ ] `test/brief/COMPARISON.md`: đối chiếu ảnh chụp vs refs + brief-visuals.md (AC-6/AC-10)

### P5 — Deploy & docs
- [ ] `.github/workflows/pages.yml`: thêm step setup-node (pin Node 20 — R6) + build yuniebel-phaser (npm ci + vite build) + rm -rf node_modules trước upload (AC-14)
- [ ] `README.md`: cách chạy, cấu trúc, URL `/games/yuniebel-phaser/dist/`, ánh xạ baseimg + nguồn refs (AC-15)
- [ ] `implementation/NOTES.md`: kết quả verify API Phaser 4 + quyết định phát sinh

### P6 — Verify tổng (AC)
- [ ] `npx vitest run` — core + smoke PASS (AC-2, AC-3)
- [ ] `npx playwright test` — e2e + visual PASS (AC-4..AC-12)
- [ ] `git diff --quiet HEAD -- games/yuniebel` exit 0 (AC-13) + `diff --no-index` vendor (AC-16)
- [ ] `npm run build` → dist/ base './' (AC-1)
- [ ] DoD checklist: LOG + PROGRESS + PLAN + STATS + task folder + commit

## Ghi chú triển khai (từ spec v3)
- UMD import: `import "../src/vendor/core.js"` (side-effect) → `window.AiosCore` (P3-B2)
- Player texture: drawCat(ctx, 14, 8, dir, fr, time) — position (p.x*3−42, p.y*3) (P1-B1)
- Butterfly texture: drawButterfly(ctx, 16, 16, time) — position (b.x*3, b.y*3) (P1-B2)
- Dark overlay + light pool world-space vào bg (P1-B3)
- "!" font 30px/42px (P2-B2)
- Visual: chờ fade ≥500ms trước freeze (P2-B3)
- d-pad e2e: dispatchEvent touchstart/touchend (P2-B5)
