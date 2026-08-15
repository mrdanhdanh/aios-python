# TASK-077 — Webgame 2D Pixel "Yuniebel" (GitHub Pages)

## Mục tiêu

Tạo một webgame 2D pixel art hoàn toàn static (0 dependency, chạy offline), kể câu chuyện mèo "Yuniebel" đi tìm chủ nhân trong một ngôi nhà bí ẩn, kết thúc bằng màn chúc mừng sinh nhật. Game deploy được qua GitHub Pages, đặt trong thư mục riêng `games/yuniebel/`, tách hẳn khỏi backend AIOS.

## Phạm vi

- **Trong phạm vi**:
  - Thư mục mới `games/yuniebel/` (HTML + CSS + JS thuần, canvas 2D, pixel art vẽ bằng code — không dùng file ảnh/audio ngoài)
  - 6 cảnh chơi + màn hình chính (title) + màn hình Game Over + màn hình Kết thúc
  - Điều khiển WASD, nút bật/tắt UI, khung nhiệm vụ + nút X về màn hình chính
  - Lựa chọn 1/2 tại cảnh bếp, knockback hồn ma, 5 lần hù dọa hành lang
  - Hiệu ứng: trời tối dần, fade chuyển cảnh, màn tối quanh mèo (darkness), jumpscare flash, âm thanh WebAudio tự sinh (meow, scare, chime — không cần file)
  - Workflow `.github/workflows/pages.yml` deploy folder `games/` → GitHub Pages
  - Test logic thuần bằng Node (`node test/core.test.js`)
- **Ngoài phạm vi**: không đụng code backend AIOS, không dùng MCP/API (game static không cần), không dùng framework/build tool, không phụ thuộc CDN/font ngoài (chỉ monospace system font).

## Input / Output

- **Input**: bàn phím WASD (di chuyển), phím bấm/click cho lựa chọn, click nút START / nút X / nút toggle UI.
- **Output**: canvas 2D hiển thị game, UI overlay (khung nhiệm vụ, nút toggle, hộp lựa chọn, hộp thoại).

## Luồng trò chơi (story beats — theo yêu cầu người dùng)

1. **Title**: bầu trời xanh, mây bay, mặt trời, nút START.
2. **Cảnh 1 — Sân vườn**: mèo chơi ngoài vườn; chủ gọi từ trong nhà → nhiệm vụ "Vào nhà". Khi mèo tới gần cửa → bướm xuất hiện → nhiệm vụ "Đuổi theo con bướm". Chạm bướm → trời dần tối → nhiệm vụ "Trời tối — hãy vào nhà" → vào cửa → Cảnh 2.
3. **Cảnh 2 — Phòng khách**: không thấy chủ → nhiệm vụ "Tìm chủ nhân — đến nhà bếp" → vào bếp → Cảnh 3.
4. **Cảnh 3 — Nhà bếp**: thấy vết máu dưới sàn → nhiệm vụ "Kiểm tra vết máu". Kiểm tra xong → vùng tối phát ra lời gọi → hộp lựa chọn:
   - **[1] Bỏ chạy** → mèo chạy về phòng khách → Cảnh 4.
   - **[2] Nghe theo lời gọi** → mèo bước vào vùng tối → màn hình tối dần → **GAME OVER** (nút Chơi lại → Title).
5. **Cảnh 4 — Phòng khách ma ám**: căn phòng quỷ dị (tối, sương mù, hồn ma). Nhiệm vụ "Tìm người chủ". Đi ra cửa trước → bị hồn ma **đẩy lùi** (knockback + flash + cảnh báo). Phải đi qua cửa phòng tiếp theo (hành lang) → Cảnh 5.
6. **Cảnh 5 — Hành lang dài**: đi càng sâu càng bị hù dọa; **5 sự kiện hù** (scare flash + shake + âm thanh). Đủ 5 lần → đến cửa phòng ăn → Cảnh 6.
7. **Cảnh 6 — Phòng ăn / Sinh nhật**: chủ ngồi bàn chờ; mèo lại gần → nhảy lên bàn → chủ ôm mèo → bong bóng "Happy Birthday Yuniebel!" → bánh kem hiện ra + dòng chữ chúc mừng sinh nhật → màn hình Kết thúc (nút Chơi lại).

