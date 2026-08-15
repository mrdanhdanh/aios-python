# TASK-082 — Tasks breakdown

> **Date**: 2026-08-16 | **Spec**: v3 (2 critique đã resolve) | Trạng thái: checklist

## P0 — Asset pipeline (A)

- [ ] **T1. `tools/gen-sprites.mjs`** — PNG encoder (signature/IHDR/IDAT zlib level 9/IEND/CRC32) + pixel maps:
  - [ ] T1.1 CAT 8 frames (walk0-3, idle, blink, tail0, tail1) 48×48, palette vendor
  - [ ] T1.2 BUTTERFLY 4 frames 48×48 (cánh mở dần), bướm 8×6 ở tâm
  - [ ] T1.3 GHOST 2 frames 54×72 (đuôi lượn 2 trạng thái), sọ trắng + dithering
  - [ ] T1.4 OWNER 1 frame 48×48 (tóc nâu, áo xanh #2e86de)
  - [ ] T1.5 CAKE 2 frames 60×48 (nến y0-7, thân y8-14, đế y14-16)
  - [ ] T1.6 sprites.json (meta + frames) cho 5 sheet
- [ ] **T2. Chạy gen**: sinh `src/assets/*.png` + `sprites.json`; verify magic bytes + SHA256 deterministic (chạy 2 lần diff)
- [ ] **T3. package.json**: thêm `gen:sprites` + `pretest`

## P1 — FX deterministic (B)

- [ ] **T4. `src/fx/fx.js`**:
  - [ ] T4.1 `mulberry32(seed)` + `hashSeed(str)` — PRNG seeded
  - [ ] T4.2 `fxState(scene, s, time)` — dust (GARDEN ngày, cây (230,40)+nhà), fireflies (GARDEN đêm), breath (HAUNTED), sparks (BIRTHDAY (8,40)) — thuần hàm
  - [ ] T4.3 `renderFx(ctx, s, time)` — vẽ particles
  - [ ] T4.4 `renderLightPool(ctx, s, time)` — ambient α theo scene (GARDEN 0.75×(d-0.5), HAUNTED 0.28, LIVING 0.15, BIRTHDAY 0.12, HALLWAY 0.18) + radial gradients quanh nguồn sáng (bảng tường minh)
  - [ ] T4.5 `nightTintAlpha(s)` — chỉ GARDEN + guard R-01: t = timers.dark ?? 5*(1-darkness); clamp((2.5-t)/1.5,0,1)*0.18
  - [ ] T4.6 `fadeAlpha(fadeT)` — (fadeT/0.6)² × 0.75
  - [ ] T4.7 Tất cả fxState/renderFx/renderLightPool nhận **camX (px)** — nguồn world trừ camX (R-02)

## P2 — GameScene tích hợp (A+B+C+D)

- [ ] **T5. GameScene.js**:
  - [ ] T5.1 `preload()`: load.spritesheet cat/butterfly/ghost/cake + load.image owner + load.json sprites (import module URL)
  - [ ] T5.2 `create()`: anims (cat-walk, cat-idle-cycle, bfl-flutter, ghost-float, cake-flame) + fx/parallax/tint/pool textures + images (ghost/owner/cake)
  - [ ] T5.3 `update()`: quy tắc frozen (không play(), setFrame cố định; pauseAll/resumeAll + play ignoreIfPlaying=true — R-07.7); renderSprites(rtime, time); parallax redraw (farTex rtime, nearTex 1 lần); camera shake/zoom theo scareActive (guard frozen; `_prevScare` init 0 — R-07.2); night tint; fade mới 0.6 ease-out; HALLWAY pool α 0.12 + đuốc tường (R-06)
  - [ ] T5.4 `renderSprites`: mèo sheet (origin 0.5, pos p.x*3+24, flipX, walk/idle-cycle — pixel map dịch 1px tránh cắt tai R-07.4), bướm sheet, ghost (408,42 + bob rtime + alpha 0.85), owner (GARDEN 858,156 / BIRTHDAY 288,126), cake (210,120 + cake-flame)
  - [ ] T5.5 overlay đêm cũ trong renderBg GARDEN → thay bằng light pool (bỏ dark overlay phẳng)
- [ ] **T6. main.js**: import PNG/JSON module → truyền GameScene (registry hoặc import)

## P3 — Test

- [ ] **T7. `test/sprite-sheet.test.js`**: PNG signature/IHDR/alpha decode (zlib.inflateSync), frames JSON đủ (cat 8, bfly 4, ghost 2, owner 1, cake 2), SHA256 deterministic + committed khớp, vendor-hashes.json (4 SHA256 baseline)
- [ ] **T8. `test/vendor-hashes.json`**: tính SHA256 4 vendor files
- [ ] **T9. `test/fx.test.js`**: PRNG deterministic (cùng seed → cùng output), fxState theo scene/darkness + camX, nightTintAlpha số cụ thể (2.5→0, 1.0→0.18, undefined+darkness=1→0.18, undefined+darkness=0→0 — R-01), fadeAlpha ease-out
- [ ] **T10. `test/visual.spec.js`**: giữ 19 shot cũ (bump chờ 700ms — R-07.1) + thêm 7 shot mới (cat-walk riêng không byte-compare; cat-idle-cycle; garden-night-fx + probe AC-9 qua getImageData — R-07.6; haunted-ghost2 + freeze-ngay; birthday2; living-fx; hallway-scare5-zoom theo thứ tự R-03) + **AC-20 flip bbox test (R-05)** + **AC-11 shake/zoom sequencing (R-03)**
- [ ] **T11. Chạy full suite**: `npm test` (vitest + playwright) — regression ≥ 56 + mới PASS; build + dist/assets verify + vite preview shot; **AC-18: `git diff --quiet HEAD -- games/yuniebel` = 0 (R-05)**

## P4 — Tài liệu + đóng gate

- [ ] **T12. test.md** — ghi kết quả test thật
- [ ] **T13. evaluation.md** — đối chiếu 23 AC (v1..v3.1), bài học; **COMPARISON.md update (R-05**: walk 4f, owner 1 frame, bướm 24×18, hallway pool, mây parallax)
- [ ] **T14. DoD**: LOG.md + PROGRESS.md + PLAN.md (nếu cần) + STATS.md (nếu milestone) + commit

## AC mapping

| AC | Tasks | AC | Tasks | AC | Tasks |
|----|-------|----|-------|----|-------|
| AC-1..2 | T1, T2, T7 | AC-8..9 | T4, T5.5, T10 | AC-15..16 | T8, T10 |
| AC-3..6 | T5.4, T10 | AC-10..11 | T5.3, T10 | AC-17..18 | T6, T11 |
| AC-7 | T4, T9 | AC-12..13 | T4.5-4.6, T9 | AC-19..22 | T5.3, T10, T11 |
| AC-20 | T10 (flip bbox) | AC-23 | T9 | AC-18 | T11 |
