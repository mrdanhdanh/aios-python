# TASK-078 — Làm lại game "Yuniebel's Cat" theo kịch bản chi tiết + ảnh tham khảo

> Ngày: 2026-08-15 · Owner: AIOS Orchestrator · Trạng thái: in-progress
> Tiền thân: TASK-077 (game gốc, 17/17 AC PASS nhưng KHÔNG khớp kịch bản chi tiết & ảnh tham khảo của người dùng)

## 1. Bối cảnh & vấn đề

TASK-077 đã tạo `games/yuniebel/` (webgame 2D pixel 100% static) đạt 17/17 AC nội bộ. Tuy nhiên người dùng cung cấp **kịch bản chi tiết** (7 cảnh: title → sân vườn → phòng khách → nhà bếp → phòng khách ma ám → hành lang → sinh nhật) kèm **5 ảnh tham khảo** (pixel art: sân vườn 3 khoảnh khắc ngày/hoàng hôn/đêm; phòng khách + bếp vết máu; phòng khách ma ám có ma xanh đầu lâu; hành lang 5 kiểu hù; cảnh sinh nhật có lò sưởi + bánh kem).

**Gap analysis (đối chiếu game hiện tại vs brief):**

| # | Hạng mục | Brief yêu cầu | Hiện tại (TASK-077) | Mức độ |
|---|----------|---------------|---------------------|--------|
| G1 | Hội thoại | **13 câu** chính xác (chủ gọi, mèo nghĩ, thì thầm, ma nói…) | Thiếu ~10 câu, vài câu sai từ | ❌ |
| G2 | Nhiệm vụ (task box) | Text chính xác từng phase, đổi task khi bị ma đẩy → "Phải đi qua phòng khác!" | Text lệch, không đổi task sau knockback | ❌ |
| G3 | Nhạc nền theo mood | Title vui tươi; vườn yên bình; tối → trầm buồn; bếp bí ẩn; ma ám căng thẳng; hành lang hồi hộp; sinh nhật piano vui | KHÔNG CÓ nhạc nền (chỉ SFX rời rạc) | ❌ |
| G4 | SFX chi tiết | Ting (bướm), chim, gió, bước chân cỏ, tích tắc đồng hồ, nhỏ giọt, thì thầm echo, swoosh, mèo kêu đau đớn, chạy gấp gáp, whoosh, creak, jump scare (rít/hét/cửa đập), nến cháy, chuông sparkle | Chỉ meow/scare/chime/whisper | ❌ |
| G5 | Visual cảnh 1 | Trời ngày → hoàng hôn → đêm dần tối khi bắt bướm; nhà có hiên, hàng rào, cây, bụi hoa | Gradient tĩnh + overlay tối 40% | ⚠️ |
| G6 | Visual cảnh 3 | Bếp: tủ trắng, lò, tủ lạnh, vết máu LỚN, cửa tối có mắt sáng | Vết máu nhỏ (42×15px), bếp sơ sài | ❌ |
| G7 | Visual cảnh 4 | Ma XANH đầu lâu lớn chặn cửa, phòng tối, đồng hồ quả lắc, chân nến, mạng nhện, ảnh nghiêng, text "Phải đi qua phòng khác!" | Ma nhỏ tím, phòng đơn giản | ❌ |
| G8 | Visual cảnh 5 | 5 kiểu hù riêng biệt: ma trắng, chân dung hét, tay zombie, bóng mắt vàng, mặt xương | Chỉ 1 sprite ma lặp lại | ❌ |
| G9 | Visual cảnh 6 | Lò sưởi lửa, chủ ôm mèo, bánh kem nến, text "Happy Birthday Yuniebel!" + "Chúc Mừng Sinh Nhật!", sparkle | Chủ ngồi + bánh nhỏ, không lò sưởi | ⚠️ |
| G10 | Kết thúc lựa chọn | Chọn 2 → swoosh + mèo kêu đau → GAME OVER | Có GAME OVER nhưng thiếu SFX | ⚠️ |
| G11 | Test | Test phải CHỤP ẢNH màn hình từng cảnh và so với brief | Chỉ assert logic (state/text), không ảnh | ❌ |

## 2. Mục tiêu

