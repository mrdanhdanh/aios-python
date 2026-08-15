# TASK-082 — Critique vòng 1 + Resolution

> **Date**: 2026-08-16 | **Critic**: AIOS critic agent | **Trạng thái**: ĐÃ RESOLVE (28/28)
> Sau critique vòng 1 → spec v1 → **v2** (sửa theo resolution bên dưới).

## Tổng quan critic

Spec có khung chuẩn, phạm vi IN/OUT rõ, kế thừa đúng bài học TASK-079/081 (determinism freeze, vendor byte-identical). **7 P1 / 13 P2 / 8 P3** — trong đó 5 P1 là lỗi số liệu/API verify được ngay từ code hiện có.

## Các vấn đề + Resolution

### P1 — Bắt buộc resolve trước implement

**C1-01 — Phaser Animations không đóng băng khi `s.frozen` → phá determinism (P1)**
- Vấn đề: playhead anim chạy theo đồng hồ Phaser, không theo `rtime` → shot frozen vỡ.
- **RESOLVE**: Thêm vào GameScene: khi `s.frozen` → `this.anims.pauseAll()` (AnimationManager#pauseAll tồn tại trong Phaser 4.2.1); khi hết frozen → `resumeAll()`. Xử lý cả trường hợp freeze khi anim chưa play. Thêm **AC-19**: "khi s.frozen, mọi anim đứng yên — 2 shot frozen cách 500ms giống hệt byte".

**C1-02 — Tọa độ mèo mâu thuẫn nội tại (P1)**
- Vấn đề: "mèo ở offset (0,0)" + "position p.x*3-42" → lệch 14 ngang/8 dọc so với hitbox cũ.
- **RESOLVE**: Chọn phương án (a): sprite mèo vẽ tại **offset (0,0) của frame 48×48** (16×16 logical), image **`setOrigin(0.5, 0.5)`, position `(p.x*3 + 24, p.y*3 + 24)`** → mèo phủ screen (p.x*3 .. p.x*3+48, p.y*3 .. p.y*3+48) = khớp hitbox cũ (chứng minh: cũ mèo phủ (p.x*3, p.y*3)..(p.x*3+48, p.y*3+48)).

**C1-03 — `setFlipX` với anchor (0,0) lật quanh mép frame → nhảy 48px (P1)**
- Vấn đề: vendor flip quanh tâm mèo; Phaser flip quanh origin.
- **RESOLVE**: Dùng `setOrigin(0.5, 0.5)` (tâm frame = tâm mèo vì mèo chiếm trọn frame 16×16) + `setFlipX(p.dir < 0)` → lật quanh tâm mèo = khớp vendor. Thêm shot kiểm chứng dir=1 và dir=-1 khớp vị trí cũ (AC-20).

**C1-04 — Load PNG/JSON bằng URL runtime → vỡ production build (P1)**
- Vấn đề: Vite chỉ emit asset được import trong JS; `vite build` → dist thiếu sprite.
- **RESOLVE**: Import làm module: `import catUrl from "../assets/cat.png"` (vite emit + hash), `import spritesJson from "../assets/sprites.json"`; thêm **AC-21**: sau `vite build`, verify `dist/assets/` chứa 5 PNG + JSON; chạy 1 shot Playwright với `vite preview` (prod build).

**C1-05 — `textures.addSpriteSheet` không nhận URL trong Phaser 4.2.1 (P1)**
- Vấn đề: source phải là HTMLImageElement/Texture, không phải URL.
- **RESOLVE**: Thêm `preload()` vào GameScene: `this.load.spritesheet("cat", catUrl, {frameWidth:48, frameHeight:48})` (FileTypesManager.register('spritesheet') tồn tại trong 4.2.1); `this.load.image` cho owner/cake/ghost; `this.load.json("sprites", spritesJsonUrl)` — hoặc dùng object import trực tiếp.

**C1-06 — Bánh kem phủ sai: (70,48) không che nến/lửa vendor y 40..47 (P1)**
- Vấn đề: flame y40..42, nến y42..47, frost y46..49, thân y48..54 — sprite tại (70,48) để lộ nến.
- **RESOLVE**: Sprite cake **20×16 logical đặt tại (70,40)** → phủ y 40..56 che trọn; pixel map cake: nến ở y 0..7 logical (tương ứng vendor y 40..47), thân y 8..14 (vendor y 48..54), đế y 14..16. AC-6 kiểm chứng shot birthday2: vùng y 40..47 (pixel 120..141 screen) không còn pixel lửa vendor riêng lẻ (chấp nhận verify manual COMPARISON).

**C1-07 — LIVING không có lò sưởi — sparks/light pool "LIVING (20,45)" hư cấu (P1)**
- Vấn đề: drawLiving chỉ có sofa/sconce/bàn trà/đồng hồ; (20,45) là sofa.
- **RESOLVE**: Bỏ LIVING khỏi sparks; light pool LIVING dùng **2 đèn sconce (10,10) và (138,10)**, bán kính 40; BIRTHDAY giữ lò sưởi (8,40) bán kính 60 + nến bánh.

### P2 — Nên resolve trước implement

**C2-01 — `G_DARK_start` chưa định nghĩa (P2)**
- **RESOLVE**: `darkness = clamp(1 - timers.dark/DARK_RAMP, 0, 1)` với DARK_RAMP=5.0 (verify core.js dòng 27/436) → darkness ≥ 0.5 khi `timers.dark ≤ 2.5`. Night tint: `α = clamp(0, (2.5 - s.timers.dark) / 1.5, 1) * 0.18` (timers.dark giảm từ 5→0; tint tăng khi darkness ≥ 0.5, lerp 1.5s). Test dùng số cụ thể: timers.dark=2.5 → α=0; =1.0 → α=0.18.

**C2-02 — Light pool ngưỡng mâu thuẫn + nguồn sáng ngoài GARDEN không bao giờ chạy (P2)**
- **RESOLVE**: Bỏ ngưỡng 0.15; định nghĩa **ambient darkness theo scene**: GARDEN: `α = max(0, (darkness-0.5)*0.75)` (chỉ khi darkness≥0.5); HAUNTED: α cố định 0.28; LIVING: α 0.15; BIRTHDAY: α 0.12; HALLWAY: α 0.18; các scene khác α=0. Light pool active khi α > 0. Nguồn sáng (bảng tường minh theo scene): GARDEN player + đèn hiên (287,47) + cửa sổ nhà (271,46)/(300,46); HAUNTED ma (139,20) + đồng hồ (120,16); LIVING sconce (10,10)/(138,10); BIRTHDAY lò sưởi (8,40) + nến bánh (80,44).

**C2-03 — nearTex 960px không đủ scrollFactor 1.15 (P2)**
- **RESOLVE**: GARDEN camX max = 320-160 = 160 logical = 480px screen. Cửa sổ near max = [1.15×480, 1.15×480+480] = [552, 1032]. **nearTex 1200×270**, cỏ/hoa lặp mỗi 200px (6 cụm), anchor (0,0), scrollFactor 1.15.

**C2-04 — Không thể chạy 2 anim song song trên 1 sprite (P2)**
- **RESOLVE**: 1 anim duy nhất `cat-idle-cycle`: frames [idle, blink, idle, idle, tail0, tail1] @4fps loop (2s/cycle). Bỏ blink/tail riêng.

**C2-05 — AC-3 phương pháp verify tự mâu thuẫn (P2)**
- **RESOLVE**: AC-3 verify: (1) shot **không freeze** tại t1 và t1+150ms → `Buffer.compare ≠ 0` (anim chạy — walk frame đổi); (2) shot frozen so khớp byte (determinism). Cộng thêm grep: GameScene không còn gọi `drawCat`/`drawButterfly`.

**C2-06 — Palette sprite không khớp vendor (P2)**
- **RESOLVE**: Dùng đúng palette vendor (verify sprites.js dòng 27-28): catBody `#f5a623`, catWhite `#ffffff`, catDark `#d98f1d`, catPink `#ffb6c1`; ownerHair `#7a4a21`, ownerShirt `#2e86de`, ownerSkin `#ffc9a3`; cake `#fff6e0`, cakeFrost `#ffc4e3`, candle `#ff6b3d`, flame `#ffd93b`; ghostBlue `#8ec9ff`, skull `#f4f6f8`, eye `#0a0a14`. Đối chiếu COMPARISON với ảnh cũ + baseimg.

**C2-07 — "Đồng hồ (120,16)" trộn scene (P2)**
- **RESOLVE**: Ghi scene tường minh: HAUNTED grandfather clock (120,16) bán kính 30; LIVING đồng hồ tròn (82,16) bán kính 25.

**C2-08 — Depth ordering chưa khai báo (P2)**
- **RESOLVE**: bg 0 < far 0.05 < near 0.08 < sprite 10 < mark 20 < fx 25 < night tint 26 < light pool 27 < flash/fade 30. Cả fx/tint/pool đều `setScrollFactor(0)` (screen-space). Pool TRÊN tint → vùng quanh nguồn sáng sáng hơn nền tối (AC-9).

**C2-09 — AC-14 cơ chế + COMPARISON (P2)**
- **RESOLVE**: Mọi shot (cũ + mới) giữ cơ chế: non-empty (length>1000) + byte-compare 2 shot frozen cách 500ms. KHÔNG dùng `toHaveScreenshot` thiếu ref (bài học TASK-079 fail-closed). Ghi chú COMPARISON.md: các shot đổi hình do feature mới (garden-day, garden-night, living, kitchen-blood, haunted, birthday, hallway-scare1..5, end, gameover).

**C2-10 — Vị trí ghost dấu "?" (P2)**
- **RESOLVE**: Sprite ghost **54×72 (18×24 logical)** đặt tại **`(136*3, 14*3)` = (408, 42)** — phủ logical (136..154, 14..38) che trọn ghost vendor (139,16)+(12×20 → 139..151, 16..36) ✓. 2 frames thể hiện trạng thái đuôi lượn; bob liên tục qua `ghostImg.setY((14 + Math.sin(rtime*2)) * 3)` (frozen → hằng số). `setAlpha(0.85)` khi darkness>0.5 (C3-01).

**C2-11 — gen-sprites chưa có entry script + thứ tự chạy (P2)**
- **RESOLVE**: Thêm npm scripts: `"gen:sprites": "node tools/gen-sprites.mjs"` + `"pretest": "node tools/gen-sprites.mjs"` (npm chạy pretest trước test → assets luôn mới). AC-1: chạy gen 2 lần → SHA256 PNG/JSON giống hệt + so với file committed (test fail nếu lệch).

**C2-12 — Camera access + tween bất đồng bộ (P2)**
- **RESOLVE**: AC-10/11 truy cập `window.__phaserGame.scene.getScene("Game").cameras.main` (đã verify main.js expose `window.__phaserGame`); sau `setScareZone` chờ ≥ 300ms rồi assert (zoomTo 250ms / shake 300ms) với tolerance zoom ±0.01.

**C2-13 — farTex kích thước + redraw policy (P2)**
- **RESOLVE**: farTex **960×270**, redraw mỗi frame khi scene GARDEN bằng `rtime` (frozen → đứng yên) + theo `s.darkness` (mây tối dần); 3 đám mây lớn style ảnh title (trắng xốp + đáy xanh nhạt) drift `sin(rtime*0.05)*20`; scrollFactor 0.25.

### P3 — Góp ý (đều áp dụng)

**C3-01** — Ghost `setAlpha(0.85)` khi darkness > 0.5 (khớp vendor). ✓
**C3-02** — Owner 1 frame — ghi rõ cố ý (giữ nguyên phong cách, không phá ảnh tham khảo; vendor owner là nhân vật phụ). ✓
**C3-03** — AC-5/AC-8 verify manual (COMPARISON); AC-9 probe tự động định lượng: crop 40×40 quanh player vs crop 40×40 góc trái màn (cùng frame), chênh brightness trung bình ≥ 10/255. ✓
**C3-04** — PNG encoder `zlib.deflateSync(buf, {level: 9})`. ✓
**C3-05** — Đèn hiên light pool dùng (287,47) bán kính 12 (đúng vendor). ✓
**C3-06** — Hash chuẩn TASK-081: lưu trong `test/vendor-hashes.json` (4 SHA256 baseline tính từ vendor hiện tại = bản TASK-081 đã verify AC-16); test so khớp. ✓
**C3-07** — Map sprite → ảnh tham khảo: cat/owner/birthday → ảnh 2 (sinh nhật) + ảnh 3 (phòng khách); ghost/cake → ảnh 2; hallway scare → ảnh 1 (5 kiểu hù); butterfly/title → ảnh 6 (title START). Ghi vào spec §1. ✓
**C3-08** — Đã verify: `debug.setMessage` set `s.dialogue` (core.js dòng 643-647) → owner GARDEN hiện khi `setPhase("G_INIT")` + `setMessage`. ✓

## Kết luận

- Tổng: **7 P1, 13 P2, 8 P3 — 28/28 RESOLVED** (spec v2).
- Spec v2 đủ điều kiện sang **critique vòng 2**.
