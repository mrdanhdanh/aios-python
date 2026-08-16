# TASK-082 — Spec: Nâng cấp Phaser 4 hướng E (Sprite Sheet PNG + FX + Parallax + Transition)

> **Status**: v3.1 — sau review (R-01..R-07 resolved) → **APPROVED để implement**
> **Date**: 2026-08-16
> **Owner**: AIOS Orchestrator
> **Base**: `games/yuniebel-phaser/` (TASK-081 — 56/56 test PASS, vendor byte-identical)
> **Tham khảo hình ảnh**: `games/yuniebel-phaser/imagedata.md` (mô tả pixel-art chi tiết 4 nhóm ảnh `games/yuniebel/baseimg/1..6.png`: 5 kiểu hù hành lang, cảnh sinh nhật, phòng khách+bếp vết máu, title screen START)
> **Yêu cầu user**: chọn hướng **E** (tất cả A+B+C+D) — "tự hoạt động, tự quyết định"

**Map sprite → ảnh tham khảo (C3-07)**: cat/owner/cake → ảnh 2 (sinh nhật) + ảnh 3 (phòng khách — mèo cam trắng); ghost → ảnh 1 (ma xanh đầu lâu) + ảnh 4 (bóng đen mắt vàng); hallway scare → ảnh 1 (5 kiểu hù); butterfly + sky parallax → ảnh 6 (title START, mây xốp); kitchen/blood → ảnh 3 (bên phải).

---

## 1. Mục tiêu

Nâng cấp bản Phaser 4 của webgame Yuniebel's Cat theo 4 hướng:

- **A. Sprite sheet PNG thật + Phaser Animation** — thay canvas primitives cho sprite động bằng pixel-art PNG có khung hình: mèo (walk 4 frames, nháy mắt, đuôi vẫy), bướm (vỗ cánh 4 frames), ma xanh đầu lâu (float 2 frames), chủ nhân (idle), bánh kem (nến cháy 2 frames).
- **B. Hiệu ứng (particle/lighting) deterministic** — bụi bay (GARDEN ngày), đom đóm (GARDEN đêm), hơi thở ma (HAUNTED), tia lửa lò sưởi (LIVING/BIRTHDAY), light pool thay overlay đêm phẳng (radial gradient quanh nguồn sáng: mèo, đèn hiên, lò sưởi, nến bánh, ma).
- **C. Parallax + camera effect** — GARDEN: mây ×2 lớp scroll chậm + cỏ/hoa tiền cảnh; camera shake khi scare tăng; zoom nhẹ khi scare 5.
- **D. Transition mượt** — fade chuyển cảnh ease-out dài hơn; night tint lerp dần khi trời tối.

## 2. Phạm vi

### 2.1. Trong phạm vi (IN)