Làm lại `games/yuniebel/` để khớp 100% kịch bản chi tiết của người dùng (hội thoại, nhiệm vụ, âm thanh, hiệu ứng) và 5 ảnh tham khảo (visual pixel art), kèm hệ thống test **chụp ảnh màn hình từng cảnh** đối chiếu brief.

## 3. Phạm vi

**Trong phạm vi:**
- `games/yuniebel/index.html`, `style.css`, `src/core.js`, `src/sprites.js`, `src/audio.js`, `src/game.js`
- `games/yuniebel/test/` — core.test.js, smoke.test.js, e2e.spec.js + **mới**: visual.spec.js (chụp ảnh mọi scene/phase), `test/brief/` (thư mục ảnh tham khảo + README hướng dẫn đối chiếu tự động)
- `games/yuniebel/playwright.config.js` — thêm visual.spec.js, snapshot path template → `test/brief/`
- Tài liệu hard gate TASK-078

**Ngoài phạm vi:** không thay đổi backend AIOS, dashboard, extension; không thêm dependency mới (giữ 100% static, 0 build).

## 4. Đầu vào

1. Kịch bản chi tiết người dùng (7 phần — **nhúng nguyên văn** trong `implementation/brief-scenario.md`, đã commit)
2. 5 ảnh tham khảo pixel art (mô tả chi tiết trong `implementation/brief-visuals.md` — ảnh gốc là file đính kèm chat, không nằm trong repo; mô tả văn bản là nguồn chuẩn)
3. Code hiện tại `games/yuniebel/` (TASK-077)

## 5. Đặc tả chức năng (kịch bản chuẩn — canonical text)

### 5.1 Màn hình chính
- Nền trời xanh, mây bay, mặt trời, cỏ cây hoa
- Nút "START" ở giữa
- Nhạc nền nhẹ nhàng vui tươi + tiếng gió + chim hót xa
- Nhấn START → fade-out → cảnh 1

### 5.2 Cảnh 1 — Sân vườn
- Hội thoại tuần tự: (1) Chủ: **"Yuniebel! Vào nhà đi!"** → (2) Mèo nghĩ: **"Meow~ Nhưng ngoài này vui quá…"**
- Nhiệm vụ ban đầu (G_INIT): **"Đuổi theo con bướm!"** (khớp dòng đầu kịch bản + ảnh B panel 1 hiển thị task này ngay — quyết định C1-04)
- Mèo tiến gần cửa (x>780) → **bướm xuất hiện** (tiếng "ting") — nhiệm vụ giữ **"Đuổi theo con bướm!"**
- Cơ chế bướm (C2-07): bướm bay theo **waypoint cố định** (vòng lặp 3 điểm trong vườn, vận tốc 60px/s); **bắt khi mèo chạm** bán kính 12px (hoặc đứng trong bán kính 40px ≥1s)
- Bắt được bướm → trời dần tối (ngày → hoàng hôn → đêm) → nhiệm vụ: **"Hãy vào nhà!"** + nhạc chuyển tone trầm buồn (`dusk-sad`)
- Âm thanh: chim, gió, bước chân mèo trên cỏ (`footstep_grass`)

### 5.3 Cảnh 2 — Phòng khách
- Mèo: **"Meow? Chủ nhân đâu rồi?"** → (không phản hồi, chỉ tiếng đồng hồ tích tắc)
- Nhiệm vụ: **"Tìm chủ nhân ở nhà bếp."**
- Nhạc nhẹ bí ẩn + tiếng đồng hồ + gió lùa cửa sổ

### 5.4 Cảnh 3 — Nhà bếp
- Mèo: **"Meow… có gì đó lạ…"** → phát hiện vết máu → Mèo: **"Meow?! Đây là gì vậy?"**
- Vùng tối thì thầm: **"Đến đây đi… Meow…"**
- Nhiệm vụ: **"Kiểm tra vết máu!"**
- Lựa chọn: 1️⃣ **"Bỏ chạy"** / 2️⃣ **"Nghe theo lời gọi"** (phím 1/2 hoặc click)
- Chọn 2 → swoosh + mèo kêu đau đớn (`pain_meow`) → **GAME OVER**
- Chọn 1 → tiếng chạy gấp gáp (`rush`) → chuyển phòng khách
- Âm thanh: nhỏ giọt (`drip`), thì thầm echo (`whisper`); mắt sáng trong vùng tối

