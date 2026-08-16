# Engine Comparison — Web / Pixel Game (cô đọng)

## Phaser 4 (phaserjs/phaser, ⭐40k, MIT)
- HTML5 game framework, WebGL + Canvas. JS/TS.
- Scene-based, physics Arcade/Matter, tilemaps, tweens, particles, cameras, input.
- **AI Agent Skills** chính thức trong `skills/` (scenes, physics, tilemaps, filters...).
- Pixel-art filters: Blocky, Pixelate, GradientMap, Quantize (xem phaser-pixel-filters.md).
- Scaffold: `npx @phaserjs/create-game@latest`.
- Phù hợp: game 2D đầy đủ, cần quản lý scene/dialogue/choice (như Yuniebel's Cat).

## KAPLAY (kaplayjs/kaplay, ⭐1.8k, MIT)
- Fun-first 2D game lib, JS/TS, component-based: `add([sprite(), pos(), body(), ...])`.
- Có KAPLAYGROUND web editor, 90+ ví dụ, palette `mulfok32`.
- Scaffold: `npx create-kaplay my-game`.
- Phù hợp: game nhỏ, prototype nhanh, người mới.

## PixiJS (pixijs/pixijs, ⭐48k, MIT)
- Renderer WebGL/WebGPU NHANH NHẤT, KHÔNG phải engine (thiếu physics/scene).
- Scaffold: `npm create pixi.js@latest`.
- Phù hợp: cần hiệu năng vẽ cao, kết hợp với engine/physics riêng.

## Vanilla Canvas (như Yuniebel's Cat hiện tại)
- 0 dependency, chạy GitHub Pages trực tiếp.
- Tự quản lý loop/render/input/state machine (core.js).
- Phù hợp: game nhẹ, control tối đa, deploy tĩnh.

## Công cụ asset
| Tool | Loại | Dùng cho |
|------|------|----------|
| Piskel | Web editor | Vẽ sprite/tilemap, export sheet+GIF |
| Pixelorama | Desktop+Web | Multitool pixel art (animation/layer) |
| Aseprite / LibreSprite | Desktop | Chuẩn ngành (Aseprite trả phí; LibreSprite GPL) |
| spritefusion-pixel-snapper | CLI (Rust) | Sửa pixel art AI thành lưới chuẩn |
| agent-sprite-forge | Agent skill | Sinh sprite/map từ prompt + script hậu-xử lý |

## Palette
- LOSPEC (lospec.com/palettes): Sweetie16, Endesga, mulfok32...
- Áp dụng qua Phaser `GradientMap` để đổi bảng màu.
