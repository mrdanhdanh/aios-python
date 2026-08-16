# TASK-081 — Spec: Scaffold Phaser + Migrate Yuniebel's Cat

> Ngày: 2026-08-15 · Owner: AIOS Orchestrator · Trạng thái: draft (chờ critique ×2 + review)

## 1. Mục tiêu

Tạo **bản Phaser** của webgame "Yuniebel's Cat" tại `games/yuniebel-phaser/`:
- **Scaffold Phaser 4.2.1** (Vite bundler, npm package riêng) — thay engine render vanilla canvas bằng Phaser Scene/camera/input, nhưng:
  - **Tái sử dụng 100% logic game** (`core.js` — framework-agnostic UMD) → 17 phase, 13 câu thoại, 9 task text, choice 1/2, 5 scare, bướm AI, knockback... KHÔNG đổi hành vi.
  - **Tái sử dụng 100% render primitives** (`sprites.js` — đã khớp 6 ảnh baseimg qua TASK-078) → pre-render nền scene thành `CanvasTexture` + sprite động vẽ texture mỗi frame.
  - **Tái sử dụng audio** (`audio.js` — WebAudio synth) nguyên văn.
- **Migrate scene + dialogue** hiện tại: mỗi scene game thành Phaser Scene (hoặc 1 GameScene quản lý theo state.scene), dialogue/UI giữ DOM overlay như vanilla.
- **Tham khảo baseimg**: 6 ảnh `games/yuniebel/baseimg/1..6.png` (title, garden 3-panel, living+kitchen 2-panel, haunted, hallway 5-scare, birthday) — visual test chụp ảnh đối chiếu (COMPARISON.md) như TASK-078.
- **Giữ nguyên** `games/yuniebel/` (vanilla) — không phá 28/28 test.

## 2. Phạm vi

### Trong phạm vi
- `games/yuniebel-phaser/` — project mới: `package.json`, `index.html`, `vite.config.js`, `src/`, `test/`, `README.md`, `.gitignore`, `baseimg-refs.md` (ánh xạ 6 ảnh baseimg → cảnh).
- `.github/workflows/pages.yml` — thêm bước build Vite game (không phá deploy vanilla).
- `aios/progress/tasks/TASK-081/` — 8-file hard gate + implementation/.
- `aios/progress/{LOG,PROGRESS,STATS}.md`, `docs/PLAN.md` — cập nhật theo DoD.

### Ngoài phạm vi
- `games/yuniebel/` (vanilla) — CHỈ ĐỌC, không sửa.
- Backend/dashboard/extension/sdk — không đụng.
- KHÔNG thêm asset PNG ngoài baseimg — mọi visual tiếp tục là canvas primitives từ sprites.js.

## 3. Kiến trúc đề xuất

```
games/yuniebel-phaser/
├── index.html              # #game-root + overlay DOM (task/dialogue/choice/dpad/mute/UI-toggle) + module script
├── style.css               # pixel style + overlay (copy cấu trúc từ vanilla, chỉnh id)
├── package.json            # phaser@4.2.1, vite, vitest, @playwright/test
├── vite.config.js          # base './' (GitHub Pages subpath), build.outDir dist, test (vitest) config
├── playwright.config.js    # webServer: vite preview (port cố định), testMatch e2e|visual
├── src/
│   ├── main.js             # Phaser.Game config: 480×270, pixelArt:true, roundPixels:true, scene list
│   ├── vendor/             # SAO CHÉP NGUYÊN VĂN từ games/yuniebel/src/ (KHÔNG sửa logic):
│   │   ├── core.js         # logic thuần UMD
│   │   ├── sprites.js      # render primitives UMD (Sprites global)
│   │   └── audio.js        # WebAudio synth UMD (AudioFX global)
│   ├── scenes/
│   │   ├── BootScene.js    # pre-render CanvasTexture cho 9 loại bg (title/garden/living/kitchen/haunted/hallway/birthday/gameover/end) + sprite textures; vào TitleScene
│   │   ├── TitleScene.js   # hiển thị bg title + nút START (Phaser text/image + DOM click), chờ start
│   │   ├── GameScene.js    # 1 scene duy nhất cho gameplay: sync state core ↔ Phaser (position/camera/zones/dialogue UI); xử lý chuyển cảnh
│   │   └── EndScene.js     # GAME OVER / END (tái dùng bg textures + nút replay DOM)
│   ├── ui/
│   │   └── ui.js           # DOM overlay sync (task box, dialogue, choice, scare counter, dpad, mute) — port từ game.js vanilla
│   └── config.js           # hằng số: CW/CH, GX, scene→texture map, input key map
└── test/
    ├── core.test.js        # vitest — migrate 27 assertions từ vanilla (import src/vendor/core.js)
    ├── smoke.test.js       # vitest — jsdom: game load, Phaser boot không crash (mock canvas/WebGL)
    ├── e2e.spec.js         # Playwright — 2 test chơi thật (title→sinh nhật, title→game over) qua vite preview
    ├── visual.spec.js      # Playwright — chụp ảnh 6+ cảnh đối chiếu baseimg (COMPARISON.md)
    └── brief/COMPARISON.md # đối chiếu ảnh chụp vs baseimg (6 ảnh)
```