| STT | Hạng mục | Chi tiết |
|-----|----------|----------|
| 1 | `tools/gen-sprites.mjs` | Script Node thuần (0 dependency, dùng `zlib.deflateSync(buf, {level: 9})` nội bộ — C3-04) sinh sprite sheet PNG từ pixel maps khai báo trong script → `src/assets/*.png` + `src/assets/sprites.json` (frame data). Deterministic: cùng đầu vào → cùng byte output. Npm scripts (C2-11): `"gen:sprites": "node tools/gen-sprites.mjs"` + `"pretest": "node tools/gen-sprites.mjs"` (npm chạy pretest trước test). |
| 2 | `src/assets/` | PNG + JSON sinh ra: `cat.png` (mèo 48×48/frame ×8: walk0..3, idle, blink, tail0, tail1), `butterfly.png` (48×48 ×4 frames vỗ cánh), `ghost.png` (54×72 ×2 frames float), `owner.png` (48×48 ×1), `cake.png` (60×48 ×2 frames nến), `sprites.json` (frame name/x/y/w/h/duration). |
| 3 | `src/scenes/GameScene.js` | Sửa: thêm `preload()` (load.spritesheet/load.image/load.json — C1-05) + tạo Phaser Animations (anims.create) khi create + `anims.pauseAll()/resumeAll()` khi frozen (C1-01); `renderSprites` dùng sprite sheet + `anims.play`/`setFrame` thay cho `drawCat`/`drawButterfly`; ma/chủ/bánh kem phủ đè lên bg ở tọa độ cố định (ma (136,14), chủ GARDEN (286,52)/BIRTHDAY (96,42), bánh (70,40) — C1-06/C2-10); overlay đêm chuyển sang light pool; thêm parallax layers, camera shake/zoom, fade ease-out, night tint. |
| 4 | `src/fx/fx.js` | Module mới: PRNG seeded (mulberry32) deterministic; particle state (bụi/đom đóm/hơi thở/tia lửa) tính từ `s.time` + seed cố định — KHÔNG dùng `Math.random`; light pool render vào CanvasTexture riêng; tất cả đóng băng khi `s.frozen` (visual determinism AC-13). |
| 5 | `src/main.js` | Import PNG/JSON làm module để Vite emit vào dist (C1-04): `import catUrl from "../assets/cat.png"` + `import spritesJson from "../assets/sprites.json"` → truyền vào GameScene qua registry/import; scene `preload()` dùng `this.load.spritesheet(key, catUrl, {frameWidth:48, frameHeight:48})` (C1-05). |
| 6 | `src/ui/ui.js` | Giữ nguyên logic camX/mood/syncUI (không bắt buộc sửa). |
| 7 | `test/` | Thêm `test/fx.test.js` (PRNG deterministic, particle công thức, light pool, transition lerp), `test/sprite-sheet.test.js` (PNG signature/IHDR/alpha + frame JSON + SHA256 deterministic + vendor-hashes.json — C2-11/C3-06), `test/vendor-hashes.json` (4 SHA256 baseline TASK-081), cập nhật `visual.spec.js` (shots mới: cat-walk (không freeze), garden-night-fx, haunted-ghost2, birthday2, living-fx, hallway-scare5-zoom) — giữ regression cũ + cơ chế non-empty + byte-compare frozen (C2-09). |
| 8 | `docs/` | Cập nhật README game nếu cần; ghi chú imagedata.md là tham khảo. |

### 2.2. Ngoài phạm vi (OUT)

- ❌ **KHÔNG sửa `src/vendor/{core,sprites,audio,loader}.js`** — byte-identical (AC-16, SHA256 không đổi).
- ❌ Không đổi hành vi game: 13 câu thoại, 9 task, 5 kiểu hù, mood nhạc, spawn/collision — core logic giữ nguyên.
- ❌ Không thay 5 scare props trong HALLWAY (chúng nằm trong bg vendor, đã animate theo time — giữ nguyên để không phá 5 kiểu hù khớp brief).
- ❌ Không thêm dependency npm mới (chỉ dùng Phaser 4 sẵn có).
- ❌ Không đụng `games/yuniebel/` (bản vanilla) và `games/yuniebel-phaser/src/vendor/`.
- ❌ Không thêm scene mới, không đổi canvas 480×270, không đổi DOM overlay UI.

## 3. Kiến trúc đề xuất

```
GameScene (preload/create/update/render)
├── preload(): load.spritesheet(cat/butterfly/ghost) + load.image(owner/cake) + load.json(sprites)
├── bg texture (giữ nguyên — vendor draw*)
├── [MỚI] parallax layers (chỉ GARDEN): farTex 960×270 (mây, redraw mỗi frame bằng rtime — C2-13)
│     + nearTex 1200×270 (cỏ/hoa lặp 200px — C2-03); depth 0.05 / 0.08, scrollFactor 0.25 / 1.15
├── bg image (giữ nguyên)
├── [MỚI] fx Tex (480×270 screen-space, depth 25, scrollFactor 0) — particles seeded (bụi/đom đóm/hơi thở/lửa)
├── [MỚI] night tint rect (480×270, depth 26, scrollFactor 0) — lerp alpha theo timers.dark
├── [MỚI] light pool Tex (480×270, depth 27, scrollFactor 0) — fill dark + radial gradients sáng (TRÊN tint — C2-08)
├── player: sprite sheet cat.png + Phaser Animations (walk 4f / idle-cycle 6f — C2-04)
├── butterfly: sprite sheet butterfly.png + anim flutter 4f
├── [MỚI] ghost/owner/cake: sprite images phủ đè lên bg (tọa độ cố định — C1-06/C2-10)
├── "!" marks (giữ nguyên, depth 20)
├── flash/fade rects (fade ease-out mới, depth 30)
└── [MỚI] anims.pauseAll()/resumeAll() theo s.frozen (C1-01)
```

