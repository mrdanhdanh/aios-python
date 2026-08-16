# TASK-079 — Fix: mèo biến mất sau khi bấm START (scale mismatch world vs logical grid)

## 1. Mục tiêu

Sửa bug nghiêm trọng của TASK-078: sau khi bấm START, nhân vật mèo (Yuniebel) **biến mất khỏi màn hình** và mọi scene gameplay không hiển thị đúng người/vật so với vị trí tương tác (walls/zones). Kết quả mong muốn: mèo hiển thị rõ ràng, chạy được xuyên suốt 6 cảnh, background khớp với vị trí tường/cửa/vùng tương tác.

## 2. Nguyên nhân gốc (đã chứng minh bằng screenshot)

- `sprites.js`: toàn bộ sprite/background vẽ trên **grid logical 160×90**, mọi hàm `R/P` nhân `GX=3` → canvas 480×270. Khai báo: `// Pixel grid: vẽ logical 160×90, scale 3 → 480×270`.
- `core.js`: map/world dùng tọa độ **world gấp 3** (GARDEN/HALLWAY `w: 960`, các scene khác `w: 480`; spawn, walls, zones, butterflyWp đều ở đơn vị world).
- `game.js`: `drawPlayer` gọi `S.drawCat(ctx, p.x - cx, p.y, ...)` với `p.x` ở đơn vị **world** nhưng `drawCat` mong đợi **logical** → mèo vẽ tại x ≈ world×3 → ví dụ spawn `x=320` → vẽ tại `960px` — ngoài canvas 480px → **không bao giờ thấy mèo**.
- Background vẽ cố định 160 logical trong khi walls/zones nằm ở world 0..960 → nhà (wall x 800..960) không bao giờ nằm trong background → thế giới không nhất quán.
- Test 54/54 "PASS" vì: test logic (`core.test.js`) chỉ kiểm tra state không kiểm tra render; test visual (`visual.spec.js`) **không có ảnh ref trong `test/brief/`** (chỉ COMPARISON.md — `fs.existsSync(ref)` false → bỏ qua `toHaveScreenshot`) nên "17/17 khớp" thực chất là so với chính ảnh vừa chụp, không phải so brief.

## 3. Giải pháp: chuyển toàn bộ core về logical grid (chia 3)

Thiết kế đúng đắn nhất: **1 đơn vị logic = 1 pixel sprite**. Map rộng:
- GARDEN: `960×270` → `320×90` (2 màn hình, camera scroll ngang)
- HALLWAY: `960×270` → `320×90` (2 màn hình, camera scroll)
- LIVING / KITCHEN / HAUNTED / BIRTHDAY: `480×270` → `160×90` (= GW — vừa khít 1 màn hình, camera đứng yên)

### 3.1 `src/core.js`

| Hằng số | Cũ (world) | Mới (logical) |
|---|---|---|
| `WALK_SPEED` | 120 | 40 |
| `BUTTERFLY_SPEED` | 60 | 20 |
| `KNOCKBACK` | 40 | 13 |
| `DARK_RECT` | (20,20,92,100) | (7,7,31,33) — khớp comment sẵn trong sprites.js |
| `BUTTERFLY_CATCH` | 12 | 4 (cosmetic — hằng không dùng trong logic, `butterflyHit` dùng cứng 8/16; giữ nguyên cho khớp tinh thần) |
| `BUTTERFLY_STAY` | 40 | 13 |
| `PW/PH/HBX/HBW/HBY/HBH` | 16/16/3/10/2/12 | giữ nguyên giá trị (sprite mèo 16×16 logical, hitbox 10×12 lệch (3,2)) |

Các scene (spawn, walls, zones, butterflyWp — tất cả chia 3, làm tròn):

- **GARDEN** `w:320 h:90`, spawn `(107,70)`, butterflyWp `(167,40),(217,30),(180,63)`; **spawn bướm `(233,47)`** — code thật nằm trong nhánh `G_INIT` của `updateGame` (C3-P3-3), kích hoạt khi `player.x > 260`
  - walls: `(267,7,53,43)` nhà, `(67,62,8,5)` bụi1, `(117,33,7,5)` bụi2, `(207,85,9,4)` bụi3 (đẩy xuống 85 để không chặn đường mèo y=70; đáy 89 ≤ 90 — giữ h=4), `(13,50,7,4)` bụi4, `(230,13,6,23)` cây
  - zones: `{door, 284,48,11,20, phases:[G_INIT,G_DOOR]}`
  - trigger bướm: `player.x > 260`
- **LIVING** `w:160 h:90`, spawn `(113,63)`
  - walls: `(10,53,30,15)` sofa, `(63,67,23,4)` bàn trà, `(127,70,10,17)` kệ
  - zones: `{door_kitchen, 3,30,11,20, phases:[L_SEARCH]}`
