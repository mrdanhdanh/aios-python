# Review trước implement — TASK-078 (bởi reviewer agent)

> Ngày: 2026-08-15 · Kết luận: **APPROVED WITH NOTES** — đủ điều kiện implement
> 12 vấn đề (R1..R12) — toàn bộ đã resolve (xem bảng dưới). Test phủ đủ 14/14 AC.

## Đối chiếu tiêu chí chấp nhận

| AC | Kiểm chứng được? | Bằng chứng |
|----|------------------|------------|
| AC-1 | ✅ | core.test.js assert 13 câu thoại |
| AC-2 | ✅ | core.test.js assert task + ghostBlocked |
| AC-3 | ✅ | e2e assert audio.getMood() |
| AC-4 | ✅ | e2e assert audio.getStats() 21 key |
| AC-5..9 | ⚠️ thủ công | 17 ảnh chụp + bảng đối chiếu brief trong test.md |
| AC-10 | ✅ | core.test.js + e2e |
| AC-11 | ✅ (phụ thuộc R1) | visual.spec.js + bảng §8.1 |
| AC-12 | ✅ | test.skip(!fs.existsSync) + COMPARISON.md |
| AC-13 | ✅ | cả 3 suite |
| AC-14 | ✅ (phụ thuộc R3) | e2e đọc state (C2-14) |

## Vấn đề + resolution

- **R1 [P1] — Freeze phải đóng băng MỌI nguồn animation, không chỉ state.time** (code cũ game.js dùng biến local `time` cho S.cat/S.butterfly/mây/flash…). → **RESOLVED**: game.js mới chỉ đọc `state.time` cho mọi animation; thêm test "chụp 2 lần cách 500ms với freeze → pixel giống hệt" vào visual.spec.js.
- **R2 [P1] — audio.getStats() đếm tầng request, không phụ thuộc AudioContext/resume/mute** (headless trả 0 → AC-4 fail giả). → **RESOLVED**: mọi hàm SFX tăng counter ngay đầu hàm trước mọi check; **mặc định âm thanh BẬT** (nút hiển thị "MUTE" để tắt).
- **R3 [P2] — AC-14 vượt timeout 30s** (chuỗi chơi thật 40–90s). → **RESOLVED**: `test.setTimeout(120_000)` cho 2 test AC-14; điểm dừng = phase `D_END` (không chờ END screen).
- **R4 [P2] — Mâu thuẫn END emoji** (bảng §6 còn "🎂"). → **RESOLVED**: sửa dòng END bảng §6: "Nền ấm, chữ 'Chúc Mừng Sinh Nhật Yuniebel!' (không emoji — vẽ bánh kem pixel), nút 'Chơi lại' → title".
- **R5 [P3] — Điều kiện W_INIT→W_WALK** → **RESOLVED**: W_INIT phát dialogue 1 câu, tự chuyển W_WALK khi queue rỗng.
- **R6 [P3] — Điều kiện D_END→END** → **RESOLVED**: sau 3 câu thoại phát xong + timer 3s → auto chuyển END.
- **R7 [P3] — Cơ chế tối dần G_DARK** → **RESOLVED**: darkness ramp tuyến tính 5s từ lúc bắt bướm; chuyển G_DOOR khi x>790 bất kể darkness.
- **R8 [P3] — Ảnh garden-dusk thiếu setButterfly** → **RESOLVED**: bảng §8.1 ảnh 3 thêm `setButterfly(x,y)` trước mặt mèo.
- **R9 [P3] — Tham chiếu §palette không tồn tại** → **RESOLVED**: tasks.md sửa thành "palette hằng số theo brief-visuals.md (mục Tổng hợp palette)".
- **R10 [P3] — playwright.config.js chưa có bước cập nhật** → **RESOLVED**: thêm checkbox P3: testMatch bao gồm visual.spec.js, timeout tăng, args `--autoplay-policy=no-user-gesture-required`.
- **R11 [P3] — smoke.test giữ fallback audio khi jsdom không có AudioContext** → **RESOLVED**: audio.js giữ try/catch init an toàn (mute hoàn toàn khi không khả dụng).
- **R12 [P3] — Ngưỡng x>780 (bướm) vs x>790 (cửa)** → **RESOLVED**: giữ 2 ngưỡng + ghi chú "bướm xuất hiện trước, cửa sau".

## Kết luận

- [x] **APPROVED WITH NOTES** — đủ điều kiện implement sau khi resolve R1–R12 (đã resolve toàn bộ).
- Bắt buộc tuân thủ khi implement: R1 (freeze + test determinism), R2 (getStats tầng request, sound ON mặc định), R3 (timeout 120s, điểm dừng D_END), R4 (END không emoji).
