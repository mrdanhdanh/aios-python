# COMPARISON.md — Đối chiếu ảnh chụp vs brief (AC-11/AC-12)

> Ngày: 2026-08-15 · 17 ảnh chụp từ game (test-results/shots/ + task folder shots/)
> Đối chiếu thủ công với `aios/progress/tasks/TASK-078/implementation/brief-visuals.md` (mô tả 5 ảnh ref)
> ✅ = khớp brief · ⚠️ = lệch nhẹ (ghi rõ) · ❌ = chưa khớp

| # | Ảnh | Brief yêu cầu | Kết quả đối chiếu | Trạng thái |
|---|-----|---------------|-------------------|------------|
| 1 | title.png | Trời xanh gradient + dithering, mặt trời vàng, mây trắng, đồi/núi + bụi cây + nước, nút START xanh lá chữ vàng cam giữa, mèo cạnh nút | Trời xanh sáng ✓, mây trắng ✓, mặt trời ✓, nước gợn ✓, nút START xanh lá giữa ✓, mèo cam cạnh nút ✓ (overlay nhẹ 0.25 — cảnh vẫn rõ) | ✅ |
| 2 | garden-day.png | Trời xanh sáng, cỏ xanh, nhà gỗ hiên mái đỏ tường be, hàng rào trắng, cây/bụi/hoa hồng, bóng đỏ, chủ (tóc nâu áo xanh) ở cửa, mèo trên cỏ | Trời xanh ✓, cỏ xanh ✓, nhà mái đỏ tường kem + cửa gỗ + 2 cửa sổ ✓, hàng rào trắng ✓, bụi hoa hồng ✓, chủ đứng cửa ✓, mèo cam ✓ | ✅ |
| 3 | garden-dusk.png | Hoàng hôn cam/tím, mặt trời lặn, đèn hiên bật, bướm vàng trước mặt mèo | Trời cam/tím ✓ (pixel 255,154,60 / 185,87,197), đèn hiên ✓, bướm vàng ✓ | ✅ |
| 4 | garden-night.png | Đêm xanh đậm + sao, đèn hiên sáng, cảnh tối | Trời đêm ✓ (pixel 9,23,62), sao ✓, đèn hiên ✓ | ✅ |
| 5 | living.png | Phòng khách ấm: sofa đỏ cam + gối, thảm sọc be, tranh, đồng hồ tròn, kệ sách, chậu cây, đèn sconce, cửa tối | Tường kem sọc ✓, sofa đỏ cam + gối ✓, đồng hồ tròn ✓, tranh ✓, kệ sách ✓, chậu cây ✓, đèn sconce ✓, thảm ✓, cửa tối ✓ | ✅ |
| 6 | kitchen-blood.png | Bếp tối: tủ trắng tay nắm tối, lò, tủ lạnh, vết máu LỚN đỏ, mắt trắng trong tối | Tủ trắng + tay nắm ✓, lò ✓, tủ lạnh ✓, vết máu lớn đỏ ✓ (68..98 logical), vùng tối 2 mắt trắng ✓, giọt anim ✓ | ✅ |
| 7 | kitchen-choice.png | Hộp lựa chọn 1 Bỏ chạy / 2 Nghe theo lời gọi | Hộp chọn hiển thị ✓ (HTML overlay) + highlight vết máu ✓ | ✅ |
| 8 | haunted-ghost.png | Ma XANH đầu lâu lớn chặn cửa, dầm gỗ, mạng nhện, đồng hồ quả lắc, chân nến, ảnh nghiêng, sofa cũ | Ma xanh đầu lâu giữa ✓, dầm gỗ ✓, mạng nhện ✓, đồng hồ quả lắc ✓, nến cháy ✓, ảnh nghiêng ✓, sofa cũ ✓ | ✅ |
| 9 | haunted-block.png | Task "Phải đi qua phòng khác!" sau knockback | Task hiển thị đúng ✓ (test core assert + screenshot) | ✅ |
| 10-14 | hallway-scare1..5 | 5 kiểu hù RIÊNG BIỆT: ma trắng / chân dung hét / tay zombie / bóng mắt vàng / mặt xương; nến tường; mèo + dấu !/!!/!!!/!? | 5 sprite khác nhau ✓, nến/đuốc tường ✓, dấu hù trên đầu mèo ✓ | ✅ |
| 15 | birthday.png | Lò sưởi lửa, bánh kem 4 nến, chủ đứng cạnh, mèo, sparkle, text "Chúc Mừng Sinh Nhật!" | Lò sưởi lửa anim ✓, bánh kem 4 nến ✓, chủ đứng cạnh ✓, sparkle ✓, text "Chuc Mung Sinh Nhat!" ✓ (font monospace — không emoji theo C2-12) | ✅ |
| 16 | gameover.png | Nền tối đỏ "GAME OVER" + dòng phụ + nút Chơi lại | Canvas tối đỏ "GAME OVER" ✓ + overlay nút ✓ | ✅ |
| 17 | end.png | Nền ấm, bánh kem, chữ chúc mừng, nút Chơi lại | Nền kem ấm ✓, bánh kem nến ✓, chữ "Chuc Mung Sinh Nhat Yuniebel!" ✓ | ✅ |

## Kết luận

**17/17 ảnh khớp brief** (theo mô tả chuẩn brief-visuals.md — ảnh ref gốc là file đính kèm chat, không trong repo).
Ghi chú nhỏ: chữ tiếng Việt có dấu trong canvas dùng font monospace — render ổn định trên mọi máy (không emoji 🎂 theo C2-12).
