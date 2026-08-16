# TASK-081 — Spec v3: Scaffold Phaser + Migrate Yuniebel's Cat

> Ngày: 2026-08-15 · Owner: AIOS Orchestrator · Trạng thái: **spec v3** (sau critique-1 + critique-2 — toàn bộ P1/P2/P3 resolved ×2 vòng)
> Lịch sử: v1 (spec-v1.md) → critique-1 → v2 → critique-2 → v3.
> Bổ sung v3 (critique-2): sprite mèo **144×96 offset 14** (P1-B1), **bỏ sprite riêng Ghost/Scare** — chỉ Player+Butterfly động (P1-B2), **dark overlay + light pool world-space** (P1-B3), texture bg **create-once + refresh** mỗi frame (P2-B1), font "!" **30px/42px ×GX** (P2-B2), visual **chờ fade ≥500ms trước freeze** (P2-B3), **KHÔNG Scale Manager** (P2-B4), d-pad e2e **dispatchEvent touch** (P2-B5), `"type":"module"` (P3-B1), import UMD side-effect (P3-B2), e2e helper vanilla (P3-B3), AC-6 nguồn brief-visuals (P3-B4), smoke Phaser try/catch (P3-B5), screenshot WebGL rủi ro (P3-B6), update delta/1000 (P3-B7).

## 1. Mục tiêu

Tạo **bản Phaser** của webgame "Yuniebel's Cat" tại `games/yuniebel-phaser/`:
- **Scaffold Phaser 4.2.1** (Vite bundler, npm package riêng) — thay engine render vanilla canvas bằng Phaser (Game/Scene/camera/input), nhưng:
  - **Tái sử dụng 100% logic game** (`core.js` — framework-agnostic UMD) → 17 phase, 13 câu thoại, 9 task text, choice 1/2, 5 scare, bướm AI, knockback... KHÔNG đổi hành vi.
  - **Tái sử dụng 100% render primitives** (`sprites.js` — đã khớp 6 ảnh baseimg qua TASK-078).
  - **Tái sử dụng audio** (`audio.js` — WebAudio synth) nguyên văn.
- **Migrate scene + dialogue** hiện tại: 1 GameScene Phaser quản lý theo `state.scene` (state machine core giữ nguyên), dialogue/UI giữ DOM overlay như vanilla.
- **Tham khảo baseimg**: 6 ảnh `games/yuniebel/baseimg/1..6.png` (title, garden 3-panel, living+kitchen 2-panel, haunted, hallway 5-scare, birthday) — copy vào `test/brief/refs/` để đối chiếu ảnh chụp (COMPARISON.md) như TASK-078.
- **Giữ nguyên** `games/yuniebel/` (vanilla) — không phá 28/28 test.

## 2. Phạm vi

### Trong phạm vi
- `games/yuniebel-phaser/` — project mới: `package.json`, `index.html`, `style.css`, `vite.config.js`, `playwright.config.js`, `src/`, `test/`, `README.md`, `.gitignore`, `test/brief/refs/` (copy 6 baseimg).
- `.github/workflows/pages.yml` — thêm bước build Vite game + **rm node_modules trước upload** (không phá deploy vanilla).
- `aios/progress/tasks/TASK-081/` — 8-file hard gate + implementation/.
- `aios/progress/{LOG,PROGRESS,STATS}.md`, `docs/PLAN.md` — cập nhật theo DoD.

### Ngoài phạm vi
- `games/yuniebel/` (vanilla) — CHỈ ĐỌC, không sửa.
- Backend/dashboard/extension/sdk — không đụng.
- KHÔNG thêm asset PNG ngoài baseimg — mọi visual tiếp tục là canvas primitives từ sprites.js.

## 3. Kiến trúc (spec v2)

