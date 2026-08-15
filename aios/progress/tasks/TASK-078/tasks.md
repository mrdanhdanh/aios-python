# TASK-078 — Tasks breakdown

> Chuỗi hard gate: plan ✅ → spec ✅ → critique-1 ✅ (17 vấn đề resolved) → critique-2 ✅ (19 vấn đề resolved) → tasks → review → implement → test → evaluate

## P0 — Core logic + text canonical (AC-1, AC-2, AC-10, AC-14)
- [ ] Viết lại `src/core.js`: state machine đầy đủ phase (TITLE, G_INIT, G_CHASE, G_DARK, G_DOOR, L_SEARCH, K_INIT, K_BLOOD, K_CHOICE, H_INIT, H_BLOCK, H_EXIT, W_INIT, W_WALK, W_DONE, D_END, GAME_OVER, END)
- [ ] `dialogueQueue` — 13 câu thoại khớp 100% brief-scenario.md (kể cả dấu …/~/?!)
- [ ] Bảng PHASES: task text canonical §6.1 (có dấu chấm cuối "Tìm chủ nhân ở nhà bếp.")
- [ ] Collision AABB + slide (walls từng scene)
- [ ] Bướm AI: xuất hiện khi mèo x>780, waypoint cố định 3 điểm, bắt khi chạm bán kính 12px / đứng 40px ≥1s
- [ ] Knockback ma (H_BLOCK): đổi task sau lần đầu vĩnh viễn, cửa phụ trái thoát
- [ ] Scare zones 5 kiểu theo mapping §6.2, mỗi zone trigger 1 lần, counter 0→5
- [ ] Lựa chọn 1/2: phím 1/2 + click; chọn 1 → rush → H; chọn 2 → swoosh + pain_meow → GAME_OVER
- [ ] Cờ âm thanh (ting/ting lúc bướm, drip, swoosh, whoosh, creak...) để game.js phát 1 lần
- [ ] Debug API: setPhase, setPlayer, setDarkness, setTimers, setScareCount, setScareZone, setMessage, setChoice, setButterfly, freeze (chỉ khi `?test=1`)

## P1 — Visual 6 cảnh theo 5 ảnh tham khảo (AC-5..AC-9)
- [ ] `src/sprites.js`: palette hằng số (theo brief-visuals.md — mục "Tổng hợp palette chính", R9)
- [ ] Title: trời gradient + dithering, mặt trời hào quang, mây trắng trôi, núi/đồi/bụi cây/nước, nút START xanh lá viền đen chữ vàng cam, mèo cạnh nút
- [ ] Garden: nhà gỗ hiên mái, hàng rào trắng, cửa mở, cây, bụi, hoa, bóng đỏ, mèo; trời động theo darkness (ngày xanh → hoàng hôn cam/tím + đèn hiên + cửa tối → đêm sao)
- [ ] Living: sofa đỏ cam + gối, thảm sọc be, tranh, đồng hồ tròn, kệ sách, chậu cây, bàn trà, đèn sconce, cửa tối
- [ ] Kitchen: tủ trắng tay nắm tối, lò + nồi, tủ lạnh, vết máu LỚN + giọt anim, vùng tối 2 mắt trắng, bàn bếp
- [ ] Haunted: tông tím/đen, dầm gỗ, mạng nhện, ma XANH đầu lâu lớn + aura, đồng hồ quả lắc, chân nến, ảnh nghiêng, sofa cũ, cửa chính + cửa phụ
- [ ] Hallway: corridor gỗ tối, đuốc/nến, 5 sprite hù khác nhau (ma trắng, chân dung hét, tay zombie, bóng mắt vàng, mặt xương), cửa 2 đầu
- [ ] Birthday: lò sưởi lửa, bánh kem 4 nến, chủ đứng cạnh, mèo ngồi, sparkle, text 2 dòng
- [ ] GAME OVER (tối đỏ) + END (ấm, không emoji)
- [ ] Sprite mèo 4 hướng + anim chạy; sprite chủ nhân (tóc nâu áo xanh); bướm vàng anim cánh; hiệu ứng fade, flash scare, sparkle, dấu !/!!/!!!/!?
- [ ] `index.html` + `style.css`: hộp thoại đen viền vàng, hộp task, hộp lựa chọn, màn hình overlay, nút MUTE, d-pad mobile

## P2 — Audio WebAudio synth (AC-3, AC-4)
- [ ] `src/audio.js`: sequencer nhạc nền theo audio clock (ctx.currentTime lookahead), 10 mood theo §6.3, fade chuyển mood
- [ ] Ambient: chim, gió, tích tắc, nhỏ giọt, creak, bước chân
- [ ] 21 SFX: ting, flutter, meow, happy_meow, scared_meow, pain_meow, footstep_grass, footstep_echo, wind, bird, clock_tick, drip, whisper, whisper_far, rush, swoosh, whoosh, creak, jumpscare, candle, bell
- [ ] Nút MUTE (mặc định bật), resume AudioContext tại gesture đầu
- [ ] `audio.getMood()` + `audio.getStats()` (counter màn chơi hiện tại, reset khi START/Chơi lại)

## P3 — Test + chụp ảnh đối chiếu brief (AC-11..AC-13)
- [ ] Cập nhật `playwright.config.js` (R10): testMatch gồm e2e + visual.spec.js, timeout project 120s cho AC-14, launch args `--autoplay-policy=no-user-gesture-required`
- [ ] `test/core.test.js`: state machine, text thoại/task (13 câu, bảng §6.1), collision, scare 5/5, choice 1/2, debug API
- [ ] `test/smoke.test.js`: jsdom load không lỗi, script classic
- [ ] `test/e2e.spec.js`: Playwright — 2 test chơi thật không hook (title→sinh nhật, title→game over) + assert mood đúng phase + SFX stats
- [ ] `test/visual.spec.js`: chụp 17 ảnh theo bảng §8.1 bằng `locator('canvas').screenshot()` → `test-results/shots/`; copy ảnh vào `aios/progress/tasks/TASK-078/shots/`; **test freeze determinism** (chụp 2 lần cách 500ms với freeze → pixel giống hệt, R1)
- [ ] `test/brief/README.md` + `COMPARISON.md`: hướng dẫn đặt ảnh ref, toHaveScreenshot skip khi thiếu, bảng đối chiếu kết quả
- [ ] Đối chiếu ảnh chụp vs brief-visuals.md + brief-scenario.md → ghi bảng đạt/không đạt vào `test.md`

## Evaluate
- [ ] `evaluation.md`: đối chiếu 14 AC, bài học, đề xuất
- [ ] Cập nhật PROGRESS.md + LOG.md + STATS.md + commit