**Depth tổng**: bg 0 < far 0.05 < near 0.08 < sprite 10 < mark 20 < fx 25 < night tint 26 < light pool 27 < flash/fade 30.

**Nguyên tắc determinism** (kế thừa AC-13/R1): mọi layer mới đều dùng `rtime` đóng băng khi `s.frozen`; particle dùng PRNG seeded — cùng seed + cùng time → cùng output; light pool/night tint/fade tính từ `s.time`/`rtime` thuần hàm; **Phaser anims phải `pauseAll()` khi frozen (C1-01)** — playhead anim chạy theo đồng hồ Phaser, không theo rtime.

## 4. Đặc tả chi tiết

### 4.1. A — Sprite sheet PNG thật (gen-sprites.mjs)

**PNG encoder (trong script)**: chuẩn PNG 8-bit RGBA — signature `89 50 4E 47 0D 0A 1A 0A`, chunks IHDR (width/height, bit depth 8, color type 6), IDAT (mỗi scanline filter byte 0 + RGBA, `zlib.deflateSync`), IEND; CRC32 tự tính. Đã verify bằng magic bytes test.

**Pixel maps** (khai báo mảng chuỗi + palette char→hex trong script; **palette = đúng vendor** — C2-06):
- `CAT` 16×16 logical ×3 scale → 48×48 px/frame. 8 frames:
  - walk0..walk3: chân đổi (pattern khớp vendor: chân trước/trái so le), đuôi giữa;
  - idle: đứng yên mắt mở;
  - blink: mắt nhắm (thay pixel mắt → màu lông);
  - tail0/tail1: đuôi cong lên/xuống (khớp vendor `Math.sin(time*6)*1.5` — 2 mức).
  - Layout: sheet ngang 8×48 = 384×48. Mèo chiếm trọn frame (offset 0,0).
  - Palette vendor: catBody `#f5a623`, catWhite `#ffffff`, catDark `#d98f1d`, catPink `#ffb6c1`, mắt `#1a1a2e`.
- `BUTTERFLY` 16×16 logical ×3 = 48×48/frame ×4 (cánh mở rộng dần frame 0→3). Palette vendor: `#e8c93a`, `#d4a61e`, `#3c2a10`.
- `GHOST` 18×24 logical ×3 = 54×72/frame ×2 (2 trạng thái đuôi lượn — C2-10; bob liên tục qua setY). Palette vendor: thân ghostBlue `#8ec9ff` alpha 0.9, sọ skull `#f4f6f8`, mắt `#0a0a14`, dithering 2×2 checker trên thân.
- `OWNER` 16×16 ×3 = 48×48 ×1 (theo ảnh sinh nhật: tóc nâu bob, áo xanh, mắt nhắm cười). Palette vendor: ownerHair `#7a4a21`, ownerSkin `#ffc9a3`, ownerShirt `#2e86de`.
- `CAKE` 20×16 ×3 = 60×48 ×2 (nến cháy 2 trạng thái — khớp vendor flame flicker). Bố cục trong frame (C1-06): nến y 0..7 logical (khớp vendor y 40..47), thân y 8..14 (vendor y 48..54), đế y 14..16. Palette vendor: cake `#fff6e0`, cakeFrost `#ffc4e3`, candle `#ff6b3d`, flame `#ffd93b`/`#ff8c1c`, cherry `#e03030`.

**sprites.json**: `{ "meta": { "sheet": "cat.png", "frameW": 48, "frameH": 48, "scale": 3 }, "frames": [{ "name": "cat-walk-0", "x": 0, "y": 0 }, ...] }` — cho cả 5 sheet (5 entry meta).

