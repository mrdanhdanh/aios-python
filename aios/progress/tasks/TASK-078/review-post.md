# Review sau implement — TASK-078 (bởi reviewer agent)

> Ngày: 2026-08-15 · Kết luận: **CHANGES REQUESTED → ĐÃ FIX TOÀN BỘ → APPROVED**
> Reviewer phát hiện 1 P1 (R-01) + 3 P2 (R-02..R-04) + 8 P3 (R-05..R-12) — toàn bộ đã resolve.

## Đối chiếu AC (reviewer)

| AC | Kết quả reviewer | Sau fix |
|----|------------------|---------|
| AC-1 | ⚠️ 2 câu G_INIT không hiển thị (R-01) | ✅ dialogue hiển thị ngay sau startGame (test R-01) |
| AC-2 | ✅ (lệch nhỏ thứ tự knockback) | ✅ ghostBlocked + knockback lặp lại (R-11) |
| AC-3 | ⚠️ nhạc title không khởi động (R-03) | ✅ init() bắt đầu sequencer sau gesture đầu |
| AC-4 | ⚠️ resetStats không gọi (R-02) | ✅ soundFlags.start set trong startGame |
| AC-5..9 | ✅ | ✅ |
| AC-10 | ✅ | ✅ |
| AC-11 | ✅ | ✅ |
| AC-12 | ⚠️ placeholder test | ✅ test kiểm tra COMPARISON.md thật (R-09) |
| AC-13 | ✅ 52/52 | ✅ 27 + 4 + 23 = 54/54 |
| AC-14 | ✅ | ✅ |

## Vấn đề + resolution

- **R-01 [P1] — Hội thoại G_INIT không bao giờ hiển thị** (startGame pushDialogue chỉ đặt queue, updateGame chỉ advance khi dialogue active → 2 câu đầu mất trong game thật). → **FIXED**: startGame gọi `nextDialogue` ngay + updateGame thêm `if (!dialogue && queue.length) nextDialogue()`; test core assert câu 1 + câu 2 hiển thị tuần tự.
- **R-02 [P2] — resetStats không bao giờ gọi** (không ai set soundFlags.start). → **FIXED**: startGame set `soundFlags.start = true` + test.
- **R-03 [P2] — Nhạc title không khởi động** (mood mặc định = mood title → setMood không chạy). → **FIXED**: audio.init() khởi động sequencer sau gesture đầu (started flag).
- **R-04 [P2] — Scare vĩnh viễn, flash dead code** → **FIXED**: scareTimer 1.5s reset scareActive + flash 0.5/0.3s; test assert scare hết hạn.
- **R-05 [P3] — G_CHASE/H_EXIT dead code** → chấp nhận (dùng cho ảnh chụp), ghi chú trong code.
- **R-06 [P3] — soundFlags.tick kẹt** → **FIXED**: đổi thành clockTick (có case).
- **R-07 [P3] — flutter không phát** → **FIXED**: updateButterfly set flutter định kỳ.
- **R-08 [P3] — Emoji 🎂 trong end-screen HTML** → **FIXED**: bỏ emoji.
- **R-09 [P3] — Test AC-12 placeholder** → **FIXED**: test kiểm tra COMPARISON.md tồn tại + 17/17.
- **R-10 [P3] — butterflyHit dùng MAX_DT cho stayT** → **FIXED**: stayT dùng dt thật trong updateButterfly + b.caught.
- **R-11 [P3] — Knockback H_BLOCK fire-once** → **FIXED**: delete fired để đẩy lùi lặp theo cooldown.
- **R-12 [P3] — Dead code (lastScene, case rỗng)** → **FIXED**: dọn.

## Kết luận

- [x] **APPROVED** — sau fix: core 27/27 + smoke 4/4 + Playwright 23/23 = **54/54 PASS**; 17 ảnh chụp đối chiếu brief khớp (COMPARISON.md).
