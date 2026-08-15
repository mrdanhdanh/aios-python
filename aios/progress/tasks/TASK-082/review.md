# TASK-082 — Review trước implement

> **Date**: 2026-08-16 | **Reviewer**: AIOS reviewer agent | **Kết luận**: CHANGES REQUESTED → **RESOLVED (R-01..R-07)**
> Spec v3 → **v3.1** (sửa theo resolution). Sau khi resolve → đủ điều kiện implement.

## Đánh giá chung

Spec v3 chắc (2 critique đã resolve, tọa độ nguồn sáng/API Phaser 4.2.1 đều verify trực tiếp trên code). Phát hiện tích cực: `setPhase` debug không trigger fade (prevScene capture đầu update) → regression 19 shot cũ gần bằng 0.

## Vấn đề + Resolution

### P1 — Bắt buộc sửa trước implement

**R-01 — `nightTintAlpha` ra NaN khi `timers.dark` undefined (P1)**
- Bằng chứng: `resetGame()` → `timers: {}`; `setPhase("G_DARK")` không set timers.dark → `(2.5 - undefined)/1.5` = NaN → clamp(NaN) = NaN → alpha hỏng.
- **RESOLVE**: guard `const t = s.timers.dark ?? 5 * (1 - (s.darkness || 0))` (tương đương toán học: darkness = 1 - timers.dark/5); KHÔNG dùng `|| 0` đơn thuần. Cập nhật spec §4.4 + T4.5 + test case `timers.dark=undefined → α theo darkness`.

**R-02 — FX/light pool thiếu `camX` — nguồn sáng world-coord trên layer screen-space (P1)**
- Bằng chứng: bụi (230,40), đèn hiên (287,47), cửa sổ (271/300,46) là world coords; layer screen-space 480×270 → shot garden-day camX=30 → bụi x=690 → screen 600 > 480 → AC-8 fail theo shot.
- **RESOLVE**: thêm tham số `camX` (px) vào `fxState(scene, s, time, camX)` / `renderFx(ctx, s, time, camX)` / `renderLightPool(ctx, s, time, camX)`; mọi nguồn world trừ `camX`; player trừ camX như cũ. Cập nhật T4.2/T4.4/T5.3.

### P2 — Nên sửa cùng lúc

**R-03 — Thứ tự shake/zoom/freeze + `shakeDuration` không tồn tại (P2)**
- Phaser 4.2.1: `cam.shakeEffect.isRunning/duration`, `cam.zoomEffect` — KHÔNG có `shakeDuration`.
- Shake dùng Math.random nội bộ → freeze giữa cơn shake → byte-compare vỡ.
- **RESOLVE**: Thứ tự bắt buộc trong test: (1) `setScareZone(5)` (chưa freeze) → (2) chờ ~150ms → assert `shakeEffect.isRunning === true` → (3) chờ thêm ~250ms (tổng ≥400ms > 300 shake + 250 zoom) → assert `zoom ≈ 1.04 ±0.01` → (4) `freeze(true)` → (5) shot ×2 byte-compare. Ghi vào T10 + AC-11.

**R-04 — AC-20: so crop raw sai vì mirror (P2)**
- **RESOLVE**: assert bằng **bounding box**: scan pixels màu mèo (cam #f5a623) trong crop → min/max x,y nằm cùng vùng giữa dir=1 và dir=-1 (không so ảnh raw).

**R-05 — tasks.md thiếu 3 đầu việc (P2)**
- **RESOLVE**: thêm (1) AC-20 flip test vào T10; (2) COMPARISON.md update (walk 4f, owner 1 frame, bướm 24×18, hallway pool) vào T13; (3) AC-18 (`git diff --quiet HEAD -- games/yuniebel`) vào T11/T14.

**R-06 — HALLWAY pool α=0.18 không có nguồn sáng (P2)**
- **RESOLVE**: HALLWAY α = **0.12** + thêm nguồn sáng **đuốc tường 11 cái** `(8 + i*29, 10)` bán kính 25 (khớp vendor drawHallway) → giữ không khí tối nhưng 5 kiểu hù vẫn nổi; COMPARISON note.

### P3 — Ghi nhận (áp dụng)

**R-07** (1) visual.spec chờ 500 → **700ms** sau btn-start (fade 0.6s, veil dư ~2%); (2) `_prevScare` khởi tạo **0** trong create; (3) thêm `pretest:visual`; (4) pixel map mèo dịch xuống **1px** (tai vendor y=-1 không cắt); (5) bướm vùng 24×18 — COMPARISON note; (6) AC-9 probe dùng `page.evaluate` → vẽ WebGL canvas vào 2D offscreen → `getImageData` (đơn giản hơn decode PNG); (7) `play(key, true, 0, true)` với `ignoreIfPlaying=true` khi resume sau freeze; (8) owner vendor ~9×16 (không 11×16) — sprite 16×16 vẫn che trọn.

## Kết luận

- 2 P1 + 4 P2 + 8 P3 ghi nhận — **TẤT CẢ RESOLVED** (spec v3.1 + tasks.md cập nhật).
- **APPROVED để implement** — thứ tự: P0 assets → P1 fx → P2 tích hợp → P3 test → P4 đóng gate.
