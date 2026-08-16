# Critique vòng 2 — TASK-081 (spec v2)

> Ngày: 2026-08-15 · Bởi: critic agent (vòng 2 độc lập) · Trạng thái: **RESOLVED toàn bộ** (owner AIOS Orchestrator)
> Spec phản biện: spec v2. Sau resolve → **spec v3**.

## Kết luận critic

Spec v2 chưa đạt chuẩn implement (2.5/5): 3 P1 mới + 5 P2 + 7 P3. Tất cả đều hợp lệ sau khi đối chiếu code thật (drawCat flip, drawHaunted/drawHallway vẽ ghost/scare trong bg, game.js overlay đêm).

## Phần A — Resolution vòng 1 (15/15 RESOLVED — xác nhận)

P1-1 ✓ (lưu ý create-once — chuyển P2-B1), P1-2 ✓, P2-1 ✓, P2-2 ✓ (lưu ý P3-B2), P2-3 **SAI → sửa lại bởi P1-B1**, P2-4 ✓, P2-5 ✓, P2-6 ✓, P2-7 **chưa hoàn toàn → bổ sung P2-B2/P2-B3**, P2-8 ✓, P3-1..P3-14 ✓.

## Phần B — Resolution vấn đề mới

### P1-B1 — Texture mèo 96×96 + offset 12 KHÔNG ĐỦ khi dir<0 → **RESOLVED**
- **Vấn đề**: drawCat flip nội bộ quanh (x+8): dir<0 vùng hiển thị [x−14, x], raw vẽ tới x+30. Với 96×96 (32 logical) + offset 12 → đuôi/ria/tai trái/half đầu bị clip.
- **Quyết định**: Texture mèo **144×96 (48 logical ngang × 32 dọc)**, vẽ `drawCat(ctx, 14, 8, dir, fr, time)` (offset trái 14, top 8): raw max 14+30=44 ≤ 48 ✓; dir<0 hiển thị [0,14] ✓; dir>=0 [14,28] ✓. Image position `(p.x*3 − 42, p.y*3)`, anchor (0,0), KHÔNG setFlipX. Sửa ràng buộc 4 + mục Sprite động.

### P1-B2 — Ghost/scare sprite riêng = DOUBLE-DRAW → **RESOLVED**
- **Vấn đề**: drawHaunted đã vẽ ghost skull vào bg (kèm ẩn/hiện theo phase+dialogue); drawHallway đã vẽ scareActive 1..5 vào bg (world 130..300). Sprite riêng → vẽ 2 lần, lệch vị trí.
- **Quyết định**: **Sprite động = Player + Butterfly DUY NHẤT**. Ghost/scare nằm TRONG bg texture re-render (logic ẩn/hiện đã trong sprites.js) — không tạo sprite riêng. Butterfly: texture 96×96 (32 logical), vẽ `drawButterfly(ctx, 16, 16, time)` (padding 16 — bướm 8×6 quanh tâm), image position world `((b.x − camX)*3 + offsetScreen...)` → đơn giản: image đặt tại `(b.x*3, b.y*3)` anchor (0.5) → camera scroll tự lo phần dịch (parity vanilla: vẽ tại b.x−cx).

### P1-B3 — Thiếu dark overlay + light pool đèn hiên → **RESOLVED**
- **Vấn đề**: 2 overlay trong game.js vanilla (KHÔNG thuộc sprites.js): (1) dark `rgba(8,10,30,(darkness−0.5)*0.6)` khi darkness>0.5; (2) light pool `rgba(255,217,59,0.12)` fillRect `(287−cx)*3−12, 38*3, 24, 30`.
- **Quyết định**: Port vào bg texture **world-space** sau drawGarden (cx=0): dark fillRect `(0,0,960,270)` alpha theo công thức; light pool tại `(287*3−12, 114, 24, 30)` = `(849, 114, 24, 30)` (world — scroll tự dịch đúng). Fidelity parity 100% với vanilla.