```
games/yuniebel-phaser/
├── index.html              # canvas#game (480×270) + overlay DOM (task/dialogue/choice/dpad/mute/ui-toggle/title/gameover/end/hint) + module script /src/main.js
├── style.css               # pixel style + overlay (copy cấu trúc từ vanilla, chỉnh id cho khớp)
├── package.json            # "type": "module" (P3-B1) — phaser@4.2.1, vite, vitest, jsdom, @playwright/test
├── vite.config.js          # base './', server.port 5175 strictPort, build.outDir dist, test.environment jsdom
├── playwright.config.js    # webServer: build && preview --port 4174 --strictPort; baseURL http://localhost:4174; autoplay flag; timeout 120s
├── src/
│   ├── main.js             # Phaser.Game config: canvas:#game, 480×270, pixelArt:true, roundPixels:true, scene:[GameScene]; window listener input; debug hook ?test=1
│   ├── vendor/             # SAO CHÉP BYTE-IDENTICAL từ games/yuniebel/src/ (kiểm chứng bằng diff — AC-16):
│   │   ├── core.js         # logic thuần UMD (AiosCore)
│   │   ├── sprites.js      # render primitives UMD (Sprites, GX=3)
│   │   └── audio.js        # WebAudio synth UMD (AudioFX)
│   ├── scenes/
│   │   └── GameScene.js    # 1 SCENE DUY NHẤT: re-render bg texture mỗi frame theo state; sprite động; camera; overlay; UI sync (port game.js vanilla)
│   └── ui/
│       └── ui.js           # DOM overlay sync (task box, dialogue, choice, scare counter, dpad, mute, title/gameover/end) — port từ game.js vanilla
└── test/
    ├── core.test.js        # vitest (environment jsdom) — 27 assertion migrate từ vanilla core.test.js
    ├── smoke.test.js       # vitest jsdom — 3 vendor load + Sprites.drawGarden vào mock ctx + config Phaser hợp lệ (KHÔNG boot — P2-1)
    ├── e2e.spec.js         # Playwright — 2 test chơi thật no-hook (title→sinh nhật ≤120s, title→game over) + camX (AC-7)
    ├── visual.spec.js      # Playwright — chụp ≥6 ảnh (freeze + 2 lần so khớp) → test-results/shots/ + test/brief/COMPARISON.md
    └── brief/
        ├── refs/1..6.png   # copy baseimg (P3-10)
        └── COMPARISON.md   # đối chiếu 6 ảnh chụp vs refs
```

### Render pipeline (v3 — re-render mỗi frame, create-once + refresh — P1-1/P2-B1)
- **Nền**: Tạo **9 CanvasTexture 1 lần trong `create()`**: `bg-title/bg-garden/bg-living/bg-kitchen/bg-haunted/bg-hallway/bg-birthday/bg-gameover/bg-end`. Kích thước: GARDEN/HALLWAY **960×270** (320 logical), còn lại **480×270** (160 logical).
  - Mỗi frame: `ctx = texture.getContext()` → vẽ theo `state.scene` → `texture.refresh()`:
    - GARDEN: `drawGarden(ctx, state, time, 0)` (cx=0 — vẽ TOÀN BỘ map, translate(0,0), KHÔNG clip nội bộ) → **sau đó vẽ overlay đêm world-space** (P1-B3): dark `rgba(8,10,30,(darkness−0.5)*0.6)` fillRect `(0,0,960,270)` khi darkness>0.5; light pool `rgba(255,217,59,0.12)` fillRect `(287*3−12, 38*3, 24, 30)` = `(849, 114, 24, 30)` khi darkness>0.5.
    - HALLWAY: `drawHallway(ctx, state, time, 0)` (đã chứa 5 scare world 130..300).
    - LIVING/KITCHEN/HAUNTED/BIRTHDAY: `drawLiving/drawKitchen/drawHaunted/drawBirthday(ctx, state, time)` (drawHaunted/drawKitchen đã tự xử lý ghost ẩn/hiện + highlight K_CHOICE theo state).
    - TITLE/GAMEOVER/END: `drawTitle/drawGameOver/drawEnd(ctx, time)`.
  - Cost tương đương vanilla (480×270/frame) — fidelity 100% (owner ở cửa G_INIT, darkness ramp, ghost H_INIT, highlight máu K_CHOICE, mây trôi/nến/sparkle).