### 5.5 Cảnh 4 — Phòng khách ma ám
- Mèo: **"Meow… căn phòng này… khác rồi…"**
- Hồn ma (xuất hiện, whoosh): **"Không được rời đi…"**
- Nhiệm vụ: **"Tìm người chủ!"**
- **2 cửa (C2-03)**: cửa chính giữa (ma xanh đầu lâu chặn — knockback vĩnh viễn, đổi task sang **"Phải đi qua phòng khác!"** sau lần đầu) + **cửa phụ bên trái mở sẵn** dẫn vào hành lang
- Chuỗi: `H_INIT → H_BLOCK (knockback lần 1 → đổi task) → H_EXIT (cửa phụ) → W_INIT`
- Âm thanh: gió rít (`wind`), cửa creak (`creak`), nhạc căng thẳng (`tense`), whoosh + mèo kêu hoảng (`scared_meow`), thì thầm xa (`whisper_far`)

### 5.6 Cảnh 5 — Hành lang hù dọa
- Mèo: **"Meow… mình phải đi tiếp…"**
- Mỗi lần bị hù: **"Meow!!"** hoảng hốt + jump scare (rít, hét, cửa đập)
- Nhiệm vụ: **"Đi qua hành lang."** → sau 5 lần hù: **"Đã đến phòng ăn."**
- 5 kiểu hù RIÊNG BIỆT (mapping §6.2): (1) ma trắng trôi, (2) chân dung hét trên tường, (3) tay zombie từ cửa tối, (4) bóng đen mắt vàng, (5) mặt xương lớn
- Cuối hành lang: nhạc chuyển nhẹ nhàng ấm áp (`warm`)
- Âm thanh: bước chân vang vọng (`footstep_echo`)

### 5.7 Cảnh 6 — Sinh nhật
- Chủ: **"Happy Birthday Yuniebel!"** → Mèo: **"Meow~"** → Chủ: **"Chúc Mừng Sinh Nhật!"**
- Nhiệm vụ: **"Hoàn thành nhiệm vụ: Tìm chủ nhân."**
- Nhạc vui piano nhẹ (`celebration`), tiếng nến cháy (`candle`), mèo kêu hạnh phúc (`happy_meow`)
- Text "Chúc Mừng Sinh Nhật!" xuất hiện → hiệu ứng sparkle + chuông nhỏ (`bell`)
- **Visual (C2-11)**: cảnh 6 KHÔNG có ảnh ref — spec quyết định: **chủ đứng cạnh bánh kem (không ôm mèo)**, mèo ngồi cạnh chủ; lò sưởi lửa; bánh kem 4 nến; sparkle; text "Happy Birthday Yuniebel!" + "Chúc Mừng Sinh Nhật!". END screen KHÔNG dùng emoji (C2-12) — vẽ bánh kem pixel + chữ "Chúc Mừng Sinh Nhật Yuniebel!"

## 6. Đặc tả visual (theo 5 ảnh tham khảo)

> Chi tiết chiếu theo `implementation/brief-visuals.md` — file này là **nguồn chuẩn** cho mọi vật thể/palette chưa liệt kê hết trong §6 (C2-10).