- **KITCHEN** `w:160 h:90`, spawn `(80,73)` (hitbox bottom 87 ≤ 90 — tránh kẹt biên P1-1; vẫn chồng blood zone để K_INIT auto-fire)
  - walls: `(100,47,30,15)` bàn bếp, `(127,7,33,43)` tủ bếp phải
  - zones: `{blood, 50,78,40,8}`, `{dark = DARK_RECT}`, `{door_out, 149,43,11,20}`
- **HAUNTED** `w:160 h:90`, spawn `(90,63)` (hitbox x 93..103 — tránh wall bàn (67,68,20,4) P1-2)
  - walls: `(10,53,30,15)` sofa cũ, `(67,68,20,4)` bàn
  - zones: `{door_front, 143,33,15,33}`, `{door_side, 2,30,11,20}`
- **HALLWAY** `w:320 h:90`, spawn `(20,45)`
  - walls: `(0,33,9,23)` cửa vào đóng
  - scareZones: `(47,33,30,20),(100,33,30,20),(153,33,30,20),(207,33,30,20),(260,33,30,20)`
  - zones: `{door_dining, 302,33,14,20}`
- **BIRTHDAY** `w:160 h:90`, spawn `(80,67)`
  - walls: `(47,47,67,20)` bàn bánh kem

### 3.2 `src/sprites.js`

- `sky(ctx, darkness, time, w)`: thêm tham số width (mặc định GW); mở rộng vẽ nền theo `w`, sao trải theo `sx = (i*37+13) % (w-10)` cho map 320.
- `drawGarden(ctx, state, time, cx)`: mở rộng sang **320×90** — cỏ/hàng rào/đường mòn trải 0..320; cây lớn tại (230,13); NGÔI NHÀ tại **x 267..320** (khớp wall): thân (267,26,53,24), mái 2-3 lớp (264..323, y 16..26), cửa gỗ (285,42,9,8) (khớp door zone 284,48), cửa sổ (271,32) & (300,32), hiên (265,49,55,2), đèn hiên **(287,38)** khi `d>0.15` (thống nhất overlay — P3-4/C2-P3-1); chủ nhân `drawOwner(ctx, 288, 44, 0, 1)` khi G_INIT; bụi cây vẽ đúng 4 wall + hoa rải rác; quả bóng đỏ giữ.
- **BẮT BUỘC bọc `ctx.save(); ctx.translate(-cx*S.GX, 0); ... ctx.restore();`** quanh toàn bộ phần vẽ map trong drawGarden và drawHallway (C2-P1-2) — không restore → transform rò rỉ làm drawPlayer lệch kép, clearRect xóa lệch, overlay screen-space sai tọa độ (đúng class bug gốc). **`sky()` phải nằm TRONG translate** (R3) — mặt trời/mây/sao cuộn theo camera (sao trải 0..w−10; khi cam=160 viewport 160..320 vẫn có sao).
- `drawLiving`: sofa vẽ tại (10,52) khớp wall, bàn trà (63,66) khớp wall (63,67), kệ (126,70,12,17) khớp wall (127,70,10,17), giữ chậu cây/cửa tối/đồng hồ/tranh.
- `drawKitchen`: vết máu vẽ tại (50,78,40,8) + nhánh (54,86,26,3) + chấm tối (66,86,6,2) (tất cả y ≤ 90 — C2-P3-2) khớp blood zone; **vùng tối vẽ tại (7,7,31,33) chính xác = DARK_RECT + 2 mắt sáng (17,19)/(23,19)** (P2-8); tủ lạnh (128,12,16,30) khớp wall tủ (127,7,33,43); bàn bếp (100,47,30,3) + chân (102,50,2,12),(126,50,2,12) khớp wall; cửa phải (149,40,4,20) khớp door_out; K_CHOICE highlight tại (50,78,40,8); **tủ bếp trắng trái (0,10,80,22) GIỮ NGUYÊN** (C2-P3-6: mèo đi tới vùng tối vẽ đè lên — chấp nhận, background trang trí).
- `drawHaunted`: cửa chính vẽ tại (143,20,12,40) khớp door_front; ma xanh `drawGhostSkull(ctx, 139, 16, time, state)`; glow (143,34,12,20); cửa phụ (0,40,4,20); giữ sofa/bàn/đồng hồ/ảnh nghiêng.
- `drawHallway(ctx, state, time, cx)`: mở rộng **320×90** — tường 0..320, sàn, 11 đuốc (`8+i*29`), cửa trái (0,40,4,20), cửa phải (316,40,4,20); 5 kiểu hù vẽ tại vị trí **tuyệt đối trong map** đảm bảo luôn trong viewport khi kích hoạt: scare1→130, scare2→**160** (P2-9: trigger p.x≈87 → cam≈10 → screen 150), scare3→210, scare4→260, scare5→300.
- `drawGarden(ctx, state, time, cx)` và `drawHallway(..., cx)` **nhận tham số camera `cx`** (P1-4): bên trong dùng `ctx.translate(-cx*GX, 0)` (hoặc trừ offset từng hình) trước khi vẽ toàn bộ map 320 → phần ngoài viewport 160 bị clip tự nhiên, đảm bảo nền cuộn theo mèo.
- `drawTitle`, `drawBirthday`, `drawGameOver`, `drawEnd`: không đổi (đã logical).