### Render pipeline (quan trọng nhất)
- **Nền tĩnh**: `BootScene.create()` — với mỗi scene (GARDEN 320×90, HALLWAY 320×90, còn lại 160×90, TITLE/END 160×90):
  - Tạo `CanvasTexture` kích thước `sc.w*3 × sc.h*3` (GARDEN/HALLWAY = 960×270; khác = 480×270).
  - Lấy `ctx = texture.getContext()` → gọi hàm sprites.js tương ứng (`drawGarden(ctx, state, time, cx=0)` — vẽ TOÀN BỘ map 1 lần, không camera translate) → `texture.refresh()`.
  - Lưu map `textureKey → {img: Phaser.Image, sc: SCENES[key]}`.
- **Sprite động** (vẽ lại mỗi frame vào canvas nhỏ 48×48/logical×3):
  - Player: `drawCat` → `catTexture.refresh()` mỗi frame; image position `(p.x*3, p.y*3)` (logical→pixel), flip theo dir (Phaser `setFlipX`).
  - Butterfly, ghost skull (HAUNTED), scare 1..5 (HALLWAY): vẽ vào texture động riêng, hiện/ẩn theo state.
- **Camera**: GARDEN/HALLWAY rộng 320 logical → `camX() = clamp(p.x - 80 + 3, 0, 160)` (giữ nguyên công thức vanilla) → `this.cameras.main.setScroll(camX*3, 0)` (hoặc startFollow + bounds). Các scene 160×90: scroll 0.
- **Darkness/flash**: overlay rectangle Phaser (hoặc tái vẽ bg khi darkness đổi — sprites.js drawGarden đã nhận darkness nên nền NIGHT được pre-render đúng; dark overlay + đèn hiên dùng image alpha).
- **Chuyển cảnh**: `updateGame` set `state.scene` → GameScene đọc scene mới → set active texture image, đặt player, reset camera, sync UI.

### Input map (Phaser keyboard)
- WASD/arrows → move (giữ `keys` map như vanilla, sync qua `input` object mỗi update).
- Space/Enter → start/advance dialogue.
- 1/2 → choice (chỉ khi phase K_CHOICE).
- Click DOM: btn-start, choice-1/2, replay, mute, ui-toggle, task-close.
- Touch: d-pad DOM (như vanilla).

### Audio
- `audio.js` nguyên văn (AudioFX global, mood + SFX).
- `handleSoundFlags()` + `moodForPhase()` port từ game.js vanilla sang ui.js/scene (gọi `audio.init()` sau gesture đầu).

## 4. Input / Output

- **Input**: 6 ảnh baseimg (đã ánh xạ ở plan.md §Baseimg) + mã nguồn vanilla (core/sprites/audio/game/index/style/test).
- **Output**: project chạy được (dev + build) + test 3 tầng + docs.

## 5. Tiêu chí chấp nhận (Acceptance Criteria)

