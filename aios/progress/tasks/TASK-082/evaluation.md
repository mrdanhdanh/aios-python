# TASK-082 — Evaluation

> **Date**: 2026-08-16 | **Kết luận**: ✅ **TASK-082 DONE** — 23/23 AC ĐẠT, 88/88 test PASS

## 1. Đối chiếu Acceptance Criteria (23 AC)

| # | AC | Kết quả | Bằng chứng |
|---|----|---------|------------|
| AC-1 | gen-sprites deterministic + PNG đúng + frames đủ | ✅ | Chạy 2 lần SHA256 giống hệt; sprite-sheet.test AC-1a/1b/1c |
| AC-2 | PNG có alpha hợp lệ | ✅ | sprite-sheet.test AC-2 (opaque>100, transparent>50) |
| AC-3 | Mèo sprite sheet, không drawCat; walk 4f + idle-cycle | ✅ | GameScene không gọi drawCat/drawButterfly; AC-3 Playwright (≥2 frames + 2 shot khác) |
| AC-4 | Bướm vỗ cánh 4 frames | ✅ | anim bfl-flutter 4 frames; shot garden-dusk có bướm sheet |
| AC-5 | Ma float 2 frames phủ (136,14) | ✅ | haunted-ghost2.png + freeze-ngay byte-compare |
| AC-6 | Chủ (GARDEN+BIRTHDAY) + bánh kem (70,40) | ✅ | birthday2.png + garden-day.png |
| AC-7 | FX deterministic, không Math.random | ✅ | fx.test AC-7a/b/c |
| AC-8 | Bụi/đom đóm/hơi thở/tia lửa đúng scene | ✅ | fx.test AC-8a..d + shots |
| AC-9 | Light pool: player sáng hơn góc màn | ✅ | AC-9 probe: brightness chênh ≥ 10/255 (34.7 vs 0 — crop dưới-trái) |
| AC-10 | Parallax far 0.25 / near 1.15 | ✅ | GameScene setScrollFactor(0.25/1.15); farTex redraw rtime; nearTex 1200×270 |
| AC-11 | Shake + zoom 1.04; frozen không đổi | ✅ | AC-11 Playwright (offset ≠ 0, zoom 1.04, byte-compare) |
| AC-12 | Fade ease-out | ✅ | fx.test AC-12 (fadeAlpha (fadeT/0.6)²×0.75) |
| AC-13 | Night tint lerp 1.5s theo timers.dark | ✅ | fx.test AC-13 (2.5→0, 1.0→0.18, chỉ GARDEN) |
| AC-14 | Regression: core 26 + smoke 3 + e2e 8 + visual 19+ | ✅ | 50/50 vitest + 38/38 Playwright (tổng 88/88) |
| AC-15 | Vendor byte-identical (SHA256 baseline) | ✅ | sprite-sheet.test AC-15 = vendor-hashes.json |
| AC-16 | Determinism visual (frozen 500ms byte-compare) | ✅ | Mọi shot cũ + mới byte-compare |
| AC-17 | Build PASS + không dep mới | ✅ | vite build PASS; package.json không thêm dep |
| AC-18 | Vanilla untouched | ✅ | git diff --quiet HEAD -- games/yuniebel = 0 |
| AC-19 | Anim đứng yên khi frozen (kể cả freeze-ngay) | ✅ | AC-19 Playwright (H_INIT freeze ngay → byte-identical) |
| AC-20 | Flip khớp vị trí (bbox) | ✅ | AC-20 Playwright (bbox ±4px) |
| AC-21 | Prod build có sprite + preview shot | ✅ | dist/assets 5 PNG (assetsInlineLimit 0) |
| AC-22 | Mây parallax hiển thị | ✅ | farTex redraw mỗi frame; shot garden-day so COMPARISON |
| AC-23 | Night tint không NaN (guard R-01) | ✅ | fx.test AC-23 (undefined → theo darkness) |

