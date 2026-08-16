# Review — TASK-081 (pre-implement, spec v3 + tasks.md)

> Ngày: 2026-08-15 · Bởi: reviewer agent · Trạng thái: **CHANGES REQUESTED** (2 blocking trước implement)

## Tổng quan

Task scaffold `games/yuniebel-phaser/` (Vite + Phaser 4.2.1) + migrate logic/render/audio từ vanilla:
vendor byte-identical (AC-16), 1 GameScene re-render bg texture mỗi frame, DOM overlay giữ nguyên,
3 tầng test (vitest core/smoke + Playwright e2e/visual). Spec v3 phản ánh gần hết 15/15 (vòng 1) +
15/15 (vòng 2) resolution critique. **Verify thật trên registry**: `phaser@4.2.1` tồn tại; trong
`phaser.esm.js` có `CanvasTexture#refresh()` (refresh WebGLTexture từ canvas source, JSDoc @since 3.7.0),
`CanvasTexture#getContext()`, `textures.createCanvas(key,w,h)`, `Camera#setScroll(x,y)`, config `canvas`
(nhận element, default `canvas: false`). Các API cốt lõi spec đều có thật.

**Phát hiện chính**: §3 "Sprite động" của spec v3 KHÔNG được cập nhật theo P1-B1/P1-B2 (vẫn là bản
P2-3 cũ → mâu thuẫn nội bộ với ràng buộc 4), và công thức vị trí dọc mèo trong P1-B1 bị lệch
**+8 logical (24px screen)** so với vanilla — cả 2 đều do critique-2 chỉ phân tích chiều NGANG
của drawCat, bỏ sót chiều DỌC.

## Đối chiếu tiêu chí chấp nhận

| AC | Đánh giá | Ghi chú |
|----|----------|---------|
| AC-1 | OK | dev/build + base './' — chi tiết implement |
| AC-2 | Cần sửa | 27 T() đếm đúng; migrate phải bỏ `process.exit` (R3) |
| AC-3 | OK | Không boot Phaser jsdom — đúng (P2-1) |
| AC-4 | OK | ≤120s, parity helper port (P3-B3) — timeout 120s đủ |
| AC-5 | OK | như AC-4 |
| AC-6 | Cần sửa | Chuỗi freeze đúng (P2-B3); ảnh sẽ SAI nếu không sửa R2 (mèo chìm/clip chân) |
| AC-7 | OK | clamp(p.x−77,0,sc.w−160): x≤77 → 0, x>77 → tăng — đúng |
| AC-8 | OK | dialogue DOM giữ nguyên |
| AC-9 | OK | choice core giữ nguyên |
| AC-10 | Cần sửa | scare trong bg (P1-B2 ✓), nhưng "!" Text + mèo phụ thuộc R2 |
| AC-11 | OK | getMood/getStats có thật trong audio.js (vanilla e2e đang PASS) |
| AC-12 | OK | dispatchEvent touchstart trên listener vanilla — chạy được kể cả dpad hidden |
| AC-13 | OK | `git diff --quiet HEAD -- games/yuniebel` — đúng (test-results untracked loại) |
| AC-14 | OK | pages.yml hiện chỉ upload `path: games` — build+rm node_modules hợp lý; nên thêm setup-node (R6) |
| AC-15 | OK | — |
| AC-16 | OK | diff --no-index ×3 — đúng |

## Vấn đề phát hiện

### R1 — §3 "Sprite động" stale: mâu thuẫn nội bộ spec v3 (Blocking)
- **Bằng chứng**: `spec.md` §3 vẫn ghi *"texture cố định kích thước ≥96×96 = 32 logical, P2-3: Player: vẽ drawCat vào texture 96×96 với offset trái 12 logical, anchor (0,0), position (p.x*3 − 12*3, p.y*3)"* và *"Butterfly/GhostSkull/Scare1..5: texture riêng (96×96), hiện/ẩn theo state (butterfly, H_BLOCK/H_EXIT ghost, scareActive)"* — trong khi ràng buộc 4 + header v3 ghi **144×96 / offset 14 / position (p.x*3−42)** và **chỉ Player+Butterfly động (P1-B2)**. `critique-2.md` P1-B1 ghi "Sửa ràng buộc 4 + mục Sprite động" — nhưng chỉ ràng buộc 4 được sửa, §3 còn nguyên bản P2-3.
- **Hệ quả**: implementer đọc §3 sẽ tạo texture 96×96/offset 12 (−36px) hoặc tạo sprite riêng cho Ghost/Scare → double-draw đúng lỗi P1-B2 đã cảnh báo (drawHaunted/drawHallway đã vẽ ghost/scare vào bg — xác nhận trong sprites.js: ghost skull vẽ khi `phase !== "H_INIT" || !dialogue`, scare1..5 vẽ world 130..300 trong drawHallway).
- **Đề xuất**: sửa §3 "Sprite động" = bản P1-B1/P1-B2 (144×96, offset trái 14, chỉ Player+Butterfly, KHÔNG setFlipX).