### 3.3 `src/game.js`

- `camX()`: **thay TOÀN BỘ thân hàm** (R2): giữ guard `if (!sc) return 0;` (chống crash scene TITLE — `SCENES.TITLE` undefined), **BỎ guard cũ `sc.w <= CW`** (CW=480 sẽ giết camera: 320 ≤ 480 → luôn trả 0). Công thức mới: viewport logical = 160 → `return Math.max(0, Math.min(state.player.x - 80 + 3, sc.w - 160));` (scene w=160 → clamp về 0 ✓).
- `drawScene` truyền `cx` vào `S.drawGarden(ctx, state, time, cx)` và `S.drawHallway(ctx, state, time, cx)` (P1-4).
- **XÓA dòng `S.drawBlood(ctx, 68, 66, state.time)`** trong drawScene KITCHEN (P1-5) — `drawKitchen` đã tự vẽ máu tại (50,78) (tránh 2 lớp máu chồng nhau).
- Đèn hiên overlay trong drawScene: `var lx = (287 - cx) * S.GX;` và **`ctx.fillRect(lx - 12, 38 * S.GX, 24, 30)`** (thống nhất y=38 với sprite — R5; cũ 36*S.GX lệch 2px).
- Debug hook `setButterfly` default: `(700,150)` → `(233,50)` (P2-1).
- Các chỗ khác (drawPlayer, drawButterfly, scare marks, flash) đã đúng đơn vị logical — không đổi.

### 3.4 Test