**Tích hợp GameScene**:
- `preload()` (mới — C1-05): `this.load.spritesheet("cat", catUrl, {frameWidth:48, frameHeight:48})`; tương tự `butterfly` (48×48 ×4), `ghost` (54×72 ×2), **`cake` (60×48 ×2 — sheet 120×48, C2v2-16)**; `this.load.image("owner", ownerUrl)`; `this.load.json("sprites", spritesJsonUrl)`.
- `create()`: `this.anims.create(...)`: `cat-walk` (4 frames @8fps loop), `cat-idle-cycle` (frames [idle, blink, idle, idle, tail0, tail1] @4fps loop — 1 anim duy nhất, C2-04), `bfl-flutter` (4 frames @12fps), `ghost-float` (2 frames @3fps), `cake-flame` (2 frames @5fps).
- `update()` — **Quy tắc bất biến frozen (C2v2-17)**: khi `s.frozen` → (a) sprite chưa có anim chạy → KHÔNG gọi `play()` — dùng `setFrame(frame đầu)` cố định; (b) sprite đang play → `this.anims.pauseAll()` chặn playhead; khi hết frozen → `this.anims.resumeAll()` + gọi `play()` theo trạng thái. (pauseAll emit 1 lần — play() sau freeze vẫn chạy nếu không tuân thủ.)
- `renderSprites()`:
  - Mèo: frame 48×48, mèo 16×16 logical chiếm **trọn frame (offset (0,0))** (C1-02); `catImg.setOrigin(0.5, 0.5)` + `setPosition(p.x*3 + 24, p.y*3 + 24)` → phủ screen (p.x*3..p.x*3+48, p.y*3..p.y*3+48) = khớp hitbox cũ; `setFlipX(p.dir < 0)` — lật quanh tâm (origin 0.5) = khớp vendor flip quanh tâm mèo (C1-03); `p.moving` → `play("cat-walk", true)`, idle → `play("cat-idle-cycle", true)`.
  - Bướm: **8×6 logical vẽ ở TÂM frame** (padding 4 ngang × 5 dọc trong 16×16 — C2v2-06) → phủ 24×18 px ≈ vùng vendor cũ (phủ (b.x*3-21..+24, b.y*3-6..+9)); `bfImg.play("bfl-flutter", true)`, anchor 0.5, position `b.x*3, b.y*3`.
  - Ma (HAUNTED, `phase !== "H_INIT" || !dialogue` — mirror vendor): `ghostImg` 54×72 đặt tại `(136*3, 14*3)` = **(408, 42)** (C2-10) — phủ logical (136..154, 14..38) che trọn ghost vendor (139..151, 15..38) ✓; `setAlpha(0.85)` khi darkness>0.5 (C3-01); bob: `ghostImg.setY((14 + Math.sin(rtime*2)) * 3)` (frozen → hằng số); 2 frames = trạng thái đuôi lượn. Visible khi scene HAUNTED.
  - Chủ: GARDEN `phase==="G_INIT" && dialogue` (setMessage set dialogue ✓ — C3-08) → tại (286,52) logical = position (858, 156); BIRTHDAY → (96,42) = (288, 126). Image 48×48 origin (0,0) đặt tại (x*3, y*3) — phủ 16×16 logical che trọn drawOwner 11×16 (thừa 5px trong suốt ✓). 1 frame — **cố ý** (C3-02).
  - Bánh kem (BIRTHDAY): sprite 20×16 logical đặt tại **(70,40)** (C1-06) = (210, 120) — phủ y 40..56 che trọn flames/nến/thân vendor (y 40..54) ✓; pixel map: nến y 0..7 logical, thân y 8..14, đế y 14..16; `play("cake-flame", true)` (nến cháy).
- Khi scene không thuộc → setVisible(false) các sprite này.
- `renderSprites(rtime, time)` — **đổi signature**: nhận `rtime` (đóng băng) cho mọi thứ phụ thuộc time (ghost bob, fx); giữ `time` cho anim state (C2v2-13). Mèo TITLE giữ canvas vendor (drawTitle → drawCat trong vendor sprites.js) — chỉ sprite inGameplay dùng sheet (C2v2-11).
- KHÔNG gọi `drawCat`/`drawButterfly` trong GameScene nữa (AC-3).

### 4.2. B — FX deterministic (src/fx/fx.js)

```js
export function mulberry32(seed)          // PRNG deterministic
export function hashSeed(str)             // seed từ chuỗi cố định
export function fxState(scene, s, time, camX)   // {dust, fireflies, breath, sparks} — camX (px) trừ cho nguồn world (R-02)
export function renderFx(ctx, s, time, camX)     // vẽ particles vào CanvasTexture (screen-space 480×270)
export function renderLightPool(ctx, s, time, camX) // fill dark + radial gradients (screen-space; nguồn world trừ camX)
export function nightTintAlpha(s)         // R-01: guard timers.dark ?? 5*(1-darkness)
export function fadeAlpha(fadeT)          // (fadeT/0.6)² × 0.75
```