### R2 — Vị trí dọc mèo lệch +8 logical: drawCat(ctx,14,8) + position (p.x*3−42, p.y*3) (Blocking)
- **Bằng chứng**: `sprites.js` drawCat vẽ từ y−1 (tai) đến y+16 (chân). Với y=8 trong texture 96px (32 logical): mèo chiếm [7,24] texture. Image position y = p.y*3 → mèo hiển thị world [p.y+7, p.y+24], trong khi vanilla `drawPlayer` vẽ drawCat(ctx, p.x−cx, p.y) → [p.y−1, p.y+16]. Lệch **+8 logical = 24px screen**. Spawn GARDEN (107,70): chân mèo = (70+24)*3 = **282 > 270 → clip 12px đáy canvas**. Hitbox core [p.y+2, p.y+14] không đổi → mèo visual "chìm" dưới hitbox 10px (vanilla chỉ 2px). P1-B1 phân tích kỹ chiều ngang (44≤48 ✓, [0,14]/[14,28] ✓) nhưng KHÔNG phân tích chiều dọc.
- **Đề xuất**: position dọc phải trừ offset: **image (p.x*3 − 42, p.y*3 − 24)** (hoặc vẽ drawCat(ctx,14,0) — mất 1px tai, kém hơn). Sửa cả ràng buộc 4, §3, tasks.md "Ghi chú triển khai", và thêm 1 check visual (mèo tại spawn không clip chân, đối chiếu brief-visuals.md).

### R3 — tasks.md P4 thiếu lưu ý migrate core.test.js: process.exit (Major)
- **Bằng chứng**: `games/yuniebel/test/core.test.js` cuối file có `process.exit(fail > 0 ? 1 : 0)` và `require("../src/core.js")` — vitest (ESM + jsdom) chạy file này sẽ: `require` crash ở module-load nếu không chuyển import side-effect (đã có P3-B2 ✓), và `process.exit` sẽ giết vitest worker → báo lỗi worker hoặc kết quả không sạch.
- **Đề xuất**: ghi vào tasks P4: "bỏ dòng process.exit cuối file; giữ nguyên 27 T() và nội dung assert; assert pass/fail qua biến đếm + expect cuối file (hoặc throw khi fail>0)".

### R4 — Diễn đạt font "!" chưa ×GX (Minor)
- `spec.md` §3 ghi *"font monospace bold 10px (14px khi scare 5)"* — chưa ×GX; P2-B2 + header + AC-10 ghi 30/42px. Sửa §3 cho nhất quán (30px/42px).

### R5 — AC-6 "≥6 ảnh" nhưng liệt kê 7 mục (Minor)
- AC-6 liệt kê title, garden-day, living, kitchen-blood, haunted, hallway-scare, birthday = 7 + AC-10 thêm 5 shot scare → tổng 12. Ghi rõ con số để khỏi tranh cãi khi đánh giá.

### R6 — pages.yml nên pin Node (Minor)
- Workflow hiện không có `actions/setup-node` — ubuntu-latest có Node sẵn (đủ cho Vite 7) nhưng nên pin (20/22) để build CI ổn định; giữ nguyên `rm -rf games/yuniebel-phaser/node_modules` TRƯỚC upload (AC-14).

### R7 — Ghi chú depth ordering Phaser (Minor)
- Vanilla vẽ theo thứ tự: bg → "!" text → player → flash → fade. Phaser: bg image (depth 0) < player image < "!" Text < flash/fade rectangle — nếu không set depth, flash/fade rectangle phải được tạo SAU cùng (default order theo creation). Thêm 1 dòng vào tasks P3.

## Trả lời các câu hỏi kỹ thuật trọng tâm