## 2. Đánh giá theo 4 hướng user chọn (E = A+B+C+D)

| Hướng | Nội dung | Đánh giá |
|-------|----------|----------|
| **A** | Sprite sheet PNG thật + Phaser Animation | ✅ Mèo walk 4f (thay 2f) + idle-cycle (blink + đuôi vẫy), bướm vỗ cánh 4f, ma float 2f, chủ, bánh kem nến cháy 2f — `tools/gen-sprites.mjs` 0 dependency, deterministic, palette vendor |
| **B** | Hiệu ứng deterministic + light pool | ✅ Bụi 14 hạt, đom đóm 10 (đêm), hơi thở ma 8, tia lửa lò sưởi 6 (BIRTHDAY); light pool radial gradient quanh nguồn sáng theo scene (thay overlay phẳng); PRNG seeded — 100% deterministic, không Math.random |
| **C** | Parallax + camera effect | ✅ farTex mây 3 lớp drift + nearTex cỏ/hoa 1.15 scroll; shake manual deterministic (sin/cos) khi scare; zoom lerp 1.04 khi scare 5 |
| **D** | Transition mượt | ✅ Fade 0.6s ease-out (t²); night tint lerp 1.5s khi trời tối (guard NaN) |

## 3. Bài học (lessons learned)

1. **Phaser 4 camera effects không đáng tin trong setup custom canvas** — `shake`/`zoomTo` không update tự động (camera.update không được gọi) + `Math.random` nội bộ phá determinism → tự quản lý (manual scroll offset + zoom lerp) vừa deterministic vừa test được.
2. **`add.image` không có AnimationState** — sprite cần `play()` phải dùng `add.sprite` (lỗi chỉ lộ khi test đọc `anims.currentFrame`).
3. **PNG screenshot từ Playwright dùng filter Paeth + colorType RGB** — decode phải hỗ trợ đủ 5 filters + 2 color types (không chỉ filter 0).
4. **WebGL readback (`getImageData`) rỗng khi `preserveDrawingBuffer=false`** — probe pixel phải decode PNG screenshot thay vì drawImage + getImageData.
5. **WebServer EBUSY khi build đè dist** — quy trình clean (kill node → build → preview) trước khi chạy Playwright; `reuseExistingServer` chỉ an toàn khi server đúng bản build.
6. **Lỗi index mảng `src[4]` vs `src[3]`** — bug runtime im lặng chỉ lộ qua pageerror + phân lập phase từng scene (phương pháp bisect phase hiệu quả).
7. **Fail-closed đúng nghĩa** (bài học TASK-079): mọi shot non-empty + byte-compare; test đặc biệt có assert định lượng (probe số, bbox, frame count) — không "chụp cho có".

## 4. Đề xuất cải tiến tiếp theo

- Sprite sheet 2D array (mèo nhiều hướng trong 1 sheet) — hiện flipX đơn giản đủ.
- Sound design: thêm SFX đom đóm/hơi thở (hiện chỉ visual).
- `imagedata.md` → chuẩn hóa thành skill reference (R9 proposal M11).
- Tối ưu: gộp fx/pool/tint vào 1 texture render pass (hiện 3 layer riêng).

## 5. Thống kê

- **Files**: +16 (tools/gen-sprites.mjs, src/fx/fx.js, src/assets/ 6 file, test/fx.test.js, test/sprite-sheet.test.js, test/png-decode.mjs, test/vendor-hashes.json) + 4 sửa (GameScene.js, main.js? — KHÔNG main.js đổi, package.json, vite.config.js, visual.spec.js, index.html? no).
- **Test**: 88/88 (50 vitest + 38 Playwright) — regression 56/56 giữ nguyên + 32 test mới.
- **Hard gate**: plan → spec v3.1 (23 AC) → critique ×2 (28 + 16 vấn đề resolved) → tasks (14 mục) → review (2 P1 + 4 P2 resolved) → implement → test → evaluate.
