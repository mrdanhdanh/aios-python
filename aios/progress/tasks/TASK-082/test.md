# TASK-082 — Test report

> **Date**: 2026-08-16 | **Trạng thái**: ✅ ALL PASS
> Test thật: vitest 50/50 + Playwright 38/38 = **88/88 PASS**

## 1. Vitest (jsdom, không boot Phaser) — 50/50

| File | Số test | Kết quả |
|------|---------|---------|
| `core.test.js` (regression TASK-078/081) | 26 | ✅ PASS |
| `smoke.test.js` (regression TASK-081) | 3 | ✅ PASS |
| `fx.test.js` (TASK-082 mới) | 15 | ✅ PASS |
| `sprite-sheet.test.js` (TASK-082 mới) | 6 | ✅ PASS |

**fx.test.js** — AC-7 (PRNG mulberry32 deterministic, hashSeed, không Math.random), AC-8 (bụi GARDEN ngày 14 hạt / đom đóm đêm 10 / hơi thở HAUNTED 8 / tia lửa BIRTHDAY 6, LIVING 0 — C1-07), AC-8e (fxState cùng input → cùng output), AC-8f (camX trừ 90px — R-02), AC-12 (fadeAlpha ease-out (fadeT/0.6)²×0.75), AC-13 (nightTintAlpha: timers.dark 2.5→0, 1.0→0.18, chỉ GARDEN), AC-23 (guard R-01: undefined+darkness=1 → 0.18, không NaN), AC-9a (ambientAlpha theo scene), AC-9b (pool không fill khi α=0).

**sprite-sheet.test.js** — AC-1a (5 PNG signature + IHDR + IDAT decode), AC-1b (sprites.json 17 frames: cat 8/bfly 4/ghost 2/owner 1/cake 2 + meta), AC-2 (pixel alpha: opaque > 100 + transparent > 50), AC-15 (vendor SHA256 = baseline `test/vendor-hashes.json`), AC-21 (dist/assets ≥ 5 PNG).

## 2. Playwright (chromium thật, webServer preview) — 38/38

| Nhóm | Số test | Kết quả |
|------|---------|---------|
| `e2e.spec.js` (regression) | 8 | ✅ PASS |
| `visual.spec.js` — 25 shots cũ + mới (byte-compare frozen + non-empty) | 25 | ✅ PASS |
| `visual.spec.js` — test đặc biệt | 5 | ✅ PASS |

**Shots mới TASK-082** (trong test-results/shots/): `cat-idle-cycle.png` (mèo sheet + anim idle, frozen), `garden-night-fx.png` (đom đóm + light pool), `haunted-ghost2.png` (ghost sprite + freeze-ngay), `birthday2.png` (owner + cake sprite), `living-fx.png` (sconce pool), `hallway-scare5-zoom.png` (scare 5 + zoom).

**Test đặc biệt**:
- **AC-3 cat-walk**: giữ phím d → ≥ 2 frames khác + 2 shot khác (anim chạy, không byte-compare — C2v2-03).
- **AC-19 freeze-ngay**: setPhase H_INIT + freeze NGAY → 2 shot byte-identical (quy tắc C2v2-17: frozen không play()).
- **AC-9 light pool probe**: decode PNG screenshot (png-decode.mjs — hỗ trợ filter 0..4 + colorType RGB/RGBA) → brightness crop player > crop góc dưới-trái +10/255.
- **AC-11 shake+zoom**: shake scroll offset ≠ 0 (3 mốc) + zoom lerp ≈1.04 (m1=1.039→m2=1.04, loop.time tăng — xác nhận game loop chạy) + frozen byte-compare.
- **AC-20 flip bbox**: bbox mèo (màu #f5a623) dir=1 vs dir=-1 cùng vùng ±4px.

## 3. Các bug phát hiện khi test (đã sửa)

1. **`src/fx/fx.js` lightSources non-player đọc sai index `src[4]` thay vì `src[3]`** → `pa` undefined → `pa.toFixed` crash → game loop dừng ở L_SEARCH (LIVING) — phát hiện qua pageerror + phân lập phase. FIX: `r = src[2]; pa = src[3]`.
2. **Phaser camera effects (`shake`/`zoomTo`) không update tự động trong setup này** (elapsed luôn 0 — camera.update không được gọi) + dùng Math.random (phá determinism) → chuyển **shake/zoom manual deterministic**: scroll offset sin/cos theo rtime + zoom lerp theo dt (không phụ thuộc camera effects Phaser).
3. **`add.image` không có `anims`** → `play()` crash khi test đọc currentFrame → đổi sprite động sang `add.sprite`.
4. **PNG screenshot Playwright dùng filter Paeth (4) + colorType khác** → nâng png-decode hỗ trợ filter 0..4 + RGB/RGBA.
5. **WebGL getImageData rỗng** (preserveDrawingBuffer=false) → probe AC-9 chuyển sang decode PNG screenshot.
6. **WebServer EBUSY** (build mới ghi đè dist khi preview cũ giữ lock) → quy trình: kill node → build → preview → test reuse server.

## 4. Verify thêm

- `npm run build` PASS (vite 6, 17 modules) — `dist/assets/` chứa 5 PNG (assetsInlineLimit 0, AC-17/21) ✓
- `git diff --quiet HEAD -- games/yuniebel` = 0 (vanilla untouched, AC-18) ✓
- SHA256 assets deterministic (chạy gen 2 lần → giống hệt) ✓
- Vendor 4 files SHA256 = baseline TASK-081 (AC-15) ✓

## 5. Fail-closed (bài học TASK-079)

- KHÔNG dùng `toHaveScreenshot` thiếu ref — mọi shot: non-empty (length > 1000) + byte-compare 2 shot frozen cách 500ms.
- Mọi test mới có assert cụ thể (probe số, bbox, frame anim) — không shot "chụp cho có".
