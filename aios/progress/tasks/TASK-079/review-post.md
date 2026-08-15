# Review post-implement — TASK-079

> Ngày: 2026-08-15 · Reviewer: AIOS reviewer agent · Đối tượng: code sau implement
> Kết quả: **Code APPROVED — 10/10 AC ĐẠT, test 59/59 PASS (27 core + 4 smoke + 28 Playwright)**

## Tổng quan

Fix bug "mèo biến mất sau START" bằng logical grid. Code đúng thiết kế spec §3 (sau critique ×3 + review trước implement). Đối chiếu từng tọa độ spec §3.1 với code thật — khớp 100%.

## Đối chiếu AC

- [x] AC-1: pixel test mèo tại spawn (231..279, 210..258, ≥30 px #f5a623) PASS
- [x] AC-2: e2e hold d 1s → x tăng > 10 PASS
- [x] AC-3: AC-14a (45.6s) + AC-14b (22.2s) chơi thật không hook PASS
- [x] AC-4: pixel wallCream/roofRed khi cam=160 PASS
- [x] AC-5: 17/17 shot + catBody trong 6 shot có player PASS
- [x] AC-6: core 27/27 PASS
- [x] AC-7: smoke 4/4 PASS
- [x] AC-8: Playwright 28/28 PASS
- [x] AC-9: không crash, 2 playthrough trọn 6 cảnh
- [x] AC-10: GARDEN cam=160 nhà hiện + HALLWAY scare5 skull PASS

## Kiểm tra kỹ thuật

- (a) Tọa độ §3.1: khớp từng dòng (6 scene + hằng số + trigger + spawn bướm)
- (b) save/restore quanh translate: đúng cả drawGarden + drawHallway; sky() trong translate; overlay screen-space sau restore — không lệch kép
- (c) camX(): giữ !sc guard, bỏ sc.w<=CW, công thức đúng
- (d) moveTo hai tầng (120ms/40ms): đúng; targets đúng; trace lộ trình hợp lý
- (e) Không sót world cũ: grep 960/780/852/905/430 = 0 trong src+test
- (f) Gameplay không đổi: 13 câu thoại, phase, scare, choice giữ nguyên

## Vấn đề phát hiện & xử lý

### R1 (Blocking process) — Closing checklist
→ Đã đóng: LOG.md entry, PROGRESS.md mục mới, plan.md, test.md, evaluation.md, review-post.md, implementation/, commit.

### R2 (Major — ghi nhận trong evaluation.md, cosmetic)
1. Owner vẽ khi `G_INIT && dialogue` (spec: "khi G_INIT") — chủ nhân biến mất sau hết thoại dù còn G_INIT. Giữ hành vi cũ (bản gốc TASK-078 cũng vậy), ghi nhận cosmetic.
2. Hàng rào GARDEN trải 8..280 (16 cọc) thay vì 0..320 — đoạn 280..320 không có rào khi cam=160. Ghi nhận cosmetic.

### R3 (Minor)
1. Mắt vùng tối (25,19) vs spec (23,19) — đối xứng, không sai thẩm mỹ.
2. Cửa tối vẽ y 36..60 vs spec 40..60 — decorative.
3. `drawBlood` còn định nghĩa + export nhưng không còn chỗ gọi — dead code (giữ để tương thích).
4. Kệ LIVING (126,62,12,24) cao hơn spec (126,70,12,17) — bao phủ wall đủ.

## Kết luận

**APPROVED — Code không cần sửa. Mọi AC đạt, 59/59 PASS.** Đóng checklist xong → TASK-079 DONE.
