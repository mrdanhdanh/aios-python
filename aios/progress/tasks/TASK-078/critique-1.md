# Critique vòng 1 — TASK-078 (bởi critic agent)

> Ngày: 2026-08-15 · Đánh giá: 2.5/5 — CHƯA đủ điều kiện implement (3 P1 + 7 P2 + 7 P3)
> Toàn bộ vấn đề **đã resolve** (xem bảng dưới) trước khi chạy critique vòng 2.

## C1-01 [P1] — Kịch bản gốc + 5 ảnh tham khảo KHÔNG có trong repo
- **Vấn đề**: §4 tham chiếu `implementation/brief-scenario.md` + `brief-visuals.md` không tồn tại; không có ảnh png/jpg nào trong workspace → AC-1/AC-5..9 là tự quy chiếu.
- **RESOLVED**: Tạo `implementation/brief-scenario.md` (nhúng nguyên văn kịch bản 7 phần người dùng) + `implementation/brief-visuals.md` (mô tả chi tiết 5 ảnh: palette, bố cục, vật thể — phân tích từ vision). AC-1 sửa → "khớp 100% `implementation/brief-scenario.md`". Ảnh gốc là file đính kèm chat, người dùng xác nhận không đưa file vào repo → mô tả văn bản là nguồn chuẩn.

## C1-02 [P1] — Debug hook chưa đủ để chụp ảnh deterministic
- **Vấn đề**: rAF loop (mây, bướm, anim, lửa, sparkle) → screenshot pixel khác nhau mỗi lần → flaky.
- **RESOLVED**: Spec §7 bổ sung debug API đầy đủ: `setPhase`, `setPlayer(x,y)`, `setDarkness(v)`, `setTimers({name:v})`, `setScareCount(n)`, `setMessage(text,until)`, `setChoice(1|2)`, `setButterfly(x,y|null)`, **`freeze(true|false)`** — khi freeze, updateGame không tiến triển `state.time` (mọi anim dựa `state.time`).

## C1-03 [P1] — Thiếu cơ chế chụp "hoàng hôn" (trạng thái trung gian)
- **Vấn đề**: darkness trôi liên tục 0→1 trong 5s → không chụp được khoảnh khắc.
- **RESOLVED**: Spec §11 thêm bảng ≥12 phase/scene cần chụp kèm **state set trước từng ảnh** (vd `hoang-hon.png = phase G_CHASE, darkness 0.5, freeze`).

## C1-04 [P2] — Không có bảng phase→task canonical; nhiệm vụ G_INIT chưa xác minh
- **Vấn đề**: §5.2 ghi "Nhiệm vụ ban đầu: 'Vào nhà đi!'" không khớp dòng đầu kịch bản ("Đuổi theo con bướm!").
- **RESOLVED**: Thêm bảng `Phase → Task` canonical §6. Quyết định: **G_INIT nhiệm vụ = "Đuổi theo con bướm!"** (khớp dòng đầu kịch bản + ảnh B panel 1 hiển thị task này ngay). Khi mèo tiến gần cửa → bướm xuất hiện (SFX "ting", anim bướm bay vào) — nhiệm vụ giữ "Đuổi theo con bướm!" (không cần đổi vì đã là task). Bắt bướm → trời tối → "Hãy vào nhà!".

## C1-05 [P2] — Mâu thuẫn số liệu câu thoại: 15 vs 13
- **Vấn đề**: §5 chỉ có 13 câu thoại nhưng G1/AC-1 ghi 15.
- **RESOLVED**: Đếm lại — 13 câu thoại unique (S1:2, S2:1, S3:3, S4:2, S5:1+Meow!!, S6:3). Sửa G1 → "13 câu", AC-1 → "13 câu thoại khớp 100% brief".

## C1-06 [P2] — Thiếu luồng + visual màn END/GAME OVER
- **Vấn đề**: sau GAME OVER và sau cảnh 6 hiện gì, text gì, nút gì.
- **RESOLVED**: Spec §4 bổ sung: **GAME OVER** = nền tối đỏ + mèo kêu đau + chữ "GAME OVER" + dòng "Yuniebel đã đi vào bóng tối…" + nút "Chơi lại" → reset về title; **END** (sau cảnh 6) = nền ấm + chữ "🎂 Chúc mừng sinh nhật Yuniebel! 🎂" + nút "Chơi lại" → title. Bổ sung §6 visual 2 màn.