- **Sprite động** (P1-B2: **chỉ Player + Butterfly** — ghost/scare NẰM TRONG bg texture, KHÔNG tạo sprite riêng):
  - **Player**: texture **144×96** (48 logical ngang × 32 dọc — P1-B1: drawCat dir<0 vẽ raw tới x+30, hiển thị [x−14,x]; vẽ `drawCat(ctx, 14, 8, dir, fr, time)` → raw max 14+30=44 ≤ 48 ✓, hiển thị dir<0 [0,14] ✓); **anchor (0,0)**, position **`(p.x*3 − 42, p.y*3 − 24)`** (R2: mèo trong texture từ y=7..24 → world [p.y−1, p.y+16] khớp vanilla — nếu chỉ `p.y*3` sẽ lệch +8 logical = 24px, chân mèo clip đáy canvas); **KHÔNG setFlipX** (drawCat tự flip nội bộ, không đối xứng).
  - **Butterfly**: texture **96×96** (32 logical), vẽ `drawButterfly(ctx, 16, 16, time)` (bướm 8×6 quanh tâm, padding 16); image anchor (0.5), position `(b.x*3, b.y*3)` (camera scroll tự dịch — parity vanilla vẽ tại b.x−cx).
  - "!"/"!!"/"!!!"/"!?" trên đầu mèo = **Phaser Text** (P2-7 + P2-B2): position `((p.x − camX + 4)*3, p.y*3 − 4)`, font monospace bold **30px (42px khi scare 5)** — đã ×GX như vanilla `(10|14)*3` (R4), màu trắng, ẩn/hiện theo scareActive; baseline lệch vài px chấp nhận (verify bước 0).
- **Camera**: `camX() = clamp(p.x − 80 + 3, 0, sc.w − 160)` (giữ công thức vanilla) → `this.cameras.main.setScroll(camX*3, 0)` mỗi frame (GARDEN/HALLWAY 320×90; các scene 160×90 → scroll 0).
- **Depth ordering** (R7): bg image (depth 0) < player/butterfly (10) < "!" Text (20) < flash/fade rectangles (30) — khớp thứ tự vẽ vanilla.
- **Overlay**: flash jump scare = rectangle alpha theo state.flash; fade chuyển cảnh = rectangle alpha fadeT 0.35s (P3-2). Dark overlay + light pool đã vẽ vào bg (P1-B3).
- **Chuyển cảnh**: `updateGame` set `state.scene` → mỗi frame GameScene đọc `state.scene` → nếu đổi texture key → đổi image texture + reset camera/player position + syncUI (state machine core lo phần chuyển phase — giữ nguyên).

### Input (v3 — window listener, P3-3)
- Port NGUYÊN VĂN window keydown/keyup từ game.js vanilla: `keys{}`, `e.repeat` guard, `audio.init()` gesture đầu, 1/2 chỉ khi K_CHOICE, Space/Enter start/advance.
- `oneShot` (start/choice1/choice2) reset mỗi update — giữ nguyên.
- Click DOM: btn-start, choice-1/2, replay, mute, ui-toggle, task-close (giữ nguyên vanilla).
- Touch: d-pad DOM (giữ nguyên). E2E d-pad: `page.dispatchEvent('#pad-right', 'touchstart')` → giữ → `'touchend'` (P2-B5).

### GameScene.update (v3 — P3-B7, P2-B4)
- `update(delta)` (Phaser delta **ms**) → `coreUpdate = game.update(delta/1000, input)` — core nhận **giây** (MAX_DT clamp 0.05 nội bộ). Sai đơn vị → mèo chạy nhanh/chậm 1000×.
- Sau update: re-render bg (mỗi frame), sync sprite positions (player/butterfly), camera `setScroll(camX*3, 0)`, overlay flash/fade, `handleSoundFlags()` + `moodForPhase()` + footstep 0.28s + ambient bird/clockTick, `syncUI()`.
- **Scale**: KHÔNG dùng Scale Manager (không khai báo `scale` hoặc `scale: NONE`) — giữ CSS resize vanilla (JS `canvas.style.width/height` theo window).
- **Chuyển cảnh** (state.scene đổi): đổi image texture bg → reset camera scroll + player position (core đã set spawn — chỉ sync).

### Audio (giữ nguyên vanilla)
- `audio.js` byte-identical; `handleSoundFlags()` + `moodForPhase()` port từ game.js sang GameScene/ui — mood theo phase + SFX 1 lần rồi xóa flag; footstep timer 0.28s (grass/echo theo scene); ambient bird (GARDEN) + clockTick (LIVING) định kỳ (P3-2).

## 4. Input / Output