| Cảnh | Yêu cầu visual |
|------|----------------|
| Title | Trời xanh, mây, mặt trời, đồi cỏ, cây, bụi hoa, mèo đứng cạnh nút START |
| Vườn | Nhà hiên (tường be, mái đỏ, cửa gỗ), hàng rào trắng, cây, bụi, hoa, bóng đỏ; trời ĐỘNG: ngày xanh → hoàng hôn cam/tím → đêm sao (theo darkness) |
| Phòng khách | Sofa đỏ/cam + gối, thảm sọc be, tranh treo, đồng hồ tròn treo tường, kệ sách, **chậu cây xanh**, bàn trà, đèn tường (sconce), cửa tối |
| Bếp | Tủ trắng + tay nắm tối, lò + nồi, tủ lạnh, cửa sổ, vết máu LỚN đỏ + giọt anim, vùng tối có 2 mắt trắng sáng, bàn bếp |
| Ma ám | Tông tím/đen, ma XANH đầu lâu lớn chặn cửa giữa, đồng hồ quả lắc, chân nến, mạng nhện, ảnh nghiêng, sofa cũ, text nhiệm vụ "Phải đi qua phòng khác!" |
| Hành lang | Corridor gỗ tối, đuốc/nến tường, 5 vị trí hù với sprite khác nhau (ma trắng / chân dung hét / tay zombie / bóng mắt vàng / mặt xương), cửa hai đầu |
| Sinh nhật | Lò sưởi lửa, bánh kem 4 nến + kem phủ, chủ đứng cạnh, sparkle, text "Happy Birthday Yuniebel!" + "Chúc Mừng Sinh Nhật!" |
| GAME OVER | Nền tối đỏ, chữ "GAME OVER" lớn, dòng "Yuniebel đã đi vào bóng tối…", nút "Chơi lại" → reset về title |
| END | Nền ấm, chữ "Chúc Mừng Sinh Nhật Yuniebel!" (**không emoji** — vẽ bánh kem pixel, R4), nút "Chơi lại" → title |

## 6.1 Bảng Phase → Nhiệm vụ (canonical)

| Phase | Nhiệm vụ hiển thị |
|-------|-------------------|
| G_INIT | "Đuổi theo con bướm!" |
| G_CHASE | "Đuổi theo con bướm!" |
| G_DARK / G_DOOR | "Hãy vào nhà!" |
| L_SEARCH | "Tìm chủ nhân ở nhà bếp." |
| K_INIT / K_BLOOD | "Kiểm tra vết máu!" |
| K_CHOICE | "Kiểm tra vết máu!" (hộp lựa chọn 1/2 hiển thị) |
| H_INIT | "Tìm người chủ!" |
| H_BLOCK / H_EXIT | "Phải đi qua phòng khác!" |
| W_INIT / W_WALK | "Đi qua hành lang." |
| W_DONE | "Đã đến phòng ăn." |
| D_END | "Hoàn thành nhiệm vụ: Tìm chủ nhân." |

> Ghi chú chuyển phase (C2-17): `G_DARK→G_DOOR` khi mèo đứng trước cửa (x>790); `H_BLOCK→H_EXIT` khi mèo chạm cửa phụ (x<60). `TITLE`/`GAME_OVER`/`END` không hiển thị task.

## 6.3 Bảng Phase → Mood nhạc (canonical cho `audio.getMood()`, C2-06)

| Phase | Mood | Mô tả |
|-------|------|-------|
| TITLE | `calm-happy` | vui tươi nhẹ nhàng |
| G_INIT / G_CHASE | `garden-calm` | yên bình, vui |
| G_DARK / G_DOOR | `dusk-sad` | trầm, hơi buồn |
| L_SEARCH | `mystery` | nhẹ, bí ẩn |
| K_INIT / K_BLOOD / K_CHOICE | `kitchen-mystery` | căng thẳng bí ẩn |
| H_INIT / H_BLOCK / H_EXIT | `tense` | căng thẳng + thì thầm xa |
| W_INIT / W_WALK | `suspense` | hồi hộp |
| W_DONE | `warm` | nhẹ nhàng ấm áp |
| D_END | `celebration` | vui tươi piano nhẹ |
| GAME_OVER | `dusk-sad` | trầm |

## 6.2 Scare zone → kiểu hù (mapping cố định)

| Zone | Kiểu hù | Dấu |
|------|---------|-----|
| scare1 | Ma trắng ga trôi sau lưng | "!" |
| scare2 | Chân dung phụ nữ hét trên tường (tay vươn khỏi khung) | "!!" |
| scare3 | Tay zombie từ cửa tối | "!!!" |
| scare4 | Bóng đen mắt vàng cuối hành lang | "!?" |
| scare5 | Mặt xương sọ lớn | (jump scare cuối) |

## 7. Đặc tả kỹ thuật