- **Bụi (GARDEN, darkness < 0.5)**: 14 hạt quanh cây lớn **(230,40)** (C2v2-14 — vendor thân cây (230,44)) + nhà hiên, vị trí = base + sin(time*speed + i*1.7)*amp, alpha 0.15..0.35 nhấp nháy — deterministic theo time.
- **Đom đóm (GARDEN, darkness ≥ 0.5)**: 10 chấm `#d8ff8a` quanh vườn, alpha = max(0, sin(time*2 + i*2.3)) * 0.8, drift sin chậm — nhấp nháy tự nhiên, deterministic.
- **Hơi thở ma (HAUNTED)**: 8 chấm sương trắng quanh (139,16) vùng ghost, alpha 0.05..0.15, bob sin.
- **Tia lửa lò sưởi (chỉ BIRTHDAY — C1-07: LIVING không có lò sưởi)**: 6 tia quanh (8,40) BIRTHDAY — bay lên rồi tan, alpha giảm theo phase.
- **Light pool** (thay overlay đêm hiện tại trong GameScene renderBg GARDEN; C2-02; **nhận camX px — R-02**):
  - Fill `rgba(8,10,30, α)` với **ambient α theo scene**: GARDEN `α = max(0, (darkness - 0.5) * 0.75)` (chỉ khi darkness ≥ 0.5, tối đa 0.375); HAUNTED α = 0.28; LIVING α = 0.15; BIRTHDAY α = 0.12; HALLWAY α = **0.12 + đuốc tường làm nguồn sáng (R-06)**; scene khác α = 0 (pool inactive). Bỏ ngưỡng 0.15.
  - Radial gradients trong suốt (clear) quanh nguồn sáng (bảng tường minh theo scene — C2-07; **tất cả world-coord trừ `camX` (px)**): GARDEN: player `(p.x*3 - camX, p.y*3)` bán kính 90 (alpha 0.9→0), đèn hiên **(287*3 - camX, 47*3)** bán kính 12 (C3-05), cửa sổ nhà (271*3 - camX, 46*3)/(300*3 - camX, 46*3) bán kính 20; HAUNTED: ma (139*3 - camX, 20*3) bán kính 40, grandfather clock (120*3 - camX, 16*3) bán kính 30; LIVING: sconce (10*3 - camX, 10*3) + (138*3 - camX, 10*3) bán kính 40 (C1-07), đồng hồ tròn (82*3 - camX, 16*3) bán kính 25; BIRTHDAY: lò sưởi (8*3 - camX, 40*3) bán kính 60, nến bánh (80*3 - camX, 44*3) bán kính 25; **HALLWAY: đuốc tường 11 cái `(8 + i*29)*3 - camX, 10*3` bán kính 25 (khớp vendor drawHallway — R-06)**.
- **Đóng băng**: mọi hàm nhận `time` — GameScene truyền `rtime` (đã đóng băng khi frozen) → visual determinism giữ nguyên.

### 4.3. C — Parallax + camera

- **Parallax GARDEN** (chỉ GARDEN; HALLWAY/LIVING/... không có):
  - `farTex` **960×270, redraw mỗi frame** khi scene GARDEN bằng `rtime` (C2-13 — frozen → đứng yên) + theo `s.darkness` (mây tối dần): 3 đám mây lớn style ảnh title (trắng xốp + đáy xanh nhạt, alpha 0.5-0.7) tại **`x = [60, 260, 460] + sin(rtime*0.05)*20`, y = 24/56/88** (C2v2-05 — nằm trong cửa sổ far [0..600] px), image `setScrollFactor(0.25)` origin (0,0) position (0,0).
  - `nearTex` **1200×270** (C2-03 — camX max 480px → cửa sổ near max [552, 1032] < 1200 ✓): 6 bụi cỏ/hoa cao lặp mỗi 200px (y 76..90 logical — vùng cỏ), `setScrollFactor(1.15)` → dịch nhanh hơn bg → chiều sâu.
  - Depth: bg(0) < far(0.05) < near(0.08) < sprite(10). Mây/near vẽ đè lên bg (mây đè sky vendor — chấp nhận, tạo 2 tầng mây; near đè cỏ — hòa màu).