- **Input**: 6 ảnh baseimg (ánh xạ plan.md §Baseimg) + mã nguồn vanilla (core/sprites/audio/game/index/style/test).
- **Output**: project chạy được (dev + build) + test 3 tầng + docs.

## 5. Tiêu chí chấp nhận (v2)

| # | AC | Kiểm chứng |
|---|-----|------------|
| AC-1 | `npm install && npm run dev` chạy được; `npm run build` ra `dist/` (base './') | chạy thật, xem log + dist/index.html relative path |
| AC-2 | Logic core migrate byte-identical: **27 assertion** core.test.js PASS (vitest jsdom) — 17 phase, 13 thoại, 9 task, choice, 5 scare, bướm, knockback, collision | `npx vitest run test/core.test.js` |
| AC-3 | Smoke: 3 vendor load trong vitest jsdom không throw + `Sprites.drawGarden` vào mock 2D ctx không throw + config Phaser hợp lệ (KHÔNG boot — P2-1) | `npx vitest run test/smoke.test.js` |
| AC-4 | Playwright e2e chơi thật **no-hook** (chỉ ĐỌC state qua ?test=1, không gọi setter — P3-9): title→sinh nhật PASS ≤120s (tương đương vanilla 40–90s — P3-5) | `npx playwright test e2e` (webServer build+preview 4174) |
| AC-5 | Playwright e2e: title→game over (choice 2) PASS | như trên |
| AC-6 | Visual: chụp 7 ảnh chính (title, garden-day, living, kitchen-blood, haunted, hallway-scare1, birthday) + 5 ảnh phụ hallway-scare2..5 (tổng 12 — R5). **Chuỗi mỗi shot** (P2-B3): goto → click START → **chờ ≥500ms (fade 0.35s hết)** → setter → `freeze(true)` → chờ ≥100ms → chụp lần 1 → chờ 500ms → chụp lần 2 so khớp → test-results/shots/ + COMPARISON.md đối chiếu refs/1..6.png theo nguồn chuẩn `TASK-078/implementation/brief-visuals.md` (P3-B4 — đối chiếu cấu trúc chính: trời/nhà/nội thất/vị trí mèo) | xem ảnh + COMPARISON.md |
| AC-7 | Camera scroll Phaser hoạt động: **expose `camX()` qua window.__yuniebel** (P1-2) → e2e assert camX = 0 khi player.x ≤ 77, tăng khi player.x > 77 (P3-6); GARDEN + HALLWAY | e2e assert camX |
| AC-8 | Dialogue UI DOM: 13 câu hiển thị đúng + thought style + advance Space/Enter + tự advance | e2e assert |
| AC-9 | Choice 1/2 hoạt động: 1→HAUNTED, 2→GAME_OVER + UI nút | e2e |
| AC-10 | 5 scare zone → scareCount=5 (e2e assert) + 5 shot `hallway-scare1..5` (freeze theo từng scareActive) đối chiếu 5 `drawScare*` khác nhau (COMPARISON.md) + "!""/"!!"/"!!!"/"!?" (Phaser Text 30/42px) trên đầu mèo + scare counter 5/5 | e2e + visual |
| AC-11 | Audio: mood theo phase (getMood) + SFX cụ thể đếm tăng (getStats — vd footstepGrass/ting) sau sự kiện thật | e2e assert (autoplay flag — P3-8) |
| AC-12 | Mute + UI toggle hoạt động (e2e click) + d-pad hoạt động (dispatchEvent touchstart/touchend → player.x tăng — P2-B5) | e2e |
| AC-13 | Vanilla `games/yuniebel/` không bị sửa: `git diff --quiet HEAD -- games/yuniebel` (chỉ tracked — P2-4) | exit 0 |
| AC-14 | pages.yml: step build `games/yuniebel-phaser` (npm ci + vite build) + **rm -rf node_modules** TRƯỚC upload artifact (P2-5); deploy vanilla không đổi | đọc workflow + review |
| AC-15 | README.md game mới: cách chạy, cấu trúc, URL GitHub Pages (`/games/yuniebel-phaser/dist/`), ánh xạ baseimg + nguồn gốc refs | đọc file |
| AC-16 | **Vendor byte-identical** (P2-4): `diff --no-index games/yuniebel/src/{core,sprites,audio}.js vendor/...` = sạch (adapter chỉ ở file riêng, KHÔNG sửa vendor) | diff exit 0 |