## State machine — phase/sub-state (chi tiết, theo C1-02)

State cấp cảnh: `TITLE → GARDEN → LIVING → KITCHEN → HAUNTED → HALLWAY → DINING → END`, nhánh `KITCHEN → GAMEOVER`, nhánh `any → TITLE` (nút X / reset).

Sub-state (phase) mỗi cảnh + điều kiện chuyển:

| Cảnh | Phase | Điều kiện vào | Trigger chuyển tiếp |
|------|-------|---------------|---------------------|
| GARDEN | `G_INIT` | vào cảnh | chủ gọi (auto 2s), mèo chạm vùng cửa (door zone, cửa bị khóa) |
| GARDEN | `G_BUTTERFLY` | mèo vào door zone (lần đầu) | bướm spawn gần cửa, bay ra vườn |
| GARDEN | `G_CHASE` | bướm spawn xong | mèo chạm bướm (AABB, 1 lần → despawn bướm) |
| GARDEN | `G_DARK` | chạm bướm | darkness 0→1 trong 5s, mở khóa cửa |
| GARDEN | `G_DOOR` | darkness >= 1 | mèo chạm vùng cửa → vào LIVING |
| LIVING | `L_SEARCH` | vào cảnh | mèo chạm vùng cửa bếp → KITCHEN |
| KITCHEN | `K_INIT` | vào cảnh | mèo chạm vùng vết máu |
| KITCHEN | `K_BLOOD` | chạm máu | hộp thoại "vết máu..." (1.5s) → `K_VOICE` |
| KITCHEN | `K_VOICE` | xong K_BLOOD | lời gọi từ vùng tối (2s) → hiện hộp lựa chọn → `K_CHOICE` |
| KITCHEN | `K_CHOICE` | hộp chọn hiện | **[1] Bỏ chạy** → `K_RUN`; **[2] Nghe theo** → `K_OBEY`; mèo đi vào vùng tối = `K_OBEY` |
| KITCHEN | `K_RUN` | chọn 1 | mèo chạy về phía cửa phòng khách (auto, 1.5s) → HAUNTED |
| KITCHEN | `K_OBEY` | chọn 2 | mèo đi vào vùng tối (auto) → màn tối dần → GAMEOVER |
| HAUNTED | `H_SEARCH` | vào cảnh | chạm cửa trước → knockback + cảnh báo (cooldown 1.5s, không chuyển cảnh); chạm cửa hành lang → HALLWAY |
| HALLWAY | `W_WALK` | vào cảnh | mỗi scare zone (5 zone cố định, fire-once) → scare event + counter |
| HALLWAY | `W_DONE` | scare count = 5 | mở cửa phòng ăn + mũi tên chỉ → chạm cửa → DINING |
| DINING | `D_APPROACH` | vào cảnh | mèo chạm vùng cạnh bàn → khóa input |
| DINING | `D_JUMP` | cutscene | mèo tự di chuyển tới mép bàn → nhảy lên bàn (nội suy 0.5s) |
| DINING | `D_HUG` | nhảy xong | chủ ôm mèo + bubble "Happy Birthday Yuniebel!" + chime |
| DINING | `D_CAKE` | 1.5s sau D_HUG | bánh kem hiện + text chúc mừng gõ từng chữ |
| DINING | `D_END` | text xong + 2.5s | màn Kết thúc (END) + nút Chơi lại |

Mọi transition đều có fade; input bị khóa trong lúc fade (C3-06).

## Kiến trúc file

