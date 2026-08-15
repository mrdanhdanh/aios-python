# COMPARISON.md — Đối chiếu ảnh chụp (bản Phaser) vs refs (baseimg)

> Ngày: 2026-08-15 · TASK-081 · 17 ảnh chụp từ game Phaser (test-results/shots/)
> Đối chiếu thủ công với `test/brief/refs/1..6.png` (copy từ `games/yuniebel/baseimg/`)
> + nguồn chuẩn `aios/progress/tasks/TASK-078/implementation/brief-visuals.md`
> ✅ = khớp cấu trúc chính (trời/nhà/nội thất/vị trí mèo) · ⚠️ = lệch nhẹ · ❌ = chưa khớp

| # | Ảnh chụp | Ref | Brief yêu cầu (brief-visuals.md) | Kết quả đối chiếu | Trạng thái |
|---|----------|-----|----------------------------------|-------------------|------------|
| 1 | title.png | refs/1.png | Trời gradient + dithering, mặt trời + hào quang, mây trắng, nút START xanh lá chữ vàng cam, phong cảnh (đồi/cây/nước), mèo cạnh nút | | |
| 2 | garden-day.png | refs/2.png (panel 1) | Trời xanh sáng, cỏ xanh, nhà gỗ hiên, hàng rào trắng, cậu bé ở cửa, mèo trên cỏ, bóng đỏ | | |
| 3 | garden-dusk.png | refs/2.png (panel 2) | Hoàng hôn cam/tím, đèn hiên bật, bướm vàng trước mèo | | |
| 4 | garden-night.png | refs/2.png (panel 3) | Đêm xanh đậm + sao, đèn hiên sáng, cảnh tối (dark overlay) | | |
| 5 | living.png | refs/3.png (trái) | Sofa đỏ cam + gối, bàn trà, thảm be, đồng hồ tròn, kệ sách, chậu cây, đèn sconce, cửa tối | | |
| 6 | kitchen-blood.png | refs/3.png (phải) | Bếp tối, tủ trắng, vết máu LỚN đỏ, 2 mắt trắng trong tối | | |
| 7 | kitchen-choice.png | refs/3.png (phải) | Hộp lựa chọn 1 Bỏ chạy / 2 Nghe theo lời gọi (HTML overlay) | | |
| 8 | haunted-ghost.png | refs/4.png | Ma XANH đầu lâu lớn chặn cửa, sofa cũ, đồng hồ quả lắc, mạng nhện, nến | | |
| 9 | haunted-block.png | refs/4.png | Task "Phải đi qua phòng khác!" | | |
| 10-14 | hallway-scare1..5 | refs/5.png | 5 kiểu hù RIÊNG BIỆT (ma trắng / chân dung hét / tay zombie / bóng mắt vàng / mặt xương) + dấu !/!!/!!!/!? trên mèo | | |
| 15 | birthday.png | refs/6.png | Lò sưởi lửa, bánh kem 4 nến, chủ đứng cạnh, mèo, sparkle, "Chúc Mừng Sinh Nhật!" | | |
| 16 | gameover.png | — | Nền tối đỏ "GAME OVER" + nút Chơi lại | | |
| 17 | end.png | — | Nền ấm, bánh kem, chữ chúc mừng | | |

## Kết luận (điền sau khi xem ảnh)

<!-- Ghi kết quả từng ảnh + tổng số ✅/⚠️/❌ -->
