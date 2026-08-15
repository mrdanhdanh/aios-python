# Critique vòng 2 — TASK-078 (bởi critic agent)

> Ngày: 2026-08-15 · Đánh giá: 3.5/5 — không còn P1; 7 P2 + 12 P3, **đã resolve toàn bộ** (xem bảng dưới).
> Xác nhận vòng 1: 14/17 resolve trọn vẹn; 3 resolution (C1-09→C2-06, C1-13→C2-14, C1-17→C2-13) chuyển thành vấn đề mới.
> Điểm mạnh đã xác nhận: 13 câu thoại khớp **nguyên văn từng ký tự** với `brief-scenario.md`; bảng nhiệm vụ §6.1 khớp 100% brief; chuỗi phase logic chính đúng.

## C2-01 [P2] — `K_CHOICE` không có trong bảng phase canonical §6.1
- **RESOLVED**: Thêm `K_CHOICE` vào §6.1 (nhiệm vụ giữ "Kiểm tra vết máu!" — hộp lựa chọn hiện); ghi chú TITLE/GAME_OVER/END không thuộc bảng task.

## C2-02 [P2] — Thiếu đặc tả điều khiển (controls)
- **RESOLVED**: Thêm §7 Controls: `←/→/WASD` di chuyển mèo, `↑/↓/W/S` cũng di chuyển (game 2D), dialogue **tự advance** theo `dur` (không cần key, bấm phím để advance nhanh — Space/Enter), lựa chọn bằng phím `1`/`2` **và** click, nút "Chơi lại" click được, START click hoặc Enter.

## C2-03 [P2] — Lối thoát phòng ma ám chưa định nghĩa (nguy cơ deadlock)
- **RESOLVED**: Phòng ma ám có **2 cửa**: cửa chính giữa (ma xanh đầu lâu chặn — knockback vĩnh viễn) + **cửa phụ bên trái** mở sẵn dẫn vào hành lang. Knockback chỉ đẩy khỏi cửa chính. Chuỗi: `H_INIT → H_BLOCK (knockback lần 1, đổi task) → H_EXIT (cửa phụ) → W_INIT`.

## C2-04 [P2] — Bảng chụp thiếu scare 2/3/4 + thiếu API set scare zone
- **RESOLVED**: Bảng §8.1 thêm 3 ảnh `hallway-scare2/3/4.png` (tổng 17 ảnh). Debug API thêm **`setScareZone(n|null)`** — force hiển thị kiểu hù thứ n theo mapping §6.2 (sprite + dấu "!"/"!!"/"!!!"/"!?").

## C2-05 [P2] — AC-4 thiếu SFX brief bắt buộc
- **RESOLVED**: Bổ sung AC-4: `rush` (chạy gấp gáp — chọn 1), `candle` (nến cháy — D_END), `footstep_grass` (cỏ — S1), `footstep_echo` (hành lang), `whisper_far` (ma ám). Ambient list §7 thêm "bước chân". §5.5/§5.6 bổ sung dòng âm thanh "thì thầm xa" + "bước chân vang vọng".

## C2-06 [P2] — AC-3 thiếu tên mood canonical + bảng phase→mood
- **RESOLVED**: Thêm §7 bảng Phase→Mood (tên ASCII cho `getMood()`): TITLE=`calm-happy`, G_*= `garden-calm`, G_DARK=`dusk-sad`, L_SEARCH=`mystery`, K_*= `kitchen-mystery`, H_*= `tense`, W_WALK=`suspense`, W_DONE=`warm`, D_END=`celebration`, GAME_OVER=`dusk-sad`. Quy tắc đổi mood theo sự kiện (bắt bướm→dusk-sad; zone 5 xong→warm).

## C2-07 [P2] — Cơ chế bướm chưa đặc tả (AC-14 dễ flaky)
- **RESOLVED**: §5.2 bổ sung: bướm xuất hiện khi mèo đến vùng cửa (x>780); bay theo **waypoint cố định** (vòng lặp: 3 điểm trong vườn, vận tốc 60px/s); **bắt khi mèo chạm** bán kính 12px (hoặc đứng trong bán kính 40px ≥1s). Deterministic cho test thật.