- **Camera shake**: trong update, so `s.scareActive` với `this._prevScare`; khi tăng → `this.cameras.main.shake(300, 0.012)`; guard: không shake khi `s.frozen`.
- **Zoom nhẹ**: khi `scareActive === 5` → `this.cameras.main.zoomTo(1.04, 250)`; khi hết scare → `zoomTo(1, 250)`. Guard frozen (C2-12: tween 250ms — test chờ ≥300ms).

### 4.4. D — Transition mượt

- **Fade chuyển cảnh**: `fadeT` khởi tạo 0.6 (tăng từ 0.35); alpha = `(fadeT/0.6)^2 * 0.75` (ease-out) thay cho linear `(fadeT/0.35)*0.6`.
- **Night tint** (C2-01, C2v2-02, **R-01 guard**): **chỉ active khi `s.scene === "GARDEN"`** (mirror darkness của GARDEN). Core `darkness = clamp(1 - timers.dark/DARK_RAMP, 0, 1)` với DARK_RAMP=5.0 (verify core.js:27/436) → darkness ≥ 0.5 khi `timers.dark ≤ 2.5`. Tint rect xanh đêm `rgba(10,14,40, α)` với `α = clamp(0, (2.5 - t) / 1.5, 1) * 0.18` trong đó **`t = s.timers.dark ?? 5 * (1 - (s.darkness || 0))`** (guard NaN khi timers.dark undefined — debug setPhase không set timers; KHÔNG dùng `|| 0` đơn thuần) — lerp mượt 1.5s khi timers.dark giảm từ 2.5 → 1.0 (deterministic theo s.timers.dark; frozen → đóng băng). Test số cụ thể: timers.dark=2.5 → α=0; =1.0 → α=0.18; **undefined + darkness=1 → α=0.18; undefined + darkness=0 → α=0**.

## 5. Input / Output

- **Input**: `games/yuniebel-phaser/` hiện tại + `imagedata.md` (tham khảo visual) + `baseimg/*.png` (nguồn gốc).
- **Output**:
  - `tools/gen-sprites.mjs` (mới)
  - `src/assets/{cat,butterfly,ghost,owner,cake}.png` + `sprites.json` (mới, git-tracked)
  - `src/fx/fx.js` (mới)
  - `src/scenes/GameScene.js` (sửa), `src/main.js` (sửa — load assets)
  - `test/fx.test.js`, `test/sprite-sheet.test.js` (mới), `test/visual.spec.js` (mở rộng)
  - `aios/progress/tasks/TASK-082/*` (8 file hard gate)

## 6. Tiêu chí chấp nhận (Acceptance Criteria)

