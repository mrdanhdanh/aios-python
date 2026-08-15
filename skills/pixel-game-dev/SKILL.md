---
name: pixel-game-dev
description: "Meta-skill cô đọng kiến thức làm web game / pixel game: Phaser 4, KAPLAY, PixiJS, công cụ vẽ pixel (Piskel, Pixelorama, Aseprite/LibreSprite, spritefusion-pixel-snapper), palette (LOSPEC, mulfok32). Dùng để agent tư vấn chọn engine, áp dụng filter pixel-art, và sinh asset. Ánh xạ sẵn vào dự án Yuniebel's Cat."
---

# Pixel Game Dev (Web) — Tự học cô đọng

Tài liệu tham khảo cho agent khi phát triển web game / pixel game. Cô đọng từ
khảo sát Phaser 4, KAPLAY, PixiJS, agent-sprite-forge, Piskel/Pixelorama, LOSPEC.

## 1. Chọn engine (nhanh)

| Engine | Khi nào dùng | Ngôn ngữ | Điểm pixel-art |
|--------|--------------|----------|----------------|
| **Phaser 4** | Game 2D đầy đủ (scene, physics, tilemap, tween, particles, camera) | JS/TS | Filter `Blocky`/`Pixelate`/`GradientMap`/`Quantize` (xem references/phaser-pixel-filters.md) |
| **KAPLAY** | Game nhỏ, học nhanh, component-based, có web editor | JS/TS | Dùng palette `mulfok32`, style 16-bit |
| **PixiJS** | Chỉ cần renderer WebGL/WebGPU cực nhanh (không phải engine) | TS | Dùng cùng sprite atlas ngoài |
| **Vanilla Canvas** | Game siêu nhẹ, 0 dependency (như Yuniebel's Cat hiện tại) | JS | Tự vẽ primitives / sprite sheet |

> Chi tiết: `references/engine-comparison.md`

## 2. Pixel-art filters (Phaser 4 — quan trọng nhất cho Yuniebel)

Phaser 4 có filter GPU (WebGL only). Game objects cần `enableFilters()` trước;
camera có sẵn.

- `Blocky` — pixelation GIỮ nguyên màu (không blend). Dùng cho look pixel chuẩn.
- `Pixelate` — mosaic (có blend màu). `amount` càng lớn càng thô.
- `GradientMap` — recolor theo brightness qua ColorRamp → **đổi bảng màu (palette-swap)**.
- `Quantize` — giảm số màu (RGBA/HSVA, dithering) → retro palette.
- `ColorMatrix` presets: `sepia()`, `grayscale()`, `night()`, `lsd()`...

Ví dụ thêm glow + blocky:
```js
const s = this.add.sprite(400, 300, 'cat');
s.enableFilters();                       // game object cần bật
s.filters.internal.addBlocky({ amount: 4 });
s.filters.internal.addGlow(0xff66cc, 4);
```
Camera filter (có sẵn, không cần enable):
```js
this.cameras.main.filters.internal.addColorMatrix().colorMatrix.night(0.4);
```

## 3. Sinh asset (dùng skill agent-sprite-forge)
- Sprite/animation → `$generate2dsprite` (nhân vật, quái, spell, FX).
- Map playable → `$generate2dmap` (lớp, prop-pack, collision/zones).
- Script `scripts/generate2dsprite.py` (Pillow) hậu-xử lý: chroma-key #FF00FF,
  cắt frame, export PNG trong suốt + GIF + meta.

## 4. Công cụ vẽ pixel
- **Piskel** (web-based) — vẽ sprite/tilemap ngay trình duyệt, export sheet + GIF.
- **Pixelorama** — multitool mạnh, web + desktop, hỗ trợ animation/layer.
- **Aseprite / LibreSprite** — chuẩn ngành (Aseprite trả phí build; LibreSprite GPL fork).
- **spritefusion-pixel-snapper** — sửa pixel art sinh bởi AI thành lưới chuẩn.

## 5. Palette
- **LOSPEC** (lospec.com/palettes) — kho palette chuẩn (Sweetie16, Endesga, mulfok32...).
- Tích hợp vào Phaser `GradientMap` để đổi bảng màu theo style game.

## 6. Ánh xạ sang Yuniebel's Cat
- Game hiện tại: vanilla Canvas (index.html + style.css + src/), 0 dependency, test Playwright.
- Nếu muốn nâng cấp: Phaser 4 là lựa chọn tốt nhất (scene/dialogue/choice dễ quản lý,
  filter pixel-art sẵn). Giữ nguyên asset, bọc vào Scene.
- Nếu giữ vanilla: dùng **Piskel** vẽ thêm sprite, **agent-sprite-forge** sinh FX/map mới,
  áp dụng `Blocky`/`GradientMap` nếu chuyển sang Phaser sau.
- Mèo/Cthulhu/ma: sinh bằng `$generate2dsprite` (art_style=retro_pixel), 4-hướng walk → 4x4.

## Tham khảo
- `references/phaser-pixel-filters.md`, `references/engine-comparison.md`
- Upstream: phaserjs/phaser (skills/), kaplayjs/kaplay, pixijs/pixijs, 0x0funky/agent-sprite-forge