- (a) `texture.refresh()`: **TỒN TẠI** trong phaser@4.2.1 — verified trong `phaser.esm.js` (`CanvasTexture#refresh`, JSDoc "@method Phaser.Textures.CanvasTexture#refresh @since 3.7.0": "refresh the WebGLTexture from the Canvas source", gọi `this._source.update()`). Không cần fallback. `getContext()` cũng public.
- (b) Camera scroll: **ĐÚNG** — `setScroll` dịch camera viewport trong world; image bg tại (0,0) world đứng yên, chỉ phần trong viewport được hiển thị → parity vanilla (drawHallway/drawGarden vẽ translate(−cx·GX), với cx=0 vẽ full 320 map vào texture 960×270 ✓).
- (c) `locator('#game').screenshot()` với canvas WebGL: Playwright capture qua CDP compositor — hoạt động với WebGL (không cần flag); fallback P3-B6 (`preserveDrawingBuffer`/`game.renderer.snapshot()`) giữ lại đúng.
- (d) `canvas` vs `parent`: Phaser 4.2.1 config có option `canvas` (default `false` — nhận element) — dùng `canvas: document.getElementById('game')` đúng; **bắt buộc khai báo `width/height: 480×270`** trong config (nếu thiếu, Phaser dùng default 800×600 → resize canvas, phá e2e screenshot). CSS resize vanilla (canvas.style) vẫn hoạt động — không cần Scale Manager (P2-B4 ✓).
- (e) `input.start` cho title: **port đúng** — core `updateGame` xử lý `input.start` khi scene TITLE/GAMEOVER/END (startGame + reset state); giữ window listener + btn-start click → `oneShot.start` (như game.js vanilla).

## Chất lượng tổng thể

- Đúng spec: **không hoàn toàn** — 2 blocking (R1 mâu thuẫn nội bộ §3, R2 lệch offset dọc).
- Resolutions critique: 15/15 vòng 1 ✓; vòng 2: P1-B3..P3-B7 ✓, P1-B1/P1-B2 vào ràng buộc 4 nhưng **chưa vào §3**.
- Test phủ: đủ (core 27 + smoke + e2e 2 playthrough + visual 12 shot + camX/audio/mute/dpad).
- Code sạch: N/A (chưa implement) — kiến trúc spec rõ ràng, tasks P0→P6 có thứ tự hợp lý, thiếu sót duy nhất là R3 (note migrate core.test.js).

## Kết luận

- [ ] APPROVED
- [x] **CHANGES REQUESTED** — blocking trước implement:
  1. **R1**: sửa §3 "Sprite động" theo P1-B1/P1-B2 (144×96, offset 14, chỉ Player+Butterfly) — xóa mâu thuẫn với ràng buộc 4.
  2. **R2**: sửa vị trí dọc mèo thành `(p.x*3 − 42, p.y*3 − 24)` (hoặc tương đương) ở ràng buộc 4 + §3 + tasks.md; thêm check visual "mèo không clip chân tại spawn".
  3. **R3** (Major, nên sửa cùng lúc): bổ sung note bỏ `process.exit` khi migrate core.test.js vào tasks P4.

---

## RESOLUTION (bởi AIOS Orchestrator — 2026-08-15) → APPROVED

| ID | Resolution |
|----|------------|
| R1 | Đã sửa §3 "Render pipeline (v3)": Player texture **144×96**, vẽ drawCat(ctx,14,8,...), position (p.x*3−42, p.y*3−24), **chỉ Player+Butterfly động** (ghost/scare trong bg texture) — đồng bộ ràng buộc 4 |
| R2 | Đã sửa position dọc: **(p.x*3 − 42, p.y*3 − 24)** (bù offset dọc 8 logical → mèo world [p.y−1, p.y+16] khớp vanilla, không clip chân tại spawn) — ràng buộc 4 + §3 + tasks.md "Ghi chú triển khai" |
| R3 | Đã ghi vào tasks P4: bỏ process.exit khi migrate core.test.js |
| R4 | §3 font "!" đã sửa thành 30px (42px scare 5) |
| R5 | AC-6 đã ghi rõ: 7 ảnh chính + 5 hallway-scare = **12 shot** |
| R6 | Đã thêm setup-node pin Node 20 vào tasks P5 (pages.yml) |
| R7 | Đã thêm depth ordering (bg 0 < sprite 10 < \"!\" 20 < flash/fade 30) vào tasks P3 + §3 |

- [x] **APPROVED** — R1..R7 resolved trong spec v3 + tasks.md. Đủ điều kiện implement.