| # | AC | Cách verify |
|---|----|-------------|
| AC-1 | `tools/gen-sprites.mjs` chạy deterministic: chạy 2 lần → SHA256 PNG/JSON giống hệt; 5 PNG đúng signature + IHDR kích thước; sprites.json đủ frames (cat 8, bfly 4, ghost 2, owner 1, cake 2) | vitest `sprite-sheet.test.js` (fs đọc file thật) + chạy script 2 lần diff |
| AC-2 | PNG sprite có pixel alpha hợp lệ (không rỗng, có vùng trong suốt cho sheet động) | vitest đọc IHDR + scan pixels (qua PNG decode trong test — dùng zlib.inflateSync) |
| AC-3 | Mèo hiển thị bằng sprite sheet (không còn `drawCat`/`drawButterfly` trong GameScene) — walk 4 frames + idle-cycle (blink + tail) | grep GameScene + **C2v2-03**: giữ phím `d` ≥300ms (mèo walk) → 2 shot cách 150ms khác nhau (`Buffer.compare ≠ 0`) + evaluate đọc `catImg.anims.currentFrame.textureFrame` ở 2 mốc → frame khác; frozen shot byte-identical (determinism) |
| AC-4 | Bướm vỗ cánh 4 frames (`bfl-flutter` anim tồn tại) | Playwright shot + anims check qua `__phaserGame.scene.getScene("Game").anims` |
| AC-5 | Ma float 2 frames phủ đúng vị trí HAUNTED (136,14) — che trọn ghost bg | Playwright shot haunted-ghost2.png — verify manual COMPARISON (C3-03) |
| AC-6 | Chủ (GARDEN G_INIT + BIRTHDAY) + bánh kem (BIRTHDAY (70,40) — không lộ nến vendor vùng y 40..47) | Playwright shot birthday2.png + garden-day.png — verify manual COMPARISON |
| AC-7 | FX deterministic: `fxState(same, t)` → cùng output; không dùng `Math.random` trong fx.js | vitest `fx.test.js` + grep |
| AC-8 | Bụi bay hiển thị GARDEN ngày; đom đóm hiển thị GARDEN đêm (darkness≥0.5); hơi thở ma HAUNTED; tia lửa lò sưởi BIRTHDAY (LIVING không có lò sưởi — C1-07/C2v2-01) | vitest fxState đúng theo scene/darkness + Playwright shot garden-day/garden-night/haunted/birthday/living-fx có vùng pixel hạt sáng mới |
| AC-9 | Light pool thay overlay phẳng: GARDEN darkness ≥ 0.5 → quanh player sáng hơn góc màn (probe tự động — C3-03/C2v2-07) | Playwright shot garden-night (`setPlayer(133,57)` — giữa màn): crop 40×40 quanh player (clamp về canvas) vs crop 40×40 góc trái màn (cùng frame) → chênh brightness trung bình (`0.299R+0.587G+0.114B`, decode PNG qua zlib.inflateSync) ≥ 10/255 |
| AC-10 | Parallax: farTex scrollFactor 0.25, nearTex 1.15 tồn tại; khi camera scroll → far dịch 0.25×, near dịch 1.15× | Playwright: `window.__phaserGame.scene.getScene("Game").cameras.main` + đọc scrollFactor/vị trí image qua page.evaluate (C2-12) |
| AC-11 | Camera shake khi scare tăng + zoom ≈1.04 khi scare 5 (tolerance ±0.01) — không khi frozen | Playwright **thứ tự bắt buộc (R-03)**: (1) setScareZone(5) chưa freeze → (2) chờ ~150ms → assert `cam.shakeEffect.isRunning === true` (Phaser 4 KHÔNG có shakeDuration) → (3) chờ thêm ~250ms (tổng ≥400ms > 300 shake + 250 zoom) → assert `zoom ≈ 1.04 ±0.01` → (4) freeze(true) → (5) shot ×2 byte-compare; frozen → không đổi |
| AC-12 | Fade transition ease-out: fadeT 0.6, alpha công thức t² | vitest transition math (hàm thuần export) |
| AC-13 | Night tint lerp: darkness≥0.5 → alpha tăng 0→0.18 trong 1.5s theo s.time | vitest math |
| AC-14 | **Regression**: core 27/27, smoke 3/3, e2e 8/8, visual 19/19 cũ vẫn PASS — cơ chế shot cũ giữ nguyên (non-empty + byte-compare frozen); KHÔNG dùng `toHaveScreenshot` thiếu ref (fail-closed TASK-079 — C2-09) | chạy `npm test` — total ≥ 56 + test mới; COMPARISON.md ghi chú ảnh thay đổi do feature mới |
| AC-15 | **Vendor byte-identical**: SHA256 của 4 vendor files = baseline `test/vendor-hashes.json` (tính từ TASK-081 — C3-06) | vitest đọc hash file thật |
| AC-16 | Determinism visual: 2 screenshot cách 500ms (frozen) giống hệt với light pool/fx/parallax + anims pauseAll (C1-01) | visual.spec.js cơ chế cũ + shots mới |
| AC-17 | Không thêm dependency npm; `npm run build` PASS; **dist/assets chứa 5 PNG + JSON** (C1-04 — import module) | chạy build + verify dist; 1 shot Playwright với `vite preview` (prod build) |
| AC-18 | Không đụng `games/yuniebel/` (vanilla untouched) | `git diff --quiet HEAD -- games/yuniebel` = 0 |
| AC-19 | **Anim đứng yên khi frozen** (C1-01/C2v2-17): frozen → không gọi `play()` (setFrame cố định) + pauseAll — 2 shot frozen cách 500ms giống hệt byte kể cả khi mèo đang walk; **ca freeze-ngay-sau-setPhase (H_INIT) → 2 shot vẫn byte-identical** | Playwright shot frozen so khớp |
| AC-20 | **Flip khớp vị trí** (C1-03/R-04): dir=1 và dir=-1 cùng tọa độ p.x → mèo phủ cùng vùng screen (origin 0.5) | Playwright: setPlayer + set dir → 2 shot crop quanh mèo → scan **bounding box** pixels màu cam #f5a623 (min/max x,y) → 2 bbox nằm cùng vùng (±4px) — KHÔNG so ảnh raw (bị mirror) |
| AC-21 | **Prod build có sprite** (C1-04): sau `vite build`, `dist/assets/` chứa `cat.png`/`butterfly.png`/`ghost.png`/`owner.png`/`cake.png` + `sprites.json`; `vite preview` chụp 1 shot thành công | chạy build + `vite preview` + Playwright |
| AC-22 | **Mây parallax hiển thị** (C2v2-05): shot garden-day có vùng mây mới khác bg cũ | Playwright shot + COMPARISON manual |
| AC-23 | **Night tint không NaN** (R-01): timers.dark undefined + darkness=1 → α=0.18; undefined + darkness=0 → α=0 | vitest fx.test.js |

