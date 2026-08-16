# TASK-082 — Implementation

> Code chính nằm ở `games/yuniebel-phaser/` (TASK-082, nâng cấp hướng E).

## Files mới

| File | Vai trò |
|------|---------|
| `games/yuniebel-phaser/tools/gen-sprites.mjs` | Sinh sprite sheet PNG (PNG encoder thuần 0 dependency: signature/IHDR/IDAT zlib level 9/IEND/CRC32) + pixel maps khớp palette vendor → `src/assets/` |
| `games/yuniebel-phaser/src/assets/{cat,butterfly,ghost,owner,cake}.png` + `sprites.json` | Assets sinh ra (17 frames: mèo 8, bướm 4, ma 2, chủ 1, bánh 2) — deterministic SHA256 |
| `games/yuniebel-phaser/src/fx/fx.js` | FX deterministic: mulberry32 PRNG, fxState (bụi/đom đóm/hơi thở/tia lửa theo scene+darkness+camX), renderFx, renderLightPool (ambient α theo scene + radial gradient), nightTintAlpha (guard NaN), fadeAlpha |
| `games/yuniebel-phaser/test/fx.test.js` | 15 vitest: PRNG, fxState, pool, tint, fade |
| `games/yuniebel-phaser/test/sprite-sheet.test.js` | 6 vitest: PNG decode/SHA256/frames/vendor baseline |
| `games/yuniebel-phaser/test/png-decode.mjs` | PNG decoder (5 filters + RGB/RGBA) — dùng cho probe pixel |
| `games/yuniebel-phaser/test/vendor-hashes.json` | SHA256 baseline 4 vendor files (TASK-081) |

## Files sửa

| File | Thay đổi |
|------|----------|
| `games/yuniebel-phaser/src/scenes/GameScene.js` | preload() (load.spritesheet cat/butterfly/ghost/cake + image owner), 5 Phaser Animations, add.sprite cho sprite động, parallax farTex/nearTex (scrollFactor 0.25/1.15), shake/zoom manual deterministic (sin/cos + lerp), fx/pool/tint layers (depth 25/26/27), quy tắc frozen (pauseAll, không play() khi frozen), renderSprites(rtime) dùng sheet |
| `games/yuniebel-phaser/vite.config.js` | `assetsInlineLimit: 0` — PNG ra file riêng trong dist/assets (AC-17/21) |
| `games/yuniebel-phaser/package.json` | `gen:sprites` + `pretest` + `pretest:visual` |
| `games/yuniebel-phaser/test/visual.spec.js` | Bump chờ 700ms; +7 shots mới; +5 test đặc biệt (AC-3 walk anim, AC-19 freeze-ngay, AC-9 pool probe, AC-11 shake/zoom, AC-20 flip bbox) |
| `games/yuniebel-phaser/test/brief/COMPARISON.md` | Cập nhật 25 shots + ghi chú thay đổi feature A/B/C/D |

## Không đổi (bắt buộc)

- `src/vendor/{core,sprites,audio,loader}.js` — byte-identical (SHA256 = baseline, AC-15).
- `games/yuniebel/` (vanilla) — untouched (AC-18).
- Không thêm dependency npm.
