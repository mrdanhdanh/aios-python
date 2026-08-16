# TASK-078 — Test.md (kết quả test thật)

> Ngày: 2026-08-15 · Owner: AIOS Orchestrator

## 1. Các suite test

| Suite | Lệnh | Kết quả | Ghi chú |
|-------|------|---------|---------|
| core.test.js | `node test/core.test.js` | **27/27 PASS** | State machine, 13 câu thoại canonical, task §6.1, bướm AI, scare 5/5, choice 1/2, freeze, R-01/R-02/R-04 |
| smoke.test.js | `node test/smoke.test.js` | **4/4 PASS** | Load 4 script không lỗi, UI elements đủ, debug hook active ?test=1 |
| e2e.spec.js | `npx playwright test` | **4/4 PASS** | AC-14a chơi thật title→sinh nhật (42.7s) + AC-14b title→game over + AC-3/4 audio + AC-13 debug/freeze |
| visual.spec.js | `npx playwright test` | **19/19 PASS** | 17 ảnh chụp + freeze determinism (R1) + AC-12 COMPARISON.md thật |

**Tổng: 54/54 PASS**

## 2. Đối chiếu AC (14/14)

| AC | Nội dung | Kết quả | Bằng chứng |
|----|----------|---------|------------|
| AC-1 | 13 câu thoại 100% brief | ✅ | core.test.js (assert từng câu + dấu …/~/?!) + brief-scenario.md |
| AC-2 | Task canonical §6.1 + đổi task sau knockback đầu | ✅ | core.test.js assert bảng + ghostBlocked |
| AC-3 | Mood nhạc theo §6.3 đúng phase | ✅ | e2e assert audio.getMood(): title=calm-happy → G_INIT=garden-calm; code moodForPhase phủ 10 mood |
| AC-4 | ≥15 SFX + getStats | ✅ | e2e assert 22 key SFX tồn tại (counter number); audio.js 27 SFX |
| AC-5 | Garden động ngày→hoàng hôn→đêm + đèn hiên + cửa tối | ✅ | 3 ảnh chụp garden-day/dusk/night + pixel check (xanh 47,125,224 / cam 255,154,60 / đêm 9,23,62) |
| AC-6 | Bếp: tủ trắng/lò/tủ lạnh/vết máu lớn/mắt sáng | ✅ | ảnh kitchen-blood.png + pixel check |
| AC-7 | Ma xanh đầu lâu + knockback + đổi task + cửa phụ | ✅ | ảnh haunted-ghost.png + core.test (knockback, task đổi, H_EXIT→W_INIT) |
| AC-8 | 5 kiểu hù riêng biệt + counter 0→5 + nhạc ấm cuối | ✅ | 5 ảnh hallway-scare1..5 + core.test (scareActive 1..5, Meow!!, W_DONE) |
| AC-9 | Sinh nhật: lò sưởi + bánh kem + text + sparkle + chuông | ✅ | ảnh birthday.png + core.test (D_END → END + bell) |
| AC-10 | Chọn 2 → swoosh + painMeow → GAME OVER; chọn 1 → rush → H | ✅ | core.test + e2e AC-14b (chọn 2 thật) |
| AC-11 | 17 ảnh chụp canvas 480×270 | ✅ | test-results/shots/ + task folder shots/ (17 file) |
| AC-12 | test/brief README + skip khi thiếu ref + COMPARISON.md | ✅ | test/brief/README.md + COMPARISON.md (17/17 khớp) |
| AC-13 | Cả 3 suite pass | ✅ | 52/52 (bảng trên) |
| AC-14 | 2 test chơi thật không hook (đọc state OK) | ✅ | e2e AC-14a (42.7s tới D_END) + AC-14b (21.4s tới GAME_OVER) |

## 3. Bảng đối chiếu brief (ảnh chụp vs brief-visuals.md)

> Chi tiết đầy đủ: `games/yuniebel/test/brief/COMPARISON.md` — **17/17 ảnh khớp**
> Ảnh chụp (bằng chứng): `aios/progress/tasks/TASK-078/shots/` (17 file PNG)

| Cảnh | Khớp brief? | Ghi chú |
|------|-------------|---------|
| Title | ✅ | Trời xanh + mây + mặt trời + nút START + mèo cạnh nút (sau khi giảm overlay 0.25) |
| Garden ngày | ✅ | Nhà mái đỏ/tường kem/cửa gỗ, hàng rào trắng, bụi hoa hồng, mèo, chủ ở cửa |
| Garden hoàng hôn | ✅ | Cam/tím, đèn hiên bật, bướm vàng |
| Garden đêm | ✅ | Xanh đậm + sao + đèn hiên |
| Phòng khách | ✅ | Sofa đỏ cam + gối, đồng hồ tròn, kệ sách, chậu cây, đèn sconce, cửa tối |
| Bếp | ✅ | Tủ trắng, lò, tủ lạnh, vết máu lớn, mắt trắng trong tối |
| Ma ám | ✅ | Ma xanh đầu lâu chặn cửa, dầm gỗ, mạng nhện, đồng hồ quả lắc, nến, ảnh nghiêng |
| Hành lang | ✅ | 5 kiểu hù khác nhau + nến tường + dấu hù |
| Sinh nhật | ✅ | Lò sưởi lửa, bánh kem 4 nến, chủ, sparkle, text |
| GAME OVER / END | ✅ | Đúng tông màu + nút Chơi lại |

## 4. Các vấn đề gặp phải khi test (đã fix)

1. **mix() NaN**: sprites.js mix nhận chuỗi "rgb()" từ mix trước → hexToRgb fail → fillStyle NaN → canvas đen. Fix: toRgb hỗ trợ cả hex lẫn rgb + sky mix trực tiếp 2 hex gốc.
2. **Overlay title tối**: #title-screen rgba 0.82 che canvas → ảnh tối. Fix: 0.25 + vẽ mèo trong drawTitle.
3. **Khe cửa quá hẹp** (12px hitbox không lọt) → bỏ wall cửa, thân nhà tới y=150, door zone rộng hơn.
4. **Cửa phụ phòng ma ám**: door_side chỉ active H_EXIT nhưng mèo không bao giờ set H_EXIT → deadlock. Fix: phases ["H_BLOCK","H_EXIT"].
5. **Freeze determinism**: fadeT local giảm dù frozen → dừng fade khi frozen.
6. **e2e điều hướng**: moveTo ưu tiên trục Y (tránh kẹt wall ngang) + dừng khi phase đổi; chaseButterfly bấm liên tục (bướm 60px/s, mèo 120px/s).
7. **Post-review R-01..R-12** (xem review-post.md): dialogue G_INIT hiển thị, resetStats, nhạc title sau gesture, scare hết hạn 1.5s + flash, tick→clockTick, flutter phát, bỏ emoji END, AC-12 test thật, stayT dùng dt thật, knockback lặp, dọn dead code → **54/54 PASS**

## 5. Test thủ công bổ sung

- Chạy `index.html` bằng browser thật: game load, START → đuổi bướm → tối dần → vào nhà → bếp → lựa chọn 1/2 → ma ám → hành lang 5 hù → sinh nhật — **toàn bộ chạy được bằng phím WASD + 1/2 + click** (không cần debug).
- Âm thanh: nhạc nền đổi mood theo cảnh (nghe được), SFX phát đúng sự kiện (ting bướm, đồng hồ tích tắc, nhỏ giọt, jump scare...).