| # | AC | Kiểm chứng |
|---|-----|------------|
| AC-1 | `npm install && npm run dev` chạy được; `npm run build` ra `dist/` (base './') | chạy thật, xem log + dist/index.html relative path |
| AC-2 | Logic core migrate nguyên văn: 27 assertions core.test.js PASS (vitest) — 17 phase, 13 thoại, 9 task, choice, 5 scare, bướm, knockback, collision | `npx vitest run test/core.test.js` |
| AC-3 | Smoke: jsdom load game bundle (core+sprites+audio) + Phaser boot không crash (mock canvas/WebGL) | `npx vitest run test/smoke.test.js` |
| AC-4 | Playwright e2e chơi thật không hook: title→sinh nhật (45s tương đương vanilla) PASS qua `vite preview` | `npx playwright test e2e` |
| AC-5 | Playwright e2e: title→game over (choice 2) PASS | như trên |
| AC-6 | Visual: chụp ≥6 ảnh (title, garden-day, living, kitchen-blood, haunted, hallway-scare, birthday) vào test-results/shots/ + COMPARISON.md đối chiếu baseimg (6/6 khớp theo mô tả chuẩn) | xem ảnh + COMPARISON.md |
| AC-7 | Camera scroll Phaser GARDEN (320×90) + HALLWAY (320×90) hoạt động — pixel probe: khi player x>160, cảnh trượt | e2e/pixel test |
| AC-8 | Dialogue UI DOM: 13 câu hiển thị đúng + thought style + advance Space/Enter + tự advance | e2e assert |
| AC-9 | Choice 1/2 hoạt động: 1→HAUNTED, 2→GAME_OVER + UI nút | e2e |
| AC-10 | 5 scare zone → 5 sprite khác nhau + "!"/"!!"/"!!!"/"!?" trên đầu mèo + scare counter 5/5 | e2e + visual |
| AC-11 | Audio: mood theo phase + SFX phát (ít nhất 1 mood chuyển đổi được quan sát qua API/console) | smoke/e2e assert audio.getMood() |
| AC-12 | Mute + UI toggle + d-pad hoạt động | e2e |
| AC-13 | Vanilla `games/yuniebel/` KHÔNG bị sửa (git diff sạch ở thư mục đó) | `git status -- games/yuniebel` |
| AC-14 | pages.yml: thêm job/step build `games/yuniebel-phaser` (npm ci + vite build) trước upload artifact; deploy vanilla không đổi | đọc workflow + dry chạy |
| AC-15 | README.md game mới: cách chạy, cấu trúc, URL GitHub Pages (`/games/yuniebel-phaser/dist/`), ánh xạ baseimg | đọc file |

## 6. Ràng buộc & quy tắc

1. **Vendor bất biến**: `src/vendor/core.js`, `sprites.js`, `audio.js` sao chép NGUYÊN VĂN từ vanilla — không sửa logic (chỉ cho phép thêm export/UMD adapter ở wrapper nếu cần, ghi rõ diff).
2. **Không đổi hành vi game**: state machine, thoại, task, zone, tốc độ di chuyển giữ nguyên → bất kỳ thay đổi nào về hành vi đều là bug.
3. **Phaser 4.2.1**: chỉ dùng API cốt lõi (Game/Scene/cameras/textures.addCanvas/keyboard/tweens), `pixelArt: true, roundPixels: true`. Không phụ thuộc filter WebGL nâng cao.
4. **480×270 logical ×3**: mọi tọa độ Phaser = logical × 3 (GX). Player image origin tùy sprite (drawCat vẽ 16×16 logical → anchor 0.5).
5. **`?test=1` debug hook** giữ nguyên (window.__yuniebel.debug) — phục vụ visual test setPhase/setPlayer.
6. **Deploy URL**: `https://mrdanhdanh.github.io/aios-python/games/yuniebel-phaser/dist/` (base './' — chạy file:// lẫn subpath).
7. Test cuối phải chạy THẬT (không chỉ viết file).
8. DoD checklist bắt buộc (AGENTS.md §3.1): LOG/PROGRESS/PLAN/STATS/task folder/commit.

## 7. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|--------|------------|
| Phaser 4 API khác Phaser 3 (add.image, textures, camera) | Chỉ dùng API ổn định; verify bằng chạy thật + e2e; tham khảo skill pixel-game-dev + docs phaser |
| CanvasTexture refresh mỗi frame (player) tốn CPU | Texture nhỏ (48×48), 1-2 texture động; game chỉ 60fps mục tiêu; acceptable |
| pre-render bg 1 lần thiếu anim (mây trôi, nến cháy, giọt máu, lửa lò sưởi) | Những anim này là detail phụ — chấp nhận nền tĩnh (giữ fidelity tổng thể); hoặc overlay tween nhẹ (mây) |
| jsdom không có WebGL → Phaser boot crash | Smoke test mock `HTMLCanvasElement.getContext` → trả Proxy no-op + `WebGLRenderingContext` giả; nếu quá phức tạp, smoke chỉ test vendor load + config hợp lệ, Phaser boot thật qua Playwright |
| Playwright cần webServer | playwright.config `webServer: { command: 'npm run preview -- --port 4173', url: 'http://localhost:4173' }` |
| base './' với vite preview | preview dùng base tương tự; e2e dùng URL tuyệt đối root (file:// không dùng được với module script → PHẢI qua http server) |

## 8. Deliverables

- `games/yuniebel-phaser/` đầy đủ (mã + test + README + config).
- `pages.yml` cập nhật (build game mới).
- 8-file hard gate TASK-081 (plan/spec/critique×2/tasks/review/test/evaluation + implementation/).
- LOG/PROGRESS/PLAN/STATS cập nhật + commit.