## C1-07 [P2] — Title ảnh ref portrait vs canvas landscape
- **Vấn đề**: ảnh ref title dọc, canvas 480×270 ngang.
- **RESOLVED**: Spec §3 ghi rõ "render lại theo 480×270 landscape — bố cục: trời gradient trên, nút START giữa, đồi/núi/cây/nước dưới, mèo cạnh nút".

## C1-08 [P2] — 5 kiểu hù chưa ánh xạ scare zone
- **Vấn đề**: chưa nói kiểu nào ở zone nào.
- **RESOLVED**: Spec §4/§8 mapping cố định: `scare1 → ma trắng ga`, `scare2 → chân dung hét`, `scare3 → tay zombie`, `scare4 → bóng mắt vàng`, `scare5 → mặt xương sọ`.

## C1-09 [P2] — AC-3/AC-4 (âm thanh) không kiểm chứng tự động được
- **Vấn đề**: Playwright không nghe audio.
- **RESOLVED**: Spec §11 bổ sung: debug hook expose `audio.getMood()` + `audio.getStats()` (counter từng SFX) → e2e assert mood đổi đúng phase + tổng loại SFX ≥10 + mỗi SFX bắn đúng sự kiện.

## C1-10 [P2] — Scope quá lớn 1 task
- **Vấn đề**: rewrite game + sequencer 5 mood + 15 SFX + visual test.
- **RESOLVED**: tasks.md chia 4 phase: **P0** core+text (AC-1,2,10,14) → **P1** visual 6 cảnh (AC-5..9) → **P2** audio (AC-3,4) → **P3** visual.spec + đối chiếu brief (AC-11,12,13). Fallback: audio tối thiểu trước nếu nghẽn (mood đơn giản + SFX chính), nâng cấp sau — AC-3/4 vẫn bắt buộc.

## C1-11 [P3] — Thiếu chậu cây ở phòng khách
- **RESOLVED**: Thêm "chậu cây" vào §6 Phòng khách.

## C1-12 [P3] — AC-12 "skip khi thiếu ảnh" cần cơ chế cụ thể
- **RESOLVED**: Dùng `test.skip(!fs.existsSync(refPath), ...)` khi thiếu ảnh ref + ghi kết quả đạt/không đạt vào `test/brief/COMPARISON.md`.

## C1-13 [P3] — AC-11 (hook) vs AC-14 (gameplay thật) cần tách bạch
- **RESOLVED**: Ghi rõ: ảnh chụp (AC-11) dùng hook để ổn định; AC-14 = 1 test e2e **chơi thật** title→sinh nhật + 1 test title→game over (không hook).

## C1-14 [P3] — Thời điểm đổi task "Phải đi qua phòng khác!"
- **RESOLVED**: Đổi task **sau lần knockback đầu tiên** (vĩnh viễn); các lần sau chỉ knockback + SFX.

## C1-15 [P3] — Debug hook `?test=1` an toàn
- **RESOLVED**: Hook chỉ active khi URL có `?test=1`; game đơn giản static, chấp nhận cheat — ghi quyết định vào spec.

## C1-16 [P3] — WebAudio sequencer chống throttle tab ẩn
- **RESOLVED**: Scheduler theo audio clock (`ctx.currentTime` lookahead), không phụ thuộc rAF — ghi vào §7.

## C1-17 [P3] — Screenshot = camera viewport 480px, không phải toàn map
- **RESOLVED**: Ghi chú AC-11: ảnh chụp = viewport camera tại vị trí set trước; đối chiếu brief chỉ so khung hình tương ứng.

---

## Kết luận
- [x] **Đã resolve toàn bộ C1-01..C1-17** (3 P1 + 7 P2 + 7 P3) — sẵn sàng critique vòng 2.
