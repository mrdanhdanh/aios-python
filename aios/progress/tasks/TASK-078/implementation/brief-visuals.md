# Mô tả chi tiết 5 ảnh tham khảo (phân tích vision từ ảnh người dùng gửi 2026-08-15)

> Ảnh gốc là file đính kèm chat (không nằm trong repo). Đây là **bản mô tả chuẩn** để sprites.js bám theo khi render canvas primitives.
> Lưu ý tỷ lệ: ảnh ref 1 (title) dạng portrait; các ảnh khác dạng ngang nhiều panel. Game render lại theo canvas **480×270 landscape** (bố cục lại, giữ nguyên tinh thần).

## Ảnh 1 — Title screen (màn hình chính)

- **Bố cục**: Trời chiếm ~70% trên; nút START giữa màn; phong cảnh (đồi/núi/cây/nước) ~25% dưới cùng. Render lại ngang: trời gradient + nút giữa + phong cảnh dưới.
- **Màu**: Trời xanh dương gradient (đậm trên → nhạt gần chân trời) + **dithering chấm** pixel; mặt trời **vàng rực** góc trên phải có hào quang xanh nhạt; mây **trắng xốp** nhiều tầng (1 cụm lớn bên trái, vài cụm nhỏ); nút **xanh lá đậm viền đen dày** (cảm giác 3D nổi), chữ **vàng cam in hoa** "START" kiểu pixel blocky; phía dưới: dãy núi/đồi **xanh lam nhạt** → dải bụi cây **xanh lá đậm** → dải **xanh dương đậm** (mặt nước) sát mép dưới.
- **Chi tiết thêm cho game**: mèo Yuniebel (cam+trắng) đứng cạnh nút START; mây trôi nhẹ (anim).

## Ảnh 2 — Cảnh 1 Sân vườn (3 panel: ngày → hoàng hôn → đêm)

- **Panel 1 (ngày)**: trời **xanh sáng**, cỏ **xanh lá**, nắng; **ngôi nhà gỗ nhỏ** bên phải: tường gỗ, mái, **hiên nhà**, **hàng rào gỗ**, cửa ra vào; **cậu bé** (tóc nâu, áo xanh) đứng ở cửa, tay dang, bong bóng thoại "Yuniebel! Vào nhà đi!"; **mèo cam-trắng** ngồi trên cỏ nhìn về phía nhà; **quả bóng đỏ** trên cỏ; hộp văn bản đáy: **đen viền vàng**, chữ vàng.
- **Panel 2 (hoàng hôn)**: trời **cam/tím** (hoàng hôn rực), mặt trời lặn; cỏ xanh đậm; **đèn hiên nhà bật** (vàng cam); cửa nhà mở tối om; mèo **đang bước đi** (walk) về phía phải; **bướm vàng** xuất hiện trước mặt mèo; hộp văn bản "Đuổi theo con bướm!".
- **Panel 3 (đêm)**: trời **xanh đậm + sao**; cảnh tối; đèn hiên vẫn sáng; mèo **đang chạy** (running) về phía phải, vươn người; bướm vàng vẫn bay trước; hộp văn bản "Hãy vào nhà!".
- **Ghi chú**: cậu bé đứng trong nhà (chủ nhân) — trong game hiện ở cửa khi G_INIT, biến mất khi mèo quay lại.

## Ảnh 3 — Cảnh 2 Phòng khách (trái) + Cảnh 3 Nhà bếp (phải)

