# Phaser 4 — Pixel-Art Filters (cheat-sheet cô đọng)

> Nguồn: phaserjs/phaser `skills/filters-and-postfx/SKILL.md` (Phaser 4.2.1)

## Bật filter
- **Camera**: có sẵn `filters.internal` / `filters.external`. Không cần enable.
- **Game object** (sprite/image/container): phải gọi `obj.enableFilters()` trước.

```js
const s = this.add.sprite(400, 300, 'cat');
s.enableFilters();
s.filters.internal.addBlocky({ amount: 4 });
```

## Internal vs External
- `internal`: chạy TRƯỚC camera transform → theo local space của object (rẻ hơn).
- `external`: chạy SAU camera transform → screen space (đắt hơn, full-screen).
- Ưu tiên internal khi có thể.

## Filter pixel-art quan trọng
| Filter | Method | Dùng cho |
|--------|--------|----------|
| Blocky | `addBlocky({amount})` | Pixelation GIỮ nguyên màu (không blend) — look pixel chuẩn |
| Pixelate | `addPixelate(amount)` | Mosaic, `pixel = 2 + amount`, có blend màu |
| GradientMap | `addGradientMap(config)` | Recolor theo brightness qua ColorRamp → palette-swap |
| Quantize | `addQuantize({mode, gamma, dithering})` | Giảm số màu → retro palette (RGBA/HSVA) |
| ColorMatrix | `addColorMatrix()` | `.colorMatrix.sepia()/.night()/.grayscale()/.lsd()...` |

## Scale-profile (pixel-perfect)
Đặt `pixelArt: true` trong game config để disable smoothing:
```js
new Phaser.Game({ pixelArt: true, roundPixels: true, ... });
```

## Gotchas
1. WebGL only — Canvas renderer bỏ qua filter.
2. `enableFilters()` bắt buộc cho game object.
3. Mỗi object có filter = thêm draw call; test performance sớm.
4. Filter chạy tuần tự; output filter trước feed filter sau.
5. Glow `quality`/`distance` immutable sau khi tạo → destroy+recreate để đổi.
6. Không có Bloom riêng → dùng `ParallelFilters` (Threshold + Blur + ADD) hoặc
   `Phaser.Actions.AddEffectBloom`.
7. CaptureFrame cần `camera.setForceComposite(true)`.

## Ví dụ pixel-night
```js
const cam = this.cameras.main;
cam.filters.internal.addColorMatrix().colorMatrix.night(0.5);
cam.filters.internal.addBlocky({ amount: 3 });
```