- Giữ nguyên: canvas 480×270, 0 dependency, file:// + GitHub Pages, `window.__yuniebel`
- **Điều khiển (C2-02)**: `←/→/WASD` di chuyển mèo (lên/xuống dùng `↑/↓/W/S`), dialogue **tự advance** theo `dur` (Space/Enter để advance nhanh), lựa chọn bằng phím `1`/`2` **và** click nút, nút "Chơi lại"/"START" click được (Enter cũng được)
- **core.js**: thêm `dialogueQueue` (hàng đợi hội thoại tuần tự {text, dur, thought}), state `ghostBlocked` (đổi task sau knockback), text chuẩn mọi phase, cờ âm thanh (ting/drip/swoosh/whoosh/creak/… để game.js phát đúng 1 lần)
- **audio.js**: sequencer nhạc nền chiptune theo **audio clock** (`ctx.currentTime` lookahead — không phụ thuộc rAF, chống throttle tab ẩn, C1-16), đổi mood theo phase (bảng §6.3), fade; ambient (chim/gió/tích tắc/nhỏ giọt/creak/bước chân); **≥15 SFX** (C2-09): ting, flutter, meow, happy_meow, scared_meow, pain_meow, footstep_grass, footstep_echo, wind, bird, clock_tick, drip, whisper, whisper_far, rush, swoosh, whoosh, creak, jumpscare, candle, bell; **nút MUTE góc phải trên** (mặc định bật, C2-19); **resume AudioContext tại gesture đầu** (mousedown/keydown/click START — title "câm" tới gesture đầu, C2-15); **`getStats()` reset theo màn chơi hiện tại** (reset khi START/Chơi lại, C2-16)
- **sprites.js**: vẽ lại nền động (garden theo darkness), bếp, phòng khách, ma ám, hành lang, sinh nhật; sprite mới: ma xanh đầu lâu, ma trắng, chân dung hét, tay zombie, bóng mắt vàng, mặt xương, lò sưởi, bánh kem lớn, sparkle, đồng hồ
- **game.js**: render các visual mới, phát SFX theo cờ, hiển thị dialogue queue, scare visual riêng theo chỉ số, text "Chúc Mừng Sinh Nhật!" trong canvas ở cảnh 6
- **Test hook (debug API)**: `window.__yuniebel.debug` chỉ active khi URL có `?test=1` (game static, chấp nhận cheat — C1-15). API đầy đủ để chụp ảnh deterministic:
  - `setPhase(id)` — set phase, `setPlayer(x,y)` — vị trí mèo, `setDarkness(v)` — 0..1 (hoàng hôn/đêm), `setTimers({name:v})`, `setScareCount(n)`, `setScareZone(n|null)` (C2-04 — force hiển thị kiểu hù thứ n theo mapping §6.2), `setMessage(text,until)`, `setChoice(1|2)`, `setButterfly(x,y|null)`, **`freeze(true|false)`** — đóng băng `state.time` (mọi animation dựa state.time → ảnh chụp ổn định, C1-02/C1-03)
  - `audio.getMood()` — mood nhạc hiện tại (tên canonical §6.3); `audio.getStats()` — counter từng SFX đã phát trong màn chơi hiện tại (kiểm chứng âm thanh, C1-09/C2-16)

## 8. Tiêu chí chấp nhận (AC)