- **Phòng khách (trái)**: ấm áp, tông **nâu/cam**; **sofa đỏ cam** có gối tựa; **bàn trà gỗ** thấp + **thảm be** họa tiết; tường **kem sọc mờ**; **đèn tường (sconce)** vàng ấm 2 bên; tranh phong cảnh treo; **đồng hồ tròn** treo tường; **kệ sách gỗ + chậu cây xanh** góc phải; **cửa tối đen** hậu cảnh giữa; mèo đứng giữa phòng nhìn về phải; hộp văn bản vàng "Tìm chủ nhân ở nhà bếp."
- **Nhà bếp (phải)**: lạnh/tối hơn, tông **xanh xám/đen**; **tủ bếp trắng/xám** trên tường; **lò nướng**; **tủ lạnh** (mặt đơn giản); sàn **gạch nâu tối**; **vũng máu đỏ tươi LỚN** loang trên sàn; **cửa tối đen** góc phải có **2 đốm mắt trắng sáng** (sinh vật nhìn ra); mèo đứng gần vũng máu; hộp thoại đen: tiêu đề vàng "Kiểm tra vết máu!", dòng "1. Bỏ chạy" / "2. Nghe theo lời gọi.".

## Ảnh 4 — Cảnh 4 Phòng khách ma ám

- Tông **tối xanh đen/tím than**; sàn gỗ tối; dầm gỗ trần; **mạng nhện** góc trên trái.
- **Sofa đỏ nâu cũ** bên trái + kệ nến cháy + tranh nhỏ; **đồng hồ quả lắc (grandfather clock)** gỗ cao bên phải; nhiều khung ảnh; **khung ảnh rơi nghiêng** trên sàn; bàn nhỏ 2 nến; **thảm họa tiết**.
- **Con ma LỚN trung tâm** chặn cửa lớn: bóng ma cổ điển, **màu xanh lam nhạt phát sáng**, trong suốt bay phất phới, mặt là **hộp sọ trắng 2 hốc mắt đen**, tay dang đe dọa.
- Mèo đứng tiền cảnh (bình thản); dòng chữ vàng dưới đáy: **"Phải đi qua phòng khác!"**.
- Hiệu ứng: glow nến + aura xanh của ma.

## Ảnh 5 — Cảnh 5 Hành lang (5 khung jump scare)

- Hành lang gỗ tối: sàn ván gỗ, **đuốc/nến gắn tường** sáng cam, cửa hai đầu, tối.
- **Khung 1**: mèo quay đầu giật mình (dấu **"!"** trắng trên đầu); **ma trắng ga cổ điển** (miệng há) bay sau lưng.
- **Khung 2**: **bức chân dung phụ nữ HÉT** trên tường, 2 tay vươn ra khỏi khung; dấu **"!!"**.
- **Khung 3**: **nhiều bàn tay trắng bệch kiểu zombie** vươn từ bóng tối/cửa tối cuối hành lang; mèo quay nhìn; dấu **"!!!"**.
- **Khung 4**: **bóng đen TO lớn, 2 mắt vàng phát sáng** đứng cuối hành lang; mèo quay nhìn; dấu **"!?"**.
- **Khung 5**: **khuôn mặt xương sọ/quái vật** lớn (miệng há rộng) hiện ra từ bóng tối bên trái; jump scare cuối.
- Palette: đen/nâu sẫm + cam nến + trắng/xanh ma + vàng mắt.

## Tổng hợp palette chính (hex tham khảo)

- Trời ngày: `#4da6ff → #a8dcff` (gradient); hoàng hôn: `#ff9a3c → #b04fd6`; đêm: `#0b1d4d → #1d3a8a` + sao trắng.
- Cỏ: `#3fae4a` (ngày) / `#2a6b33` (tối); sàn gỗ: `#5a3a24`, `#7a5230`; tường kem: `#e8d9b8`; tối ma ám: `#23203d`, `#10101f`.
- Mèo: thân cam `#f5a623`, trắng `#ffffff`; chủ: áo xanh `#2e86de`, tóc nâu `#7a4a21`.
- Ma xanh: `#8ec9ff` (body) + sọ trắng; ma trắng ga: `#e8ecf2`; máu: `#d92626`, đỏ đậm `#8f1010`.
- UI text vàng: `#ffd93b`; nền hộp thoại đen `#101018` viền vàng; nút START xanh lá `#2ea44f` viền đen, chữ vàng cam `#ffb52e`.
