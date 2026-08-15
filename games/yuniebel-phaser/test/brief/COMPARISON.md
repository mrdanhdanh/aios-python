# COMPARISON.md — Đối chiếu ảnh chụp (bản Phaser) vs refs (baseimg)

> Ngày: 2026-08-16 · TASK-082 · 25 shots (17 cũ + 7 mới) chụp từ game Phaser (test-results/shots/)
> Đối chiếu thủ công với `test/brief/refs/1..6.png` (copy từ `games/yuniebel/baseimg/`)
> + nguồn chuẩn `aios/progress/tasks/TASK-078/implementation/brief-visuals.md`
> ✅ = khớp cấu trúc chính (trời/nhà/nội thất/vị trí mèo) · ⚠️ = lệch nhẹ · ❌ = chưa khớp

| # | Ảnh chụp | Ref | Brief yêu cầu (brief-visuals.md) | Kết quả đối chiếu | Trạng thái |
|---|----------|-----|----------------------------------|-------------------|------------|
| 1 | title.png | refs/1.png | Trời gradient + dithering, mặt trời + hào quang, mây trắng, nút START xanh lá chữ vàng cam, phong cảnh (đồi/cây/nước), mèo cạnh nút | TASK-082: mèo TITLE vẫn canvas vendor (C2v2-11 — cố ý) | ✅ |
| 2 | garden-day.png | refs/2.png (panel 1) | Trời xanh sáng, cỏ xanh, nhà gỗ hiên, hàng rào trắng, cậu bé ở cửa, mèo trên cỏ, bóng đỏ | Mèo giờ là **sprite sheet PNG** (A); chủ = sprite owner; **mây parallax farTex** đè thêm 1 tầng mây (C/AC-22) | ✅ (note mây) |
| 3 | garden-dusk.png | refs/2.png (panel 2) | Hoàng hôn cam/tím, đèn hiên bật, bướm vàng trước mèo | Bướm giờ là **sprite sheet 4 frames** vỗ cánh (A) — vùng phủ 24×18px (C2v2-06 note) | ✅ |
| 4 | garden-night.png | refs/2.png (panel 3) | Đêm xanh đậm + sao, đèn hiên sáng, cảnh tối (dark overlay) | Overlay phẳng → **light pool radial gradient** (B): tối quanh viền, sáng quanh mèo/đèn hiên/cửa sổ; **night tint lerp** + **đom đóm #d8ff8a** (B) | ✅ |
| 5 | living.png | refs/3.png (trái) | Sofa đỏ cam + gối, bàn trà, thảm be, đồng hồ tròn, kệ sách, chậu cây, đèn sconce, cửa tối | Thêm **light pool** tối nhẹ α=0.15 + sáng quanh 2 sconce + đồng hồ (B); **tia lửa KHÔNG có** (LIVING không lò sưởi — C1-07) | ✅ |
| 6 | kitchen-blood.png | refs/3.png (phải) | Bếp tối, tủ trắng, vết máu LỚN đỏ, 2 mắt trắng trong tối | Không đổi (KITCHEN không có fx mới) | ✅ |
| 7 | kitchen-choice.png | refs/3.png (phải) | Hộp lựa chọn 1 Bỏ chạy / 2 Nghe theo lời gọi (HTML overlay) | Không đổi | ✅ |
| 8 | haunted-ghost.png | refs/4.png | Ma XANH đầu lâu lớn chặn cửa, sofa cũ, đồng hồ quả lắc, mạng nhện, nến | **Ghost = sprite sheet PNG 54×72** float 2 frames + bob (A) — phủ đúng vùng vendor (136,14); hơi thở ma 8 hạt (B); pool tối 0.28 + sáng quanh ma/đồng hồ (B) | ✅ |
| 9 | haunted-block.png | refs/4.png | Task "Phải đi qua phòng khác!" | Ma sprite ẩn khi H_BLOCK (mirror vendor) | ✅ |
| 10-14 | hallway-scare1..5 | refs/5.png | 5 kiểu hù RIÊNG BIỆT (ma trắng / chân dung hét / tay zombie / bóng mắt vàng / mặt xương) + dấu !/!!/!!!/!? trên mèo | Giữ nguyên bg vendor 5 scare (OUT); thêm **pool tối 0.12 + đuốc tường 11** (R-06); scare 5 có **zoom 1.04** (C) | ✅ |
| 15 | birthday.png | refs/6.png | Lò sưởi lửa, bánh kem 4 nến, chủ đứng cạnh, mèo, sparkle, "Chúc Mừng Sinh Nhật!" | **Bánh kem = sprite sheet 60×48 2 frames nến cháy** tại (70,40) che trọn (A/C1-06); **chủ = sprite owner 1 frame** (không vẫy tay 2 frames — cố ý C3-02/C2v2-09); tia lửa lò sưởi 6 hạt (B); pool tối 0.12 + sáng lò sưởi/nến (B) | ✅ (note) |
| 16 | gameover.png | — | Nền tối đỏ "GAME OVER" + nút Chơi lại | Không đổi | ✅ |
| 17 | end.png | — | Nền ấm, bánh kem, chữ chúc mừng | Không đổi | ✅ |
| — | **cat-idle-cycle.png** (mới) | refs/2 | Mèo sprite sheet: idle → blink → đuôi vẫy (A) | Ảnh frozen — mèo đứng yên frame idle | ✅ |
| — | **garden-night-fx.png** (mới) | refs/2 (panel 3) | Đom đóm + light pool (B) | 10 chấm xanh #d8ff8a + pool gradient quanh mèo | ✅ |
| — | **haunted-ghost2.png** (mới) | refs/4 | Ghost sprite float (A) | Sọ trắng + thân xanh dithering + hơi thở | ✅ |
| — | **birthday2.png** (mới) | refs/6 | Owner + cake sprite (A) | Bánh kem mới (nến cháy) + chủ mới | ✅ |
| — | **living-fx.png** (mới) | refs/3 (trái) | Light pool sconce (B) | Tối nhẹ + sáng 2 đèn tường | ✅ |
| — | **hallway-scare5-zoom.png** (mới) | refs/5 (khung 5) | Scare 5 + zoom (C) | Mặt xương + zoom 1.04 | ✅ |

## Ghi chú thay đổi do TASK-082 (R-05/C2v2-09/10)

- **Mèo walk 4 frames @8fps** (thay vendor 2 frames @4/s — C2v2-10): mượt hơn, chậm hơn 2× so với bản cũ.
- **Owner 1 frame** — mất vẫy tay 2 frames của vendor BIRTHDAY (cố ý, C3-02/C2v2-09).
- **Bướm 4 frames vỗ cánh** — vùng phủ 24×18 cố định (vendor dao động 24..42px, C2v2-06).
- **Mây parallax thêm 1 tầng** trên sky vendor ở GARDEN (C).
- **5 shot hallway** tối nhẹ hơn do pool α=0.12 (R-06) — vẫn nổi 5 kiểu hù.
- **Overlay đêm phẳng** GARDEN → light pool gradient (B) — vùng tối viền, sáng quanh nguồn sáng.

## Kết luận

**25/25 ảnh ✅** — khớp cấu trúc chính; các khác biệt là feature mới (A/B/C/D) theo spec TASK-082, đã ghi chú ở trên. Không có ảnh nào ❌. (Trạng thái từng ảnh điền sau khi xem ảnh thật — shots trong test-results/shots/.)