- **AC-1**: **13 câu thoại** khớp 100% `implementation/brief-scenario.md` (bảng §5 + test)
- **AC-2**: Mọi nhiệm vụ khớp bảng canonical §6.1; task đổi sang "Phải đi qua phòng khác!" **sau lần knockback đầu tiên** (vĩnh viễn — C1-14)
- **AC-3**: Nhạc nền theo mood từng cảnh theo bảng §6.3 (tên canonical cho `audio.getMood()`), đổi mood đúng thời điểm (bắt bướm → `dusk-sad`; zone 5 xong → `warm`); kiểm chứng qua `audio.getMood()` + `audio.getStats()` (C1-09/C2-06)
- **AC-4**: ≥15 SFX hoạt động và được assert bằng `audio.getStats()` (counter màn chơi hiện tại): ting, flutter, meow, happy_meow, scared_meow, pain_meow, footstep_grass, footstep_echo, wind, bird, clock_tick, drip, whisper, whisper_far, rush, swoosh, whoosh, creak, jumpscare, candle, bell (C2-05)
- **AC-5**: Visual cảnh 1 động ngày→hoàng hôn→đêm; nhà/hàng rào/cây/bụi/hoa theo ảnh ref; **đèn hiên sáng theo darkness, cửa nhà mở tối om khi hoàng hôn** (C2-10)
- **AC-6**: Bếp có tủ trắng/lò/tủ lạnh/vết máu lớn + giọt anim/mắt sáng trong tối
- **AC-7**: Phòng khách ma ám có ma xanh đầu lâu lớn chặn cửa giữa; **dầm gỗ, mạng nhện, glow xanh** (C2-10); knockback + đổi task sau lần đầu; cửa phụ trái thoát được
- **AC-8**: Hành lang 5 kiểu hù RIÊNG BIỆT theo mapping §6.2, đủ 5 lần, counter 0→5, nhạc ấm cuối
- **AC-9**: Cảnh sinh nhật có lò sưởi + bánh kem + text "Chúc Mừng Sinh Nhật!" + sparkle + chuông
- **AC-10**: Chọn 2 → swoosh + pain meow → GAME OVER; chọn 1 → chạy gấp gáp → phòng khách ma ám
- **AC-11**: Test chụp ảnh màn hình **17 phase/scene** (bảng §8.1) bằng `locator('canvas').screenshot()` — clip đúng canvas 480×270 (C2-13), có bảng đối chiếu brief (đạt/không đạt)
- **AC-12**: `test/brief/README.md` hướng dẫn đặt ảnh ref; so sánh pixel dùng `toHaveScreenshot` nhưng **`test.skip` khi thiếu ảnh ref** (C1-12) + ghi kết quả vào `test/brief/COMPARISON.md`
- **AC-13**: Toàn bộ test chạy pass: `node test/core.test.js` + `node test/smoke.test.js` + `npx playwright test` (e2e + visual)
- **AC-14**: Chạy được offline file://, không lỗi console; **2 test chơi thật không hook** (title→sinh nhật, title→game over) — "không hook" = không gọi debug setter, **được phép đọc state** (phase/task) để điều hướng input (C2-14)

## 8.1 Bảng chụp ảnh deterministic (AC-11 — 17 ảnh)

| # | Ảnh (tên file) | Debug set trước khi chụp | Dialogue |
|---|----------------|--------------------------|----------|
| 1 | `title.png` | phase TITLE, freeze | — |
| 2 | `garden-day.png` | phase G_INIT, freeze (mèo tại sân) | có (chủ gọi, dùng `setMessage`) |
| 3 | `garden-dusk.png` | phase G_CHASE, **setDarkness(0.5)**, **setButterfly(trước mặt mèo)**, freeze (R8) | — |
| 4 | `garden-night.png` | phase G_DARK, **setDarkness(1)**, freeze | — |
| 5 | `living.png` | phase L_SEARCH, freeze | — |
| 6 | `kitchen-blood.png` | phase K_BLOOD, freeze (mèo cạnh vết máu) | — |
| 7 | `kitchen-choice.png` | phase K_CHOICE, freeze (hộp lựa chọn hiển thị) | — |
| 8 | `haunted-ghost.png` | phase H_INIT, freeze (ma hiện, task "Tìm người chủ!") | — |
| 9 | `haunted-block.png` | phase H_BLOCK, freeze (task "Phải đi qua phòng khác!") | — |
| 10 | `hallway-scare1.png` | phase W_WALK, **setScareZone(1)**, freeze | — |
| 11 | `hallway-scare2.png` | phase W_WALK, **setScareZone(2)**, freeze | — |
| 12 | `hallway-scare3.png` | phase W_WALK, **setScareZone(3)**, freeze | — |
| 13 | `hallway-scare4.png` | phase W_WALK, **setScareZone(4)**, freeze | — |
| 14 | `hallway-scare5.png` | phase W_WALK, **setScareZone(5)**, freeze | — |
| 15 | `birthday.png` | phase D_END, freeze (text "Chúc Mừng Sinh Nhật!" + sparkle) | — |
| 16 | `gameover.png` | phase GAME_OVER, freeze | — |
| 17 | `end.png` | phase END, freeze | — |

## 9. Ràng buộc

- KHÔNG thêm dependency/build step (trừ devDependency @playwright/test đã có)
- KHÔNG dùng ảnh ngoài (sprite vẽ bằng canvas primitives, giữ phong cách pixel art)
- Không sửa backend AIOS
