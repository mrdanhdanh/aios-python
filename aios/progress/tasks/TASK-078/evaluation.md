# TASK-078 — Evaluation (đánh giá cuối)

> Ngày: 2026-08-15 · Owner: AIOS Orchestrator · Kết quả: **TASK-078 DONE**

## 1. Đối chiếu tiêu chí chấp nhận (14/14 ĐẠT)

| AC | Nội dung | Kết quả | Bằng chứng |
|----|----------|---------|------------|
| AC-1 | 13 câu thoại 100% brief-scenario.md | ✅ | core.test.js (assert từng câu + dấu) + R-01 fix hiển thị thật |
| AC-2 | Task canonical §6.1 + đổi task sau knockback đầu | ✅ | core.test.js bảng phase→task + ghostBlocked |
| AC-3 | Mood nhạc theo §6.3 (10 mood) đúng phase | ✅ | e2e assert getMood + R-03 fix title music |
| AC-4 | ≥15 SFX + getStats + reset màn chơi | ✅ | e2e assert 22 SFX + R-02 fix resetStats |
| AC-5 | Garden động ngày→hoàng hôn→đêm + đèn hiên + cửa tối | ✅ | 3 ảnh chụp + pixel check (xanh 47,125,224 → cam → đêm 9,23,62) |
| AC-6 | Bếp: tủ trắng/lò/tủ lạnh/vết máu lớn/mắt sáng | ✅ | kitchen-blood.png |
| AC-7 | Ma xanh đầu lâu + knockback + đổi task + cửa phụ | ✅ | haunted-ghost.png + core.test (H_EXIT→W_INIT) |
| AC-8 | 5 kiểu hù riêng biệt + counter 0→5 + nhạc ấm | ✅ | 5 ảnh scare + core.test + R-04 scare hết hạn |
| AC-9 | Sinh nhật: lò sưởi + bánh kem + text + sparkle + chuông | ✅ | birthday.png + core.test (D_END→END bell) |
| AC-10 | Chọn 2 → GAME OVER; chọn 1 → phòng khách ma ám | ✅ | core.test + e2e AC-14b chơi thật |
| AC-11 | 17 ảnh chụp canvas 480×270 | ✅ | test-results/shots/ + task folder shots/ (17 file) |
| AC-12 | test/brief README + skip khi thiếu ref + COMPARISON.md | ✅ | test/brief/* + test kiểm tra COMPARISON thật (R-09) |
| AC-13 | Cả 3 suite pass | ✅ | **54/54**: core 27 + smoke 4 + Playwright 23 |
| AC-14 | 2 test chơi thật không hook | ✅ | e2e AC-14a (42.7s → D_END) + AC-14b (21.4s → GAME_OVER) |

## 2. Kết quả test cuối cùng

- `node test/core.test.js` → **27/27 PASS**
- `node test/smoke.test.js` → **4/4 PASS**
- `npx playwright test` → **23/23 PASS** (e2e 4 + visual 19)
- **Tổng: 54/54 PASS**

## 3. Đối chiếu với yêu cầu người dùng

1. **"Làm lại từ đầu vì làm xấu quá"** → ✅ Viết lại hoàn toàn 8 file (core/sprites/audio/game/index/style + 4 test files), đồ họa theo 5 ảnh tham khảo (palette + bố cục + chi tiết từng cảnh), trời động ngày→hoàng hôn→đêm, 5 kiểu hù riêng biệt, ma xanh đầu lâu, vết máu lớn...
2. **"Test phải chụp ảnh và so với brief, không hời hợt"** → ✅ 17 ảnh chụp thật (Playwright) + COMPARISON.md đối chiếu từng ảnh với brief-visuals.md (17/17 khớp) + 2 test chơi thật không hook chứng minh gameplay đạt mọi phase + ảnh lưu làm bằng chứng trong task folder.
3. **Kịch bản chi tiết** → ✅ 13 câu thoại nguyên văn (kể cả dấu …/~/?!), 9 task text chính xác, 10 mood nhạc nền, 21+ SFX đúng sự kiện.

## 4. Bài học

- **Review sau implement bắt được bug mà test không thấy**: dialogue G_INIT không hiển thị (R-01) — test chỉ assert data, không assert hiển thị thật. Bài học: mọi phase có dialogue phải có test "sau startGame + 1 frame → dialogue active".
- **mix() màu lỗi NaN nghiêm trọng** (canvas đen toàn bộ) — phát hiện nhờ đọc pixel thật (System.Drawing) thay vì nhìn ảnh. Bài học: luôn verify render bằng pixel check, không chỉ "không crash".
- **Overlay HTML che canvas** khiến ảnh chụp tối — bài học: chụp ảnh test phải kiểm tra lớp phủ UI.
- **e2e chơi thật cần helper di chuyển thông minh** (ưu tiên trục Y, dừng khi phase đổi, đọc state mỗi bước) — test script cứng (bấm phím cố định) dễ flaky.
- **Fix qua review-post**: 12 vấn đề (1 P1 + 3 P2 + 8 P3) đều sửa được trong task — giá trị của post-review không thể bỏ qua.

## 5. Thống kê

- Files tạo/sửa: 8 game files + 5 test files + 3 brief files + 17 ảnh chụp
- Hard gate: plan → spec → critique ×2 (36 vấn đề resolved) → tasks → review (12 vấn đề) → implement → test (54/54) → post-review (12 vấn đề resolved) → evaluate
- Thời lượng: ~2-3 phiên (khảo sát + hard gate + implement + test + fix)

## 6. Đề xuất cải tiến (ngoài scope)

- Thêm ảnh ref thật của người dùng vào `test/brief/` để bật pixel-compare tự động (hiện skip vì không có file)
- Cân nhắc lưu điểm/achievement (localStorage) cho các màn chơi lại
- Tối ưu âm thanh: piano vui tươi cảnh 6 có thể nâng cấp thêm arpeggio
