# YUNIEBEL'S CAT — Cuộc phiêu lưu của mèo con 🐱

Webgame 2D pixel art **100% static** (HTML/CSS/JS thuần — 0 dependency, không build, không CDN). Chạy offline bằng cách mở `index.html` trực tiếp, hoặc online qua GitHub Pages.

> Làm lại hoàn toàn theo kịch bản chi tiết + 5 ảnh tham khảo — TASK-078 (thay thế bản TASK-077).

## 🎮 Cách chơi

- **WASD / mũi tên** — di chuyển mèo
- **Space / Enter** — advance hội thoại nhanh
- **1 / 2** (hoặc click) — chọn lựa ở cảnh nhà bếp
- **🔊** (góc phải) — bật/tắt âm thanh
- Mobile: d-pad ảo hiện tự động

## 📖 Câu chuyện

Hôm nay là sinh nhật Yuniebel — nhưng chủ nhân biến mất... 7 màn chơi: sân vườn đuổi bướm (ngày → hoàng hôn → đêm) → phòng khách → nhà bếp bí ẩn (lựa chọn 1/2) → phòng khách ma ám (ma xanh đầu lâu chặn cửa) → hành lang 5 jump scare → và cuối cùng là một bất ngờ ngọt ngào. 🎂

## 🚀 Chơi online (GitHub Pages)

```
https://mrdanhdanh.github.io/aios-python/games/yuniebel/
```

## 📁 Cấu trúc

```
games/yuniebel/
├── index.html      # Canvas + UI overlay (script classic, relative path)
├── style.css       # Pixel style + letterbox + overlay
├── src/
│   ├── core.js     # Logic thuần (UMD — test được bằng Node)
│   ├── sprites.js  # 7 cảnh + sprite vẽ canvas primitives theo 5 ảnh ref
│   ├── audio.js    # WebAudio: 10 mood nhạc nền + 27 SFX (audio clock)
│   └── game.js     # Game loop + render + input + debug hook (?test=1)
└── test/
    ├── core.test.js    # logic thuần (27 assertions)
    ├── smoke.test.js   # jsdom load (4 assertions)
    ├── e2e.spec.js     # Playwright — chơi thật không hook + audio assert
    ├── visual.spec.js  # Playwright — chụp 17 ảnh đối chiếu brief
    └── brief/          # README + COMPARISON.md (đối chiếu 17/17 khớp)
```

## ✅ Test

```bash
npm test                 # core + smoke + playwright (54/54 PASS)
node test/core.test.js   # logic thuần (27)
node test/smoke.test.js  # smoke jsdom (4)
npx playwright test      # e2e + visual — chụp 17 ảnh ra test-results/shots/
```

Test gồm **chụp ảnh màn hình 17 cảnh** đối chiếu với brief (COMPARISON.md) + **2 test chơi thật không hook** (title→sinh nhật, title→game over).

## 🔍 Debug

Thêm `?test=1` vào URL → `window.__yuniebel.debug` (setPhase/setPlayer/setDarkness/setScareZone/freeze...) — chỉ dùng cho test/chụp ảnh.

Tạo bởi AIOS Orchestrator — TASK-078 (spec + critique ×2 + review + post-review + test + evaluation đầy đủ).
