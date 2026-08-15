# YUNIEBEL — Cuộc phiêu lưu của mèo con 🐱🎂

Webgame 2D pixel art **100% static** (HTML/CSS/JS thuần — 0 dependency, không build, không CDN). Chạy offline bằng cách mở `index.html` trực tiếp, hoặc online qua GitHub Pages.

## 🎮 Cách chơi

- **WASD** — di chuyển mèo (mũi tên cũng được)
- **1 / 2** — chọn lựa khi xuất hiện hộp chọn
- **Nút UI (góc trên phải)** — bật/tắt khung nhiệm vụ
- **✕ (góc trên trái)** — về màn hình chính
- Mobile: d-pad ảo hiện tự động

## 📖 Câu chuyện

Hôm nay là sinh nhật Yuniebel — nhưng chủ nhân biến mất... Đi qua 6 cảnh: sân vườn đuổi bướm → nhà bếp bí ẩn → phòng khách ma ám → hành lang dài → và cuối cùng là một bất ngờ ngọt ngào. 🎂

## 🚀 Chơi online (GitHub Pages)

Sau khi workflow `pages.yml` deploy (cần bật **Settings → Pages → Source: GitHub Actions**):

```
https://mrdanhdanh.github.io/aios-python/games/yuniebel/
```

## 📁 Cấu trúc

```
games/yuniebel/
├── index.html      # Canvas + UI overlay (script classic, relative path)
├── style.css       # Pixel style + letterbox
├── src/
│   ├── core.js     # Logic thuần (test được bằng Node — UMD)
│   ├── sprites.js  # Pixel art vẽ bằng ma trận ký tự
│   ├── audio.js    # WebAudio SFX tự sinh (meow/scare/chime)
│   └── game.js     # Game loop + render + input
└── test/
    └── core.test.js  # node test/core.test.js
```

## ✅ Test

```bash
node test/core.test.js        # logic thuần (58 assertions)
node test/smoke.test.js       # smoke test jsdom (cần node_modules của dashboard)
```

Tạo bởi AIOS Orchestrator — TASK-077 (spec + critique ×2 + review + test đầy đủ).
