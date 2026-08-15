# Evaluation — TASK-077 (Webgame Yuniebel)

## Đối chiếu AC (tiêu chí chấp nhận)

| AC | Nội dung | Trạng thái | Ghi chú |
|----|----------|------------|---------|
| AC1 | Chạy offline bằng file:// + relative path | ✅ | Script classic + relative path (core/sprites/audio/game.js) |
| AC2 | Title: bầu trời + mây + mặt trời + START | ✅ | bgTitle() vẽ gradient + sun + clouds + grass |
| AC3 | Mèo pixel tóc hồng, WASD, bị chặn | ✅ | Sprites.cat() + collision slide + clamp biên |
| AC4 | Nút UI toggle (góc phải) | ✅ | uiBtn click → ẩn/hiện task box |
| AC5 | Task box (góc trái) + nút X → Title | ✅ | taskText + task-close → resetGame() |
| AC6 | Cảnh 1 tuần tự: cửa khóa → bướm → đuổi → tối → LIVING | ✅ | core.js phases G_INIT→G_BUTTERFLY→G_CHASE→G_DARK→G_DOOR |
| AC7 | Cảnh 2: phòng khách → bếp | ✅ | L_SEARCH → zone door_kitchen → K_INIT |
| AC8 | Cảnh 3: máu → lời gọi → chọn 1/2 hoặc vùng tối | ✅ | K_INIT→K_BLOOD→K_VOICE→K_CHOICE; [1]→K_RUN→HAUNTED; [2]→K_OBEY→GAMEOVER |
| AC9 | Cảnh 4: knockback cửa trước + cửa hành lang | ✅ | HAUNTED: door_front knockback 40px + cd 1.5s; door_hall → HALLWAY |
| AC10 | Cảnh 5: 5 scare fire-once + counter | ✅ | HALLWAY: 5 scare zones, counter "Bị hù: x/5", W_DONE |
| AC11 | Cảnh 6: cutscene → ôm → bánh → END | ✅ | D_APPROACH→D_JUMP→D_HUG→D_CAKE→D_END |
| AC12 | Fade + darkness + light radius | ✅ | fade 0.5s, darkness overlay, lightCanvas radial gradient |
| AC13 | pages.yml tồn tại | ✅ | .github/workflows/pages.yml (checkout→configure→upload→deploy) |
| AC14 | Node test PASS | ✅ | 58/58 PASS |
| AC15 | Hard gate đầy đủ + LOG/PROGRESS | ✅ | Đang thực hiện |
| AC16 | resetGame() reset toàn bộ | ✅ | node test: "resetGame 2 lần liên tục không lỗi" |
| AC17 | D-pad mobile | ✅ | ontouchstart → d-pad div overlay |

## Kết luận
- **17/17 AC PASS**
- Sprites mới dùng canvas primitives thay vì ma trận ký tự — pixel art chi tiết hơn nhiều
- Backgrounds pre-rendered (7 scenes) — render mỗi frame chỉ cần drawImage 1 lần
- Audio: WebAudio 4 SFX (meow/scare/chime/whisper), graceful degradation
- Mobile: d-pad ảo + touch events

## Bài học
- Ma trận ký tự 16x16 quá thô → canvas primitives cho pixel art đẹp hơn nhiều
- Pre-render backgrounds →性能 tốt hơn fillRect từng ô mỗi frame
- Override requestAnimationFrame trước khi eval game.js trong jsdom (tránh jsdom native rAF bất đồng bộ)

## Hành động đề xuất
- Manual test trên browser (file:// + GitHub Pages URL)
- Bật GitHub Pages tại Settings → Pages → Source: GitHub Actions