- `test/core.test.js`: mọi tọa độ player chia 3 (790→263, 860→287, 20→7, 190→63, 40→13, 430→143, 10→3, 160→53, 910→303, 0 giữ; y tương tự 150→50, 160→53, 100→33, 240→80, 40→13, 130→43). Riêng: test xuyên tường nhà `(263,30)` (hitbox y 32..44 chồng wall y 7..50 — P2-7); test chạm máu `(63,73)` (hitbox bottom 87 ≤ 90, hợp lệ — P3-3).
- `test/e2e.spec.js`: **helper `moveTo` hai tầng** (R1 — tránh oscillation: bước 120ms ≈ 4.7px > tolerance 2 → lặp vô hạn; và dải hạ cánh [47.3,48) chạm wall nhà): dừng khi `|dx| < 2 && |dy| < 2`; ưu tiên Y: `|dy| > 12` → hold 120ms, `|dy| > 2` → hold **40ms** (≈1.6px < 2 → hội tụ |dy'| ≤ 2); sau khi Y hội tụ → X hai tầng tương tự. Dải hạ cánh y ∈ [48,52] ⊂ [48,66] (thoát wall nhà đáy 50 + chạm door zone y 48..68) ✓. Verify an toàn mọi target: (7,20) dừng y≈20.6 hitbox 22.6..34.6 clear sofa ✓; (3,20) ✓; (20,20) ✓; (147,50) ✓; (310/312,45) ✓. `moveTo` chia 3: (800,210)→**(271,70)** (C3-P2: cửa sổ dừng (261..271) luôn > ngưỡng trigger 260 — margin dương; cũ (267,70) dừng (257..267) chạm biên 260 → flaky spawn bướm), (865,178)→**(288,50)** (C2-P2-1/C3-P1: an toàn khi kết hợp hai tầng — từ mọi catch y → hội tụ 48..52), (20,110)→**(7,20)** (P1-3: lối trên sofa — chạm door_kitchen (3,30,11,20)), (60,60)→(20,20), (440,150)→(147,50), (10,110)→**(3,20)** (P1-3: tương tự HAUNTED), (930,135)→(310,45), (935,135)→(312,45). Cập nhật comments: "mèo 120px/s đuổi 60px/s" → 40/20 (P3-2), "x>780" → "x>260" (C3-P3-2). **Áp dụng (288,50) cho CẢ AC-14a lẫn AC-14b** (C2-P2-1).
- `test/e2e.spec.js`: **thêm test AC-2** — hold "d" 1s → `player.x` tăng (P2-2).
- `test/visual.spec.js`: `setPlayer` chia 3: garden-day (107,70), garden-dusk (153,53) + butterfly (160,43), garden-night (133,57), living (107,63), kitchen **(73,70) — áp dụng cho CẢ 2 shot kitchen-blood + kitchen-choice** (C3-P3-1), haunted **(90,63) — áp dụng cho CẢ 2 shot haunted-ghost + haunted-block** (C3-P3-1), hallway (50/100/153/207/263, 45), birthday (80,67), **R1-determinism test setPlayer(320,190)→(107,63)** (C3-P3-1).
- `test/smoke.test.js`: không chạm tọa độ — không đổi.

## 4. Phạm vi

- **Trong**: `games/yuniebel/src/core.js`, `src/sprites.js`, `src/game.js`, `test/core.test.js`, `test/e2e.spec.js`, `test/visual.spec.js`.
- **Ngoài**: index.html, style.css, audio.js, smoke.test.js, logic hội thoại/task/âm thanh, GitHub Pages deploy.
- Không thay đổi hành vi gameplay (thứ tự phase, thoại, scare, choice giữ nguyên).

## 5. Tiêu chí chấp nhận (Acceptance Criteria)

- **AC-1**: Sau START, mèo hiển thị trên màn hình GARDEN tại spawn (107,70) — verify pixel: canvas region **(231..279, 210..258)** chứa ≥ 30 pixel màu `#f5a623` (`catBody`) (P3-1 + C2-P1-1: cam=30 tại spawn → screen x 77 → canvas 231..279).
- **AC-2**: Mèo di chuyển được bằng WASD; nhấn phải 1s → tọa độ x tăng (test e2e mới — P2-2).
- **AC-3**: Có thể chơi hết game title→sinh nhật và title→game over (2 test e2e thật không hook) — PASS.
- **AC-4**: Background khớp walls: nhà vẽ tại x 267..320 trùng wall nhà; cửa door zone (284,48) nằm trong nhà vẽ; bụi cây/cây vẽ trùng 4 wall GARDEN (verify bằng visual test pixel — P2-3/P2-6).
- **AC-5**: Cả 17 shot visual (scene + 5 scare) đều chụp được, `img.length > 1000`, và **mèo hiện diện** trong ít nhất các shot có player (garden-day, living, kitchen, haunted, hallway, birthday) — check pixel `catBody` trong shot.
- **AC-6**: `node test/core.test.js` — toàn bộ test PASS (27/27) sau khi đổi tọa độ.
- **AC-7**: `node test/smoke.test.js` PASS (4/4).
- **AC-8**: `npx playwright test` — toàn bộ e2e + visual PASS.
- **AC-9**: Không crash console/pageerror trong mọi test.
- **AC-10**: Camera scroll hoạt động (P2-6/C2-P2-6): visual test — GARDEN: `setPhase("G_INIT")` + `setPlayer(300,50)` + `freeze(true)` → pixel `wallCream`/`roofRed` xuất hiện trong nửa phải canvas (nhà hiện khi cam=160); HALLWAY: `setPhase("W_WALK")` + `setPlayer(300,45)` + **`setScareZone(5)`** + `freeze(true)` (C2-P3-5) → pixel tường `#17131f` và skull scare (skull color) hiển thị trong canvas.

## 6. Rủi ro & giảm thiểu

- **Bụi cây chặn đường mèo** (GARDEN): bụi3 đẩy xuống y=85 (h=4, đáy 89 ≤ 90); bụi khác nằm ngoài tuyến di chuyển y=70 — e2e chơi thật sẽ phát hiện nếu kẹt (đã tính hitbox 10×12 lệch (3,2) cho từng wall: bụi1 y 62..67, bụi2 y 33..38, bụi4 y 50..54 — mèo hitbox 72..84 ở y=70 không chạm).
- **Camera mới sai** → mèo mất lần nữa: AC-1/AC-5/AC-10 verify bằng pixel thật, không chỉ logic.
- **Vị trí scare ngoài viewport**: đặt 130/160/210/260/300 với cam max = 160 (sc.w−160): scare1 cam 0 → screen 130; scare2 cam≈10 → 150; scare3 cam 63..103 → screen 107..147 (C2-P3-3); scare4 cam 117..160 → 100..143; scare5 cam 160 → 140 — tất cả ≥ 0 (P2-9/P2-10/C2-P3-3).
- **Test cũ "màu xanh"**: bổ sung AC-4 (visual pixel test tọa độ khớp) + AC-5/AC-10 (pixel check) để không tái phát.
