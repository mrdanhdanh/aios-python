# YUNIEBEL'S CAT — Phaser 4 Edition 🐱

Webgame 2D pixel art **"Yuniebel's Cat"** — bản **Phaser 4 (4.2.1) + Vite** (TASK-081), migrate scene/dialogue từ bản vanilla `games/yuniebel/` (TASK-078).

> **Bản vanilla** (HTML/JS thuần, 0 dependency) vẫn giữ nguyên tại `games/yuniebel/`. Bản này là **bản Phaser**: engine render/camera/input thay bằng Phaser, nhưng **logic game + render primitives + audio = byte-identical** với vanilla (vendor).

## 🎮 Cách chạy

```bash
cd games/yuniebel-phaser
npm install
npm run dev        # http://localhost:5175 (strictPort — tránh dashboard 5173)
npm run build      # ra dist/ (base './' — chạy file:// lẫn GitHub Pages subpath)
npm run preview    # http://localhost:4174
```

## 🚀 Chơi online (GitHub Pages)

```
https://mrdanhdanh.github.io/aios-python/games/yuniebel-phaser/dist/
```

## 🎮 Cách chơi

- **WASD / mũi tên** — di chuyển mèo
- **Space / Enter** — advance hội thoại nhanh / START
- **1 / 2** (hoặc click) — chọn lựa ở cảnh nhà bếp
- **🔊** (góc phải) — bật/tắt âm thanh
- Mobile: d-pad ảo hiện tự động

## 📁 Cấu trúc

```
games/yuniebel-phaser/
├── index.html            # canvas#game 480×270 + overlay DOM (port vanilla)
├── style.css             # pixel style + letterbox (port vanilla)
├── vite.config.js        # base './', port 5175, vitest jsdom
├── playwright.config.js  # webServer build+preview 4174
├── src/
│   ├── main.js           # Phaser.Game boot + input window listeners + debug hook ?test=1
│   ├── vendor/           # BYTE-IDENTICAL với games/yuniebel/src/ (AC-16):
│   │   ├── core.js       #   logic thuần (17 phase, 13 thoại, 9 task, choice, 5 scare)
│   │   ├── sprites.js    #   render primitives (GX=3 — khớp 6 ảnh baseimg)
│   │   ├── audio.js      #   WebAudio synth (10 mood + 22 SFX)
│   │   └── loader.js     #   adapter UMD (file riêng — vendor không sửa)
│   ├── scenes/
│   │   └── GameScene.js  # 1 scene duy nhất: re-render bg texture mỗi frame + sprite động + camera scroll + overlay
│   └── ui/
│       └── ui.js         # DOM overlay sync + camX + moodForPhase + handleSoundFlags (port game.js vanilla)
└── test/
    ├── core.test.js      # vitest — 27 assertion (migrate vanilla)
    ├── smoke.test.js     # vitest jsdom — vendor load + drawGarden mock ctx + config Phaser
    ├── e2e.spec.js       # Playwright — 2 playthrough thật + camX + d-pad + mood/SFX + freeze
    ├── visual.spec.js    # Playwright — 17 shot (freeze determinism) → test-results/shots/
    └── brief/
        ├── refs/1..6.png # copy từ games/yuniebel/baseimg/ (6 ảnh tham khảo scene)
        └── COMPARISON.md # đối chiếu ảnh chụp vs refs + brief-visuals.md
```

## 🖼️ Ánh xạ baseimg (6 ảnh tham khảo)

| File (refs/) | Cảnh | Nguồn gốc |
|--------------|------|-----------|
| 1.png (portrait) | Title screen | ảnh tham khảo người dùng gửi (TASK-078 + TASK-081) |
| 2.png (landscape) | Sân vườn — 3 panel: ngày → hoàng hôn → đêm | như trên |
| 3.png (landscape) | Phòng khách + Nhà bếp (vết máu, mắt sáng) | như trên |
| 4.png (landscape) | Phòng khách ma ám (ma xanh đầu lâu chặn cửa) | như trên |
| 5.png (landscape) | Hành lang — 5 jump scare | như trên |
| 6.png (portrait) | Sinh nhật (lò sưởi, bánh kem) | như trên |

Mô tả chuẩn để đối chiếu: `aios/progress/tasks/TASK-078/implementation/brief-visuals.md`.

## ✅ Test

```bash
npm test                 # vitest (core+smoke) + playwright (e2e+visual)
npx vitest run           # 27 core + 3 smoke
npx playwright test      # e2e 8 test + visual 18 test (webServer tự build+preview)
```

## 🔍 Debug

Thêm `?test=1` vào URL → `window.__yuniebel`:
- `debug` — setPhase/setPlayer/setDarkness/setScareZone/freeze...
- `getState()` — đọc state (e2e chỉ ĐỌC — no-hook quy ước)
- `camX()` — camera scroll hiện tại (AC-7)
- `core`, `audio` — AiosCore + AudioFX instance

## 🔧 Kiến trúc render (tóm tắt)

- **9 CanvasTexture** tạo 1 lần (bg-title/garden/living/kitchen/haunted/hallway/birthday/gameover/end).
- Mỗi frame: vẽ bg theo `state.scene` vào texture (drawGarden cx=0 + dark overlay + light pool đèn hiên world-space) → `refresh()`.
- Sprite động: Player (144×96, anchor 0,0, position `p.x*3−42, p.y*3−24`) + Butterfly (96×96) — ghost/scare nằm TRONG bg (sprites.js tự xử lý).
- Camera: `camX() = clamp(p.x−77, 0, sc.w−160)` → `setScroll(camX*3, 0)` (GARDEN/HALLWAY 320×90 → 960×270).

Tạo bởi AIOS Orchestrator — TASK-081 (plan + spec v3 + critique ×2 + review APPROVED + test + evaluation).
