# Critique vòng 2 — TASK-077 (bởi critic agent, 2026-08-15)

## Đánh giá chung
Spec sau resolve vòng 1 đã cải thiện rõ: state machine có bảng sub-state, AC gắn phương thức kiểm chứng, ràng buộc path/deploy/input/audio chốt, pages.yml chi tiết. Mức sẵn sàng 3.5/5 — còn thiếu dữ liệu cụ thể: kích thước bản đồ, danh sách sprite, quy tắc trigger, input lock per phase.

## 1. Rà soát resolution vòng 1 → spec
16/20 đã phản ánh đúng. **Thiếu/không đầy đủ (4)**: C3-04 (bướm AI) — KHÔNG có trong spec; C3-01 (tường vô hình vùng tối trước K_CHOICE) — chỉ có nửa sau; C2-05 (cửa vào đóng sau lưng hành lang) — không mô tả cơ chế; C2-04 (mũi tên cửa hành lang cảnh 4 + heart D_HUG) — không có. Mâu thuẫn nhỏ: AC16 thiếu "audio" so với C2-07.

## 2. Vấn đề mới

### P1 — Bắt buộc sửa

**C2-11 — Thiếu kích thước bản đồ từng cảnh + policy camera**
- **RESOLUTION: CHẤP NHẬN** → chốt: GARDEN 960×270 (scroll ngang, camera follow), HALLWAY 960×270, LIVING/KITCHEN/HAUNTED/DINING 480×270 (vừa canvas, không camera). Policy: map > canvas → camera follow mèo + clamp biên map; map ≤ canvas → không camera. Test: clamp tọa độ + camera clamp.

**C2-12 — Thiếu quy tắc trigger zone (fire-once/re-activate/ưu tiên overlap)**
- **RESOLUTION: CHẤP NHẬN** → (a) mỗi phase khai báo danh sách zone active riêng, fire-once trong phase, tự re-activate khi phase quay lại; (b) ưu tiên xử lý: knockback/cảnh báo TRƯỚC chuyển cảnh (không chuyển cảnh cùng frame bị knockback); (c) zone tối thiểu ≥ 16px mỗi chiều; (d) trigger check sau di chuyển + clamp.

### P2 — Nên sửa

**C2-13 — Thiếu danh sách sprite + lưới + frame animation**
- **RESOLUTION: CHẤP NHẬN** → bảng sprite tối thiểu trong spec (16×16 lưới, scale 3x, ≤ 16 màu/palette): mèo (idle + walk 2 frame, 2 hướng + mirror), bướm (2 frame vỗ cánh), chủ (idle + ôm), hồn ma (float 2 frame), bánh kem (nến cháy 2 frame), cửa (khóa/mở), bàn, vết máu, mây, mặt trời, cây, hoa, heart, mũi tên chỉ đường.

**C2-14 — Chưa quy định input trong hộp thoại/cutscene**
- **RESOLUTION: CHẤP NHẬN** → mỗi phase có cờ `inputLocked` (bảng phase thêm cột); khi lock: WASD/click bỏ qua NHƯNG key state vẫn cập nhật (tránh dính phím); phím 1/2 chỉ xử lý khi phase = K_CHOICE; nút X luôn hoạt động ở MỌI state (gọi resetGame — không bao giờ kẹt); bubble KHÔNG chặn di chuyển (chỉ cutscene cảnh 6 + fade mới lock hoàn toàn).

**C2-15 — Game timer theo dt (tab ẩn nhảy phase)**
- **RESOLUTION: CHẤP NHẬN** → MỌI timing logic dùng dt tích lũy từ rAF (game-time accumulator), cấm setTimeout/setInterval cho logic game; tab ẩn → rAF dừng → pause tự nhiên, quay lại tiếp tục đúng trạng thái; test node: không dt → không transition.

**C2-16 — Bướm AI chưa vào spec**
- **RESOLUTION: CHẤP NHẬN** → bổ sung đúng C3-04: bay pattern sin, mèo cách < 60px → bay tránh (85 px/s < mèo 120 px/s, đuổi kịp 3–5s), giới hạn biên bản đồ, chạm = despawn 1 lần.

**C2-17 — Vùng tối cảnh 3 + light radius chưa định nghĩa**
- **RESOLUTION: CHẤP NHẬN** → trước K_CHOICE: vùng tối = tường vô hình; từ K_CHOICE: đi vào = K_OBEY. Light radius 90px quanh mèo, áp dụng cảnh 4 & 5; cảnh 3 sáng (chỉ vùng tối cục bộ tối); cảnh 1 G_DARK: darkness 0→1 trong 5s là overlay nền (KHÔNG light radius — vẫn dễ đi, chỉ tối bầu trời/khung). Test: darkness tăng đúng 0→1 trong 5s.

**C2-18 — Collision resolution chưa quy định**
- **RESOLUTION: CHẤP NHẬN** → collision kiểu slide (tách X/Y, trượt dọc bề mặt); vật cản/biên/tường vô hình ≥ 8px (an toàn với bước 6px/frame); knockback cũng áp dụng collision (đẩy tới khi chạm tường, không xuyên).

### P3 — Nhẹ

- **C2-19 — AC16/AC17**: RESOLUTION: AC16 thêm "audio" vào reset; AC17: d-pad = div overlay 4 nút, touchstart/touchend (giữ = di chuyển liên tục), có touch → ẩn hint bàn phím.
- **C2-20 — pages.yml nhánh**: RESOLUTION: trigger cả 2 nhánh `[master, main]` (không biết chắc nhánh chính).
- **C2-21 — Fade + visual thiếu**: RESOLUTION: fade 0.5s; D_HUG thêm heart; HAUNTED thêm mũi tên chỉ cửa hành lang; bubble chủ cảnh 1 có thể bị cắt khi mèo chạm cửa sớm (CHẤP NHẬN).
- **C2-22 — Audio degradation**: RESOLUTION: WebAudio không khả dụng → mute hoàn toàn, game vẫn chơi; `ctx.resume()` khi gesture/tab quay lại.

## 3. Đánh giá AC16/AC17 + bảng sub-state
Đủ về ý tưởng. Cần thêm 3 cột cho bảng phase: `inputLocked`, zone active, timer duration — sẽ bổ sung vào tasks.md khi implement. AC16 cần case test "gọi resetGame 2 lần liên tục không lỗi".

## Kết luận
- [x] Cần sửa trước khi implement: C2-11..C2-18 (P1+P2) + C2-19..C2-22 (P3) — **TẤT CẢ ĐÃ RESOLVE** (spec.md đã cập nhật). Mức sẵn sàng sau sửa: 4.5/5 — đủ điều kiện sang tasks.md.