## C2-08 [P3] — §5.3 thiếu dấu chấm cuối nhiệm vụ
- **RESOLVED**: §5.3 → "Tìm chủ nhân ở nhà bếp." (thêm dấu chấm).

## C2-09 [P3] — §7 trùng bullet audio.js, số SFX lệch (12 vs 15)
- **RESOLVED**: Gộp 1 bullet audio.js duy nhất; con số thống nhất **≥15 SFX**.

## C2-10 [P3] — Chi tiết visual từ brief-visuals chưa vào spec (đèn hiên, cửa mở tối, dithering, dầm gỗ, glow)
- **RESOLVED**: §6 thêm câu: "chi tiết chiếu theo `implementation/brief-visuals.md` — nguồn chuẩn cho mọi vật thể/palette chưa liệt kê hết"; AC-5 thêm "đèn hiên sáng theo darkness, cửa mở tối om"; AC-7 thêm "dầm gỗ, mạng nhện, glow xanh".

## C2-11 [P3] — Cảnh sinh nhật không có ảnh ref; mâu thuẫn "chủ ôm mèo" vs "chủ đứng cạnh"
- **RESOLVED**: Ghi chú §6: cảnh 6 không có ảnh ref — visual do spec định. **Chốt: chủ đứng cạnh bánh kem, mèo ngồi cạnh chủ** (không ôm — dễ vẽ pixel). Sửa G9 cho khớp.

## C2-12 [P3] — Emoji 🎂 rủi ro font headless CI
- **RESOLVED**: §6 END không dùng emoji — vẽ bánh kem pixel + chữ "Chúc Mừng Sinh Nhật Yuniebel!".

## C2-13 [P3] — "viewport camera 480px" mơ hồ
- **RESOLVED**: AC-11 quy định chụp bằng `locator('canvas').screenshot()` — clip đúng canvas 480×270, bỏ chữ "viewport camera".

## C2-14 [P3] — AC-14 "không hook" chưa rõ việc đọc state
- **RESOLVED**: Ghi rõ: "không hook = không gọi debug setter; **được phép đọc state** (phase/task) để điều hướng input".

## C2-15 [P3] — Autoplay policy chặn nhạc title trước gesture
- **RESOLVED**: §7: resume AudioContext tại gesture đầu (mousedown/keydown bất kỳ hoặc click START); title "câm" tới gesture đầu — chấp nhận.

## C2-16 [P3] — `audio.getStats()` cần reset theo màn chơi
- **RESOLVED**: §7: `getStats()` trả counter từ đầu **màn chơi hiện tại** (reset khi START/Chơi lại).

## C2-17 [P3] — Điều kiện chuyển phase trung gian (G_DARK/G_DOOR, H_BLOCK/H_EXIT)
- **RESOLVED**: §6.1 thêm ghi chú: `G_DARK→G_DOOR` khi mèo đứng trước cửa (x>790); `H_BLOCK→H_EXIT` khi mèo chạm cửa phụ (x<60); gộp task text giữ nguyên.

## C2-18 [P3] — Bảng chụp chưa kiểm soát hội thoại hiển thị
- **RESOLVED**: Bảng §8.1 thêm cột "Dialogue" (có/không) cho từng ảnh; dùng `setMessage(text, until=∞)` + freeze khi cần bong bóng.

## C2-19 [P3] — Nút bật/tắt âm thanh không có trong brief
- **RESOLVED**: Giữ nút MUTE (góc phải trên, mặc định bật) — vì WebAudio nhạc nền liên tục dễ gây khó chịu; thêm 1 dòng §7.

---

## Kết luận
- [x] **Đã resolve toàn bộ C2-01..C2-19** (7 P2 + 12 P3) — đủ điều kiện implement.
- [x] **Critique ×2 đã đủ** (vòng 1: 17 vấn đề; vòng 2: 19 vấn đề — không còn P1).
