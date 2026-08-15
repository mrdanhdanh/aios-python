# Critique vòng 1 — TASK-077 (bởi critic agent, 2026-08-15)

## Đánh giá chung
Spec rõ về câu chuyện, cấu trúc file, ràng buộc kỹ thuật và có 15 AC. NHƯNG chưa đủ để implement an toàn: (1) state machine chỉ liệt kê state cấp cảnh, thiếu sub-state/phase trong từng cảnh — nguồn chính của "kẹt trigger"; (2) không quy định đường dẫn tài nguyên → rủi ro vỡ asset khi deploy sub-path (AC1 file:// vs URL `/aios-python/games/yuniebel/`); (3) AC visual (AC2–AC12) không có phương thức kiểm chứng; (4) nhiều case biên chưa được quyết định (bấm X giữa chừng, spam phím, mèo kẹt trigger, đổi ý sau chọn).
**Mức sẵn sàng: 3/5 — cần sửa trước khi implement.**

## Phản biện

### P1 — Bắt buộc sửa

**C1-01 — Đường dẫn tài nguyên: AC1 (file://) xung đột tiềm ẩn với deploy sub-path (P1)**
- Vấn đề: Game deploy tại sub-path `/aios-python/games/yuniebel/`, còn AC1 yêu cầu mở bằng file:// vẫn chơi được. Hai môi trường chỉ cùng hoạt động nếu MỌI đường dẫn là relative và dùng script tag **classic** (`<script type="module">` bị CORS chặn trên file://).
- **RESOLUTION: CHẤP NHẬN** → spec bổ sung ràng buộc: script classic + relative path + cấm absolute/fetch/module. test.md thêm bước kiểm tra Network chỉ có request local.

**C1-02 — State machine thiếu sub-state trong cảnh (P1)**
- Vấn đề: Chuỗi `TITLE → GARDEN → ...` chỉ là state cấp cảnh; các chuỗi bên trong cảnh (bướm, máu, cutscene) cần sub-state kèm điều kiện chuyển.
- **RESOLUTION: CHẤP NHẬN** → spec bổ sung bảng phase đầy đủ: `GARDEN: G_INIT → G_BUTTERFLY → G_CHASE → G_DARK → G_DOOR`; `KITCHEN: K_BLOOD → K_VOICE → K_CHOICE → (K_RUN → HAUNTED | K_OBEY → GAMEOVER)`; `DINING: D_APPROACH → D_JUMP → D_HUG → D_CAKE → D_END`; mỗi transition ghi điều kiện.

**C1-03 — Cửa cảnh 1 phải khóa tới khi chạm bướm (P1)**
- Vấn đề: Nếu cửa vẫn mở, người chơi đi thẳng vào cửa → bỏ lỡ chuỗi bướm/trời tối.
- **RESOLUTION: CHẤP NHẬN** → cửa bị chặn (invisible wall) tới khi chạm bướm; chạm bướm 1 lần → despawn; bướm bay giới hạn trong biên bản đồ.

**C1-04 — AC visual (AC2–AC12) thiếu phương thức kiểm chứng (P1)**
- Vấn đề: `node test/core.test.js` chỉ test logic thuần; AC visual không Node-test được → trạng thái done mơ hồ.
- **RESOLUTION: CHẤP NHẬN** → test.md quy định: (1) manual checklist ~15 bước đi hết mọi nhánh (2 lựa chọn, Game Over, X giữa chừng, START lại, resize, tab background); (2) danh sách node test case tối thiểu (C2-10); (3) mỗi AC ghi rõ verify bằng node test hay manual.

### P2 — Nên sửa

**C2-01 — Cơ chế nạp module cho Node test chưa quy định (P2)**
- **RESOLUTION: CHẤP NHẬN** → core.js = logic + dữ liệu thuần (không window/document/rAF), export kèm UMD guard (`typeof module !== 'undefined'`); game.js/audio.js/sprites.js không nằm trong test.

**C2-02 — Điều khiển mobile/touch chưa quyết định (P2)**
- **RESOLUTION: CHẤP NHẬN** → thêm d-pad ảo (4 nút) hiển thị khi phát hiện `ontouchstart`, set key state tương đương WASD.

**C2-03 — Input: spam phím, key repeat, focus loss (P2)**
- **RESOLUTION: CHẤP NHẬN** → key state set (keydown/keyup), bỏ qua `e.repeat`, `preventDefault` WASD/arrows, clear key state khi `blur`/`visibilitychange`; hộp lựa chọn one-shot (khóa tới khi transition xong).

**C2-04 — Knockback cửa trước cảnh 4 (P2)**
- **RESOLUTION: CHẤP NHẬN** → knockback 40px ngược hướng + cooldown 1.5s; mỗi lần chạm: đẩy 1 lần + cảnh báo "Bóng tối chặn cửa! Hồn ma đẩy mèo lùi lại!"; hồn ma canh cửa trước (vẽ sprite), cửa hành lang ở vị trí khác rõ ràng (mũi tên chỉ).

**C2-05 — Cảnh 5: cơ chế "5 lần hù" (P2)**
- **RESOLUTION: CHẤP NHẬN** → 5 scare zone cố định theo độ sâu, fire-once; hành lang one-way (cửa vào đóng sau lưng); counter "Bị hù: x/5" góc dưới màn hình; sau scare thứ 5 → mở cửa phòng ăn + mũi tên chỉ.

**C2-06 — Cảnh 6: cutscene (P2)**
- **RESOLUTION: CHẤP NHẬN** → script cutscene: vào trigger cạnh bàn → khóa input → mèo tự di chuyển tới mép bàn → nhảy (nội suy 0.5s) → chủ ôm (2 sprite chồng nhau + heart) → bubble "Happy Birthday Yuniebel!" + chime → bánh kem hiện + text gõ từng chữ → 2.5s → nút Chơi lại.

**C2-07 — Reset trạng thái: X / Chơi lại / Game Over (P2)**
- **RESOLUTION: CHẤP NHẬN** → hàm `resetGame()` duy nhất reset toàn bộ (scene, trigger flags, scare counter, darkness, audio, hộp thoại); X và mọi nút Chơi lại gọi hàm này; X không cần xác nhận (game ngắn).

**C2-08 — Delta time không clamp (P2)**
- **RESOLUTION: CHẤP NHẬN** → clamp dt max 50ms; trigger check dùng vị trí mới mỗi frame (đủ với bản đồ nhỏ + clamp).

**C2-09 — pages.yml thiếu chi tiết (P2)**
- **RESOLUTION: CHẤP NHẬN** → chốt workflow trong spec: `actions/checkout@v4` + `actions/configure-pages@v5` + `actions/upload-pages-artifact@v3` (path `games`) + `actions/deploy-pages@v4`; permissions `contents: read / pages: write / id-token: write`; trigger `push master` + `workflow_dispatch`; AC13 đổi thành "pages.yml tồn tại + syntax hợp lệ + deploy thử (cần user bật Pages tại Settings → Pages → GitHub Actions)"; bước thủ công ghi trong test.md.

**C2-10 — AC14 thiếu danh sách test case tối thiểu (P2)**
- **RESOLUTION: CHẤP NHẬN** → spec liệt kê: (1) di chuyển 4 hướng + biên; (2) collision vật cản; (3) chuỗi trigger cảnh 1 (4 phase) + cảnh 3 (2 nhánh) + cảnh 4 (knockback) + cảnh 5 (5 lần, không fire lặp) + cảnh 6; (4) mọi transition kể cả GAMEOVER + reset; (5) light radius.

### P3 — Nhẹ

- **C3-01 — Vùng tối cảnh 3 đi vào trước khi chọn** → RESOLUTION: trước phase K_CHOICE, vùng tối là tường vô hình; từ K_CHOICE trở đi, mèo đi vào vùng tối = GAMEOVER (tương đương chọn [2]).
- **C3-02 — "Kiểm tra vết máu" chưa rõ cơ chế** → RESOLUTION: vết máu = trigger zone, chạm = hoàn thành nhiệm vụ → phase K_VOICE.
- **C3-03 — Nội dung hội thoại chưa chốt** → RESOLUTION: chốt toàn bộ text trong spec (mục "Nội dung hội thoại").
- **C3-04 — Bướm AI** → RESOLUTION: bướm bay pattern sin (hover), khi mèo cách < 60px thì bay tránh xa (tốc độ 85 px/s < mèo 120 px/s — đuổi kịp sau ~3–5s), giới hạn biên bản đồ, despawn khi chạm.
- **C3-05 — Audio "footstep" không khớp scope** → RESOLUTION: bỏ footstep khỏi scope — chỉ meow/scare/chime.
- **C3-06 — Input lock khi fade** → RESOLUTION: khóa input trong lúc fade (transition timer).
- **C3-07 — localStorage/điểm số mâu thuẫn hồ sơ** → RESOLUTION: ghi rõ "không có điểm số/localStorage — ngoài scope" trong spec.
- **C3-08 — Resolution/scale** → RESOLUTION: canvas nội phân giải 480×270 (16:9), CSS scale giữ tỷ lệ với window (letterbox), `image-rendering: pixelated`.

## Kết luận
- [x] Cần sửa trước khi implement: C1-01..04 + C2-01..10 + C3-01..08 — **TẤT CẢ ĐÃ RESOLVE** (xem mục RESOLUTION ở trên, spec.md đã cập nhật).