## 7. Rủi ro & giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|--------|-----|------------|
| Sprite sheet PNG encode sai (IDAT/CRC) | Cao | Test magic bytes + IHDR + inflate scanline trong vitest; script chạy cục bộ trước khi commit |
| Sprite phủ lệch vị trí so với bg vendor (ghost/owner/cake) | Trung | Tọa độ đọc trực tiếp từ sprites.js (139,16 / 96,42 / 70,48); sprite ≥ bản cũ; shot Playwright đối chiếu COMPARISON |
| Phaser Animations API khác biệt Phaser 4 vs 3 | Trung | Dùng API cơ bản (anims.create/play/setFlipX) ổn định cả 3/4; smoke test không boot — verify qua Playwright thật |
| CanvasTexture + setScrollFactor trong Phaser 4 | Trung | Dùng image + setScrollFactor — API ổn định; test AC-10 qua debug hook |
| Particles/light pool phá determinism (frozen) | Cao | Mọi thứ thuần hàm theo time/rtime; PRNG seeded; visual test so 2 shot |
| Performance re-render mỗi frame (đã có) | Thấp | Layer mới đều CanvasTexture nhỏ; không thêm draw call lớn |
| Regression 56/56 vỡ | Cao | Chạy full suite trước khi đánh dấu done; vendor diff check |

## 8. Test plan

1. **vitest** (jsdom, không boot Phaser): `sprite-sheet.test.js` (AC-1/2/15/21 — đọc file thật, decode PNG qua zlib.inflateSync, so SHA256 committed + baseline vendor-hashes.json), `fx.test.js` (AC-7/12/13 + PRNG seeded), core/smoke cũ (AC-14).
2. **Playwright** (trình duyệt thật): e2e cũ 8 (AC-14) + visual cũ 19 (AC-14/16; **bump chờ 500 → 700ms sau btn-start** — R-07.1) + shots mới: `cat-walk.png` (**test riêng, KHÔNG byte-compare — phải khác giữa 2 mốc 150ms khi giữ phím d**, C2v2-03/C2v2-15), `cat-idle-cycle.png` (frozen determinism, AC-19), `garden-night-fx.png` (đom đóm + light pool probe AC-9 — probe qua `page.evaluate` vẽ WebGL canvas vào 2D offscreen `getImageData`, R-07.6), `haunted-ghost2.png` (ghost sprite AC-5 + freeze-ngay AC-19), `birthday2.png` (owner + cake sprite AC-6), `living-fx.png` (sconce light pool), `hallway-scare5-zoom.png` (zoom AC-11 theo thứ tự R-03) — 6 shots còn lại: non-empty + byte-compare 2 lần cách 500ms (AC-16) + lưu COMPARISON update (ghi chú: walk 4f, owner 1 frame không vẫy tay, bướm 24×18, hallway pool — C2v2-09/10/R-07.5/R-06).
3. **Prod build**: `npm run build` → verify `dist/assets/` có 5 PNG + JSON (AC-17/21) + `vite preview` 1 shot (AC-21).
4. **Manual verify**: chạy `npm run dev` → chơi thử nhanh qua Playwright không hook (title→sinh nhật, đã có e2e 45s).

## 9. Milestone/Plan liên quan

- Kế thừa: TASK-081 (scaffold Phaser 4), TASK-078 (game + brief visuals), TASK-080 (sprite skill).
- Không phá INV-001..034 (game nằm ngoài backend AIOS).
- Đề xuất M11 (proposal doc) R1/R3/R4 có liên quan phương pháp (determinism, golden-master) — áp dụng tinh thần: test fail-closed, ảnh ref có thật.
