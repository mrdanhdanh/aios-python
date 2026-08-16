# TASK-082 — Critique vòng 2 + Resolution

> **Date**: 2026-08-16 | **Critic**: AIOS critic agent | **Trạng thái**: ĐÃ RESOLVE (3 P1 + 7 P2 + 6 P3)
> Spec v2 → **v3** (sửa theo resolution bên dưới). Đủ 2 vòng critique đã resolve → qua tasks + review.

## Đối chiếu vòng 1 (28/28)

- **25/28 ✓** hoàn toàn (critic verify trực tiếp trên source Phaser 4.2.1 + code vendor).
- **3/28 ⚠️** áp dụng một phần → đã tạo vấn đề mới vòng 2: C1-07 (AC-8 sót) → C2v2-01; C2-05 (cơ chế test) → C2v2-03; C2-13 (công thức mây) → C2v2-05.

## Vấn đề vòng 2 + Resolution

### P1

**C2v2-05 — Mây farTex nằm ngoài màn hình (`x = -160±20`) (P1)**
- Cửa sổ hiển thị far với scrollFactor 0.25 + scrollX 0..480 là `[0..600]` px.
- **RESOLVE**: 3 đám mây tại `x = [60, 260, 460] + sin(rtime*0.05)*20`, y lần lượt 24/56/88; farTex image origin (0,0) position (0,0); thêm AC-22: shot garden-day có vùng mây khác bg cũ (COMPARISON).

**C2v2-16 — Cake: `load.image` mâu thuẫn anim `cake-flame` 2 frames (P1)**
- **RESOLVE**: `this.load.spritesheet("cake", cakeUrl, {frameWidth: 60, frameHeight: 48})` (sheet 120×48, 2 frames) — thống nhất IN #2 + AC-1 (2 frames cake).

**C2v2-17 — `play()` lần đầu SAU freeze vẫn chạy playhead (P1)**
- pauseAll emit 1 lần; play() sau freeze → anim không bị chặn → phá AC-16 (shot haunted-ghost cũ khi ghost mới xuất hiện sau freeze).
- **RESOLVE — Quy tắc bất biến**: khi `s.frozen`:
  - Sprite **chưa có anim chạy** → KHÔNG gọi `play()` — dùng `setFrame(frame đầu)` cố định;
  - Sprite **đang play** → pauseAll() đã chặn playhead — giữ nguyên;
  - Khi hết frozen → `resumeAll()` + gọi `play()` theo trạng thái.
  - Ghi quy tắc vào §3 + §4.1; AC-19 mở rộng: test `setPhase("H_INIT")` + freeze NGAY (không chờ) → 2 shot byte-identical.

### P2

**C2v2-01 — AC-8 sót "tia lửa LIVING" (P2)** → **RESOLVE**: AC-8: "tia lửa lò sưởi hiển thị BIRTHDAY (LIVING không có lò sưởi — C1-07)".
**C2v2-02 — Night tint chưa giới hạn scene (P2)** → **RESOLVE**: "night tint chỉ active khi `s.scene === "GARDEN"`"; AC-13 ghi rõ điều kiện scene.
**C2v2-03 — AC-3 cơ chế test không xác định (P2)** → **RESOLVE**: (1) giữ phím `d` ≥300ms (mèo walk) → 2 shot cách 150ms khác nhau + qua evaluate đọc `catImg.anims.currentFrame.textureFrame` ở 2 mốc → frame khác; (2) frozen shot byte-identical.
**C2v2-04 — AC-11 chờ 300ms → shakeDuration có thể = 0 (P2)** → **RESOLVE**: assert shake sau ~150ms (giữa cơn shake 300ms); zoom giữ chờ ≥300ms (> tween 250ms).
**C2v2-06 — Kích thước bướm trong frame (P2)** → **RESOLVE**: bướm **8×6 logical vẽ ở TÂM frame** (padding 4 ngang × 5 dọc) → phủ 24×18 px ≈ vùng cũ (vendor phủ (b.x*3-21..+24, b.y*3-6..+9)); ghi COMPARISON note nếu lệch nhỏ.
**C2v2-07 — AC-9 probe (P2)** → **RESOLVE**: `setPlayer(133, 57)` (giữa màn, khớp shot garden-night cũ); crop clamp về canvas; brightness trung bình = `0.299R + 0.587G + 0.114B`; decode PNG trong test (kỹ thuật zlib.inflateSync sẵn cho AC-2).
**C2v2-15 — §8 byte-compare mâu thuẫn cat-walk (P2)** → **RESOLVE**: §8 tách rõ: `cat-walk` test riêng (không byte-compare — phải khác, C2v2-03); 6 shots còn lại byte-compare frozen.

### P3 (ghi chú — áp dụng)

**C2v2-08** — Zoom 1.04 lệch pool ≤ ~10px — chấp nhận (bán kính pool 90 che). ✓
**C2v2-09** — Owner vendor vẫy tay 2 frames — sprite 1 frame cố ý; ghi COMPARISON.md. ✓
**C2v2-10** — Walk 4 frames @8fps = 2 chu kỳ/s vs vendor 2 frames 4 chu kỳ/s — feature A cố ý; COMPARISON note. ✓
**C2v2-11** — Mèo TITLE giữ canvas vendor (drawTitle → drawCat trong vendor sprites.js) — spec ghi rõ: "chỉ sprite inGameplay; AC-3 grep giới hạn GameScene". ✓
**C2v2-13** — `renderSprites` hiện nhận `time` (đồng hồ Phaser) → đổi signature truyền `rtime` (ghost bob/fx). ✓
**C2v2-14** — Bụi quanh cây lớn: vendor thân cây (230,44) → dịch bụi về (230,40) (decorative). ✓

## Kết luận

- Vòng 1: 28/28 resolved. Vòng 2: 3 P1 + 7 P2 + 6 P3 — **TẤT CẢ RESOLVED** (spec v3).
- **Đủ 2 vòng critique độc lập, không còn P1/P2** → đủ điều kiện sang tasks + review + implement.