```
games/yuniebel/
├── index.html          # Canvas + UI overlay, script tag CLASSIC (không module), relative path
├── style.css           # Pixel style (image-rendering: pixelated), UI layout, letterbox
├── src/
│   ├── core.js         # Logic THUẦN (test bằng Node): scenes, phases, tasks, collision, trigger, state machine, light radius, resetGame. KHÔNG window/document/rAF; UMD guard (typeof module !== 'undefined' → module.exports)
│   ├── sprites.js      # Pixel art maps (mèo hồng, bướm, chủ, ma, bánh kem...) + render helper (browser only)
│   ├── audio.js        # WebAudio SFX tự sinh (meow/scare/chime)
│   └── game.js         # Game loop (rAF), input, scene rendering, UI wiring (browser only)
└── test/
    └── core.test.js    # Node test cho core.js (assert thủ công, exit code)
.github/workflows/pages.yml  # Deploy games/ → GitHub Pages
```

## Ràng buộc đường dẫn & môi trường (C1-01)

- MỌI đường dẫn tài nguyên là **relative** (`src/core.js`, `style.css`); **cấm** URL tuyệt đối (bắt đầu `/`), **cấm** `fetch`, **cấm** `<script type="module">` (CORS chặn trên file://).
- Game chạy được cả khi mở bằng `file://` lẫn deploy tại `/aios-python/games/yuniebel/`.
- Không dùng điểm số/localStorage (ngoài scope — C3-07).

## Tiêu chí chấp nhận (Acceptance Criteria)

Phương thức kiểm chứng: **[node]** = `node test/core.test.js`; **[manual]** = manual checklist trong test.md; **[visual]** = xem bằng mắt khi chạy game.

- **AC1** [manual+visual] Mở `games/yuniebel/index.html` bằng file:// là chơi được; DevTools → Network chỉ có request local (C1-01).
- **AC2** [visual] Title: bầu trời xanh + mây bay + mặt trời + nút START → vào Cảnh 1.
- **AC3** [node+manual] Mèo pixel tóc hồng, di chuyển WASD 4 hướng, bị chặn bởi biên bản đồ và vật cản.
- **AC4** [manual] Nút bật/tắt UI góc trên phải: ẩn/hiện khung nhiệm vụ + hướng dẫn điều khiển.
- **AC5** [manual] Khung nhiệm vụ góc trên trái hiển thị nhiệm vụ hiện tại; nút X → về Title (gọi `resetGame()` — AC16).
- **AC6** [node+manual] Cảnh 1 đúng chuỗi: Vào nhà → gần cửa (cửa KHÓA tới khi chạm bướm — C1-03) → bướm xuất hiện → đuổi bướm → chạm bướm (despawn) → trời tối dần 5s → nhiệm vụ về nhà → vào cửa → Cảnh 2.
- **AC7** [node+manual] Cảnh 2: phòng khách, không có chủ, nhiệm vụ tìm chủ ở bếp; vào bếp → Cảnh 3.
- **AC8** [node+manual] Cảnh 3: chạm vết máu → kiểm tra (K_BLOOD) → lời gọi → lựa chọn; [1] → Cảnh 4; [2] hoặc đi vào vùng tối → Game Over (màn RIP + Chơi lại).
- **AC9** [node+manual] Cảnh 4: ma ám (tối + sương + hồn ma canh cửa trước), ra cửa trước → knockback 40px + cooldown 1.5s + cảnh báo; cửa hành lang → Cảnh 5.
- **AC10** [node+manual] Cảnh 5: hành lang one-way, 5 scare zone fire-once (counter "Bị hù: x/5"), sau 5 lần → mở cửa + mũi tên → Cảnh 6.
- **AC11** [node+manual] Cảnh 6: cutscene đúng thứ tự (lại gần → nhảy → ôm → "Happy Birthday Yuniebel!" → bánh kem + text gõ chữ → END + Chơi lại).
- **AC12** [visual] Fade chuyển cảnh; cảnh 1 tối dần sau khi chạm bướm; vùng sáng quanh mèo ở cảnh tối (4, 5); input khóa khi fade.
- **AC13** [manual] `pages.yml` tồn tại + syntax hợp lệ (validate YAML); deploy thử khi user bật Pages (Settings → Pages → GitHub Actions) → URL `/aios-python/games/yuniebel/` hoạt động. Bước thủ công ghi trong test.md.
- **AC14** [node] `node test/core.test.js` PASS — tối thiểu các case (C2-10): (1) di chuyển 4 hướng + biên; (2) collision vật cản không xuyên; (3) chuỗi trigger cảnh 1 (4 phase); (4) cảnh 3 2 nhánh + đi vào vùng tối; (5) cảnh 4 knockback + không chuyển cảnh; (6) cảnh 5 5 lần fire-once + mở cửa; (7) cảnh 6 chuỗi cutscene; (8) mọi transition + GAMEOVER; (9) `resetGame()` reset toàn bộ; (10) light radius.
- **AC15** [manual] Hard gate đầy đủ 8 file + cập nhật LOG.md/PROGRESS.md + commit.
- **AC16** [node] `resetGame()` là hàm duy nhất reset toàn bộ state (scene, phases, trigger flags, scare counter, darkness, hộp thoại, audio, timers); nút X và mọi nút Chơi lại đều gọi nó (C2-07); gọi resetGame 2 lần liên tục không lỗi (C2-19).
- **AC17** [manual] Mobile: d-pad ảo (div overlay 4 nút) hiện khi `ontouchstart` — `touchstart/touchend` giữ ngón = di chuyển liên tục (tương đương keydown/keyup); khi có touch → ẩn hint bàn phím (C2-02/C2-19).

## Ràng buộc kỹ thuật

- Canvas 2D nội phân giải **480×270** (16:9, C3-08), CSS scale giữ tỷ lệ với window (letterbox), `image-rendering: pixelated`, scale sprite 3x.
- Pixel art định nghĩa bằng ma trận ký tự (string array), mỗi ký tự = 1 màu — vẽ lên offscreen canvas, không dùng file ảnh.
- Vòng lặp `requestAnimationFrame` + delta time **clamp dt ≤ 50ms** (C2-08); physics đơn giản (AABB, velocity, walk speed 120 px/s); trigger check theo vị trí mới mỗi frame.
- Trigger zone: AABB tĩnh theo scene; mỗi scene có mảng phase/trigger/story events (theo bảng sub-state ở trên).
- Input: key state Set (keydown/keyup), bỏ qua `e.repeat`, `preventDefault` WASD/arrows, clear key state khi `blur`/`visibilitychange` (C2-03); hộp lựa chọn one-shot (khóa tới khi transition xong); d-pad ảo khi `ontouchstart` (C2-02).
- UI overlay: div HTML (không vẽ lên canvas) — khung nhiệm vụ, hộp thoại, hộp lựa chọn, counter hù.
- Toàn bộ text tiếng Việt có dấu (canvas fillText hỗ trợ unicode; font system monospace).
- Âm thanh: WebAudio tự sinh, khởi tạo context sau gesture đầu tiên (autoplay policy) — meow/scare/chime (C3-05). WebAudio không khả dụng → mute hoàn toàn, game vẫn chơi bình thường; `ctx.resume()` khi có gesture mới / quay lại tab (C2-22).
- Fade chuyển cảnh: 0.5s (C2-21).
- `resetGame()`: duy nhất reset toàn bộ state, gọi từ nút X / Chơi lại (C2-07).

## Bản đồ & camera (C2-11)

| Cảnh | Kích thước map (px) | Camera | Ghi chú |
|------|--------------------|--------|---------|
| GARDEN | 960×270 | follow mèo (clamp biên) | vườn rộng scroll ngang |
| LIVING | 480×270 | không | vừa canvas |
| KITCHEN | 480×270 | không | |
| HAUNTED | 480×270 | không | layout giống LIVING, tối + ma |
| HALLWAY | 960×270 | follow mèo | 5 scare zone theo độ sâu |
| DINING | 480×270 | không | |

Camera: map > canvas → follow mèo, clamp không lộ biên; map ≤ canvas → tĩnh.

## Quy tắc trigger zone (C2-12)

- Mỗi phase khai báo danh sách zone **active riêng**; zone fire-once trong phase; tự re-activate khi phase quay lại (door zone GARDEN dùng 2 phase).
- Trùng zone trong 1 frame → ưu tiên: knockback/cảnh báo xử lý TRƯỚC, không chuyển cảnh cùng frame.
- Zone tối thiểu ≥ 16px mỗi chiều (mèo bước tối đa 6px/frame — không lọt zone).
- Trigger check sau khi di chuyển + clamp.

## Sprite list (tối thiểu — C2-13)

Lưới 16×16 (scale 3x = 48px hiển thị), palette ≤ 16 màu, vẽ bằng ma trận ký tự:

| Sprite | Frame | Hướng | Dùng ở |
|--------|-------|-------|--------|
| Mèo (tóc hồng) | idle + walk 2 frame | trái/phải (mirror) | mọi cảnh |
| Bướm | 2 frame vỗ cánh | — | GARDEN |
| Chủ | idle + ôm | phải | GARDEN (gọi), DINING (ngồi bàn) |
| Hồn ma | float 2 frame | — | HAUNTED, HALLWAY (scare) |
| Bánh kem | 2 frame nến cháy | — | DINING |
| Cửa | khóa / mở | — | GARDEN, LIVING, KITCHEN, HAUNTED, HALLWAY, DINING |
| Bàn | 1 frame | — | DINING, KITCHEN |
| Vết máu | 1 frame | — | KITCHEN |
| Mây, mặt trời | mây 2 frame drift | — | TITLE, GARDEN |
| Cây, bụi, hoa | 1 frame | — | GARDEN |
| Heart | 2 frame phồng | — | D_HUG |
| Mũi tên chỉ đường | 1 frame | — | HAUNTED (cửa hành lang), HALLWAY W_DONE |
| Vùng tối (bóng) | 1 frame | — | KITCHEN |

## Input trong hộp thoại/cutscene (C2-14)

- Mỗi phase có cờ `inputLocked` (bảng phase): khi lock, WASD/click di chuyển bị bỏ qua NHƯNG key state vẫn được cập nhật (tránh dính phím).
- Phím 1/2 chỉ xử lý khi phase = K_CHOICE.
- Nút X **luôn hoạt động ở MỌI state** (kể cả fade/cutscene/GAMEOVER — gọi resetGame).
- Bubble/hộp thoại KHÔNG chặn di chuyển; chỉ cutscene cảnh 6 + fade mới lock hoàn toàn.

## Timer (C2-15)

- MỌI timing logic dùng **dt tích lũy từ rAF** (game-time accumulator); cấm setTimeout/setInterval cho logic game (chỉ UI không critical).
- Tab ẩn → rAF dừng → game pause tự nhiên, quay lại tiếp tục đúng trạng thái (không cần pause menu).
- Test: không có dt → không transition.

## Bướm AI (C2-16 / C3-04)

- Bay pattern sin (hover lên xuống, ±8px, tần số 2Hz).
- Mèo cách < 60px → bay tránh xa, tốc độ 85 px/s (mèo 120 px/s → đuổi kịp sau ~3–5s).
- Giới hạn trong biên bản đồ; chạm (AABB) = despawn 1 lần → G_DARK.

## Vùng tối cảnh 3 & light radius (C2-17 / C3-01)

- KITCHEN: trước phase K_CHOICE, vùng tối là **tường vô hình** (chặn đi vào); từ K_CHOICE trở đi, mèo đi vào vùng tối = K_OBEY (GAMEOVER). Phòng sáng — chỉ vùng tối cục bộ tối.
- Light radius: bán kính **90px** quanh mèo, áp dụng cảnh HAUNTED và HALLWAY (tối toàn cảnh, ngoài bán kính chỉ thấy silhouette).
- GARDEN G_DARK: darkness 0→1 trong 5s là overlay nền (bầu trời tối dần, KHÔNG áp dụng light radius — mèo vẫn thấy).

## Collision (C2-18)

- Collision resolution kiểu **slide**: tách trục X/Y — va chạm theo trục nào thì giữ nguyên tọa độ trục đó, vẫn di chuyển trục kia (trượt dọc tường).
- Mọi vật cản/biên/tường vô hình ≥ 8px bề dày (an toàn với bước 6px/frame).
- Knockback cũng áp dụng collision: đẩy tới khi chạm tường, không xuyên.

## Nội dung hội thoại & nhiệm vụ (chốt — C3-03)

| Nơi | Text |
|-----|------|
| Title | Tiêu đề "YUNIEBEL" + phụ đề "Một câu chuyện mèo con" + nút START + hint "WASD để di chuyển" |
| Cảnh 1 — G_INIT | Bong bóng chủ (từ cửa): "Mèo ơi, vào nhà đi!" | Nhiệm vụ: "Nghe lời chủ — vào nhà" |
| Cảnh 1 — G_BUTTERFLY | "Bướm kìa!" | Nhiệm vụ: "Đuổi theo con bướm!" |
| Cảnh 1 — G_CHASE xong | "Mèo bắt được bướm!" | Nhiệm vụ: "Trời tối rồi — nhanh vào nhà!" |
| Cảnh 2 | Nhiệm vụ: "Chủ đâu rồi nhỉ? — Tìm ở nhà bếp" |
| Cảnh 3 — K_BLOOD | "Vết máu dưới sàn... phải kiểm tra!" | Nhiệm vụ: "Kiểm tra vết máu" |
| Cảnh 3 — K_VOICE | Lời gọi từ vùng tối: "Mèo ơi... lại đây..." | Nhiệm vụ: "Có tiếng gọi từ vùng tối..." |
| Cảnh 3 — K_CHOICE | Hộp chọn: "[1] Bỏ chạy" / "[2] Nghe theo lời gọi" |
| Game Over | "Mèo Yuniebel đã đi vào bóng tối..." + "GAME OVER" + nút "Chơi lại" |
| Cảnh 4 | Nhiệm vụ: "Tìm người chủ... căn phòng sao lạ thế này" ; cảnh báo cửa trước: "Bóng tối chặn cửa! Hồn ma đẩy mèo lùi lại!" |
| Cảnh 5 | Nhiệm vụ: "Đi qua hành lang... đừng sợ" + counter "Bị hù: x/5" |
| Cảnh 6 | Nhiệm vụ: "Chủ ở đây rồi!" → cutscene: "Happy Birthday Yuniebel!" + "🎂 Chúc mừng sinh nhật Yuniebel! 🎂" |
| END | "Hết game — Cảm ơn đã chơi!" + nút "Chơi lại" |

## Workflow GitHub Pages (chốt — C2-09)

`.github/workflows/pages.yml`:
- Trigger: `push` nhánh `[master, main]` (paths: `games/**`, `.github/workflows/pages.yml`) + `workflow_dispatch` (C2-20).
- Permissions: `contents: read`, `pages: write`, `id-token: write`; `concurrency: { group: pages, cancel-in-progress: true }`.
- Steps: `actions/checkout@v4` → `actions/configure-pages@v5` → `actions/upload-pages-artifact@v3` (path: `games`) → `actions/deploy-pages@v4`.
- Kết quả URL: `https://mrdanhdanh.github.io/aios-python/games/yuniebel/` (cần user bật Pages → Source: GitHub Actions).
