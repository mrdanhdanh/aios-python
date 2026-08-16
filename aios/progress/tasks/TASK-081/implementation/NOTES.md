# NOTES — TASK-081 implement (2026-08-15)

## Verify Phaser 4.2.1 API (bước 0 — P3-11)

Đã verify THẬT trên `phaser@4.2.1` (npm registry + grep phaser.esm.js):
- `CanvasTexture#refresh()` — **TỒN TẠI** (JSDoc @since 3.7.0, gọi `this._source.update()`) ✓
- `CanvasTexture#getContext()` — public ✓
- `textures.createCanvas(key, w, h)` ✓
- `Camera#setScroll(x, y)` ✓
- Game config `canvas` (nhận element, default false) + **bắt buộc width/height 480×270** ✓
- `add.image(...).setOrigin(0,0).setDepth(n)`, `add.rectangle(...).setScrollFactor(0)` ✓
- `add.text(...)` ✓

## Quyết định phát sinh trong implement

1. **UMD vendor + Vite CJS-interop** (P2-2/P3-B2 — PHÁT HIỆN MỚI): import trực tiếp `vendor/core.js` trong Vite/vitest KHÔNG gán `window.AiosCore` vì Vite transform `module.exports` thành ESM wrapper → nhánh browser không chạy. **Giải pháp**: `src/vendor/loader.js` (file adapter RIÊNG — vendor vẫn byte-identical AC-16): nhúng raw (`?raw`) + indirect eval → UMD gán window như browser. Không sửa 3 file vendor.
2. **`"type": "module"`** (P3-B1): spec files Playwright phải ESM (import, không require); `__dirname` → `fileURLToPath(import.meta.url)` (visual.spec.js).
3. **Playwright chạy từ root sai** (PHÁT HIỆN MỚI): `npx playwright test` phải chạy từ `games/yuniebel-phaser/` (2 node_modules @playwright/test khác nhau — vanilla + phaser → xung đột). Script `npm test` đã chạy trong thư mục đúng.
4. **Viewport e2e**: 480×270 (khớp canvas — ảnh chụp đúng 480×270).
5. **Phaser import trong Node/jsdom crash** (`window is not defined`) — smoke test dùng dynamic import try/catch (P3-B5), boot thật = Playwright.

## Cấu trúc render (khớp spec v3)

- 9 bg CanvasTexture create-once (GARDEN/HALLWAY 960×270, còn lại 480×270), re-render mỗi frame + `refresh()`.
- drawGarden cx=0 + dark overlay world-space + light pool đèn hiên (849,114,24,30).
- Player texture 144×96, `drawCat(ctx,14,8,...)`, position `(p.x*3−42, p.y*3−24)` (R2).
- Butterfly 96×96 `drawButterfly(ctx,16,16)`, position `(b.x*3, b.y*3)`.
- "!" Text 30px/42px (×GX), depth 20.
- camera `setScroll(camX*3, 0)`; flash/fade rectangles scrollFactor 0, depth 30.
- debug hook: `window.__yuniebel = {debug, getState, camX, core, audio}`.

## Files chính

| File | Vai trò |
|------|---------|
| `src/main.js` | Phaser boot + input window + resize CSS + debug hook |
| `src/scenes/GameScene.js` | 1 scene: update core (delta/1000) + renderBg/renderSprites/renderOverlays + audio + syncUI |
| `src/ui/ui.js` | camX/moodForPhase/handleSoundFlags/syncUI (port game.js vanilla) |
| `src/vendor/loader.js` | UMD adapter (?raw + indirect eval) — file riêng, vendor không sửa |
| `test/core.test.js` | 27 assertion vitest (migrate vanilla, bỏ process.exit — R3) |
| `test/smoke.test.js` | 3 test: vendor load + drawGarden mock ctx + config Phaser |
| `test/e2e.spec.js` | 8 test (2 playthrough thật + camX + d-pad + mood/SFX + mute/ui + freeze) |
| `test/visual.spec.js` | 17 shot (freeze determinism ×2) → test-results/shots/ |

## Bug fixes trong test phase (2026-08-15)

1. **Phaser.AUTO crash với custom canvas** (ROOT CAUSE e2e toàn bộ fail "Target crashed"): Phaser 4 khi truyền `canvas` tùy chỉnh BẮT BUỘC `renderType` tường minh (`Phaser.AUTO` bị từ chối: "Must set explicit renderType in custom environment"). **FIX** (`main.js`): compute `renderType = WEBGL nếu context webgl tồn tại, fallback CANVAS` rồi truyền `type: renderType`. Verify qua `diagnose.mjs`: boot thành công → phase TITLE → G_INIT/GARDEN.
2. **Determinism fail khi freeze** (AC-13 + visual R1): `gameCore.update` có `if (state.frozen) return;` (core.js:346) → `s.time` đứng yên → sprite deterministic. NHƯNG `renderBg(time)` dùng `time` từ Phaser loop (tiếp tục tăng) → bg vẫn animate (drawGarden/drawKitchen... nhận param `time`) → 2 screenshot 500ms cách nhau KHÁC nhau. **FIX** (`GameScene.js` `update`): tính `rtime = s.frozen ? (this._frozenTime ?? (this._frozenTime = time)) : (this._frozenTime = null, time)` và truyền `rtime` vào `renderBg`. Khi unfreeze reset `_frozenTime=null`. Kết quả: AC-13 + visual R1 + 17 shot đều PASS.
3. **Vitest double-run Playwright specs** (suite fail): `npm test` = `vitest run && playwright test`. Vitest default include `*.{test,spec}.js` → cố chạy `e2e/visual.spec.js` (thuộc Playwright, cần browser) → "2 failed suites". **FIX** (`vite.config.js`): `test.include = ["test/**/*.test.js"]` → chỉ unit/integration; `*.spec.js` thuộc Playwright. Sau fix: vitest 2 files / 29 tests PASS, 0 failed suite.
4. **`require is not defined` trong ESM spec** (P3-B1): `type:module` → spec files dùng `import` thay `require`; `visual.spec.js` dùng `fileURLToPath(import.meta.url)` thay `__dirname`.

## Kết quả test cuối (TASK-081 DONE)

- Vitest: **29/29 PASS** (core 27 + smoke 3) — 2 files, 0 failed.
- Playwright: **27/27 PASS** (e2e 8 + visual 19: 17 shot + R1 + AC-7b).
- Tổng: **56/56 PASS**.
- Vendor byte-identical (AC-16): SHA256 core/sprites/audio = games/yuniebel/src/ ✓.
- Vanilla games/yuniebel/ KHÔNG đổi (AC-13) ✓.