## 6. Ràng buộc & quy tắc

1. **Vendor bất biến**: `src/vendor/core.js`, `sprites.js`, `audio.js` = **byte-identical** với vanilla (AC-16). Mọi adapter (nếu cần UMD/import) nằm ở file riêng `src/vendor/loader.js` hoặc cấu hình vitest — không sửa vendor.
2. **Không đổi hành vi game**: state machine, thoại, task, zone, tốc độ, knockback, scare giữ nguyên → bất kỳ thay đổi hành vi nào đều là bug.
3. **Phaser 4.2.1**: chỉ dùng API cốt lõi (Game/Scene/cameras.setScroll/textures.createCanvas+refresh/add.image/add.text/rectangle). `pixelArt: true, roundPixels: true`. Verify API thật trước khi viết scene (bước 0 — P3-11).
4. **Tọa độ**: logical grid 160×90 (GARDEN/HALLWAY 320×90); Phaser pixel 480×270 = logical ×3 (GX=3); scene rộng 320 → texture 960×270. Sprite động: **Player texture 144×96, anchor (0,0), vẽ drawCat(ctx,14,8,...), position (p.x*3−42, p.y*3−24)** (R2: bù offset dọc 8 logical — mèo world [p.y−1, p.y+16] khớp vanilla, không clip chân); Butterfly texture 96×96 anchor (0.5) vẽ drawButterfly(ctx,16,16,...) (P1-B1/P1-B2); KHÔNG setFlipX.
5. **`?test=1` debug hook** giữ nguyên: `window.__yuniebel = { debug, getState, camX, core, audio }` — visual dùng debug setter + freeze; e2e chỉ ĐỌC (P3-9).
6. **Deploy URL**: `https://mrdanhdanh.github.io/aios-python/games/yuniebel-phaser/dist/` (base './' — chạy file:// lẫn subpath).
7. Test cuối phải chạy THẬT (không chỉ viết file).
8. DoD checklist bắt buộc (AGENTS.md §3.1): LOG/PROGRESS/PLAN/STATS/task folder/commit.

## 7. Rủi ro & giảm thiểu (v2)

| Rủi ro | Giảm thiểu |
|--------|------------|
| Phaser 4 API khác Phaser 3 (textures/camera/add) | Bước 0 verify API bằng snippet thật; chỉ dùng API cốt lõi; e2e phủ |
| Re-render bg mỗi frame tốn CPU | Vanilla đã vẽ 480×270/frame chạy mượt; Phaser refresh texture 960×270 cost tương đương; target 60fps, chấp nhận |
| jsdom không có WebGL → Phaser boot crash | AC-3 KHÔNG boot Phaser trong jsdom (P2-1) — boot thật qua Playwright |
| vitest Node ESM + UMD vendor | environment jsdom (có self) → UMD gán window đúng (P2-2) |
| Playwright file:// không chạy module script | webServer vite build+preview port 4174 strictPort (P2-8); baseURL http |
| CI artifact phình node_modules | rm -rf node_modules trước upload (P2-5) |
| Pixel probe WebGL không dùng getImageData | AC-7 qua camX() expose + screenshot() compositor (P1-2) |
| Đuôi mèo bị cắt khi flip | Texture 144×96 offset 14 logical, anchor (0,0), không setFlipX (P1-B1) |
| Screenshot WebGL ra ảnh rỗng | Bước 0 chụp thử 1 frame sớm; nếu rỗng → `render: { preserveDrawingBuffer: true }` hoặc `game.renderer.snapshot()` (P3-B6) |
| Smoke import Phaser crash jsdom | Bước 0 verify; nếu crash → smoke chỉ assert config thuần + dynamic import try/catch (P3-B5) |
| Dev port xung đột dashboard 5173 | vite server port 5175 strictPort (P3-12) |

## 8. Deliverables

- `games/yuniebel-phaser/` đầy đủ (mã + test + README + config + test/brief/refs/6 ảnh).
- `pages.yml` cập nhật (build game mới + rm node_modules).
- 8-file hard gate TASK-081 (plan/spec/critique×2/tasks/review/test/evaluation + implementation/).
- LOG/PROGRESS/PLAN/STATS cập nhật + commit.