### P2-B1 — createCanvas mỗi frame → **RESOLVED**
- **Quyết định**: Tạo 9 texture bg 1 lần trong `create()` (bg-title/garden/living/kitchen/haunted/hallway/birthday/gameover/end); mỗi frame: `ctx = texture.getContext()` → vẽ → `texture.refresh()`. Verify `refresh()` ở bước 0 (Phaser 3 có; Phaser 4 phải xác nhận).

### P2-B2 — Font "!" thiếu ×GX → **RESOLVED**
- **Quyết định**: Font **30px (42px khi scare 5)** monospace bold (đã ×GX như vanilla). Baseline lệch vài px chấp nhận — verify ở bước 0 (Phaser Text origin).

### P2-B3 — Visual chưa chờ fade trước freeze → **RESOLVED**
- **Quyết định**: AC-6 chuỗi đầy đủ mỗi shot: goto → click START → **chờ ≥500ms** (fade 0.35s hết) → setter → `freeze(true)` → chờ ≥100ms → chụp lần 1 → chờ 500ms → chụp lần 2 so khớp (port nguyên văn chuỗi vanilla).

### P2-B4 — Scale Manager chưa chốt → **RESOLVED**
- **Quyết định**: **KHÔNG dùng Scale Manager** (không khai báo `scale` hoặc `scale: NONE`) + giữ CSS resize vanilla (JS resize canvas.style). Verify `canvas` config Phaser 4 ở bước 0.

### P2-B5 — d-pad e2e thiếu touch emulation → **RESOLVED**
- **Quyết định**: e2e dùng `page.dispatchEvent('#pad-right', 'touchstart')` → giữ → `page.dispatchEvent('#pad-right', 'touchend')` (vanilla listener đơn giản nên hoạt động) + assert player.x tăng. (Không cần hasTouch context.)

### P3-B1 — `"type": "module"` → **RESOLVED** — thêm vào package.json (vite.config.js + playwright.config.js ESM export default).
### P3-B2 — Import UMD trong vitest → **RESOLVED** — `import "../src/vendor/core.js"` (side-effect) + `const core = window.AiosCore` (KHÔNG `import core from`).
### P3-B3 — e2e kịch bản chi tiết → **RESOLVED** — port nguyên văn helper vanilla (gotoGame/moveTo/hold/chaseButterfly — bước 120ms/40ms, hội tụ |dx|,|dy|≤2) để parity thời gian 40–90s.
### P3-B4 — AC-6 nguồn chuẩn → **RESOLVED** — ghi nguồn `TASK-078/implementation/brief-visuals.md` + tiêu chí đối chiếu cấu trúc chính theo từng ref.
### P3-B5 — Smoke import Phaser rủi ro → **RESOLVED** — bước 0 verify; nếu Phaser crash ở module-load trong jsdom → smoke chỉ assert config object thuần + dynamic import try/catch.
### P3-B6 — Screenshot WebGL rủi ro → **RESOLVED** — ghi vào bảng rủi ro; bước 0 chụp thử 1 frame sớm; nếu ảnh rỗng → `render: { preserveDrawingBuffer: true }` hoặc `game.renderer.snapshot()`.
### P3-B7 — Phaser update delta ms → **RESOLVED** — GameScene.update(time, delta): `game.update(delta/1000, input)` (core nhận giây).

## Phần C — AC bổ sung

- AC-6: + nguồn brief-visuals.md + chuỗi chờ fade (P2-B3).
- AC-10: + e2e assert scareCount=5 + 5 shot hallway-scare1..5 đối chiếu 5 drawScare* khác nhau (COMPARISON.md).
- AC-12: + cơ chế touch emulation dispatchEvent (P2-B5).
- AC-11: + assert SFX cụ thể (footstepGrass/ting) đếm tăng sau sự kiện.
- AC-7: camX là nguồn sự thật — chấp nhận (không bắt buộc getScroll).

## Trạng thái

- [x] Tất cả P1/P2/P3 vòng 2 **RESOLVED**.
- Spec **v3** phản ánh đầy đủ (đang chờ review trước implement).
