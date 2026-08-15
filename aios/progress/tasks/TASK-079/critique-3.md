# Critique vòng 3 — TASK-079 (XÁC NHẬN cuối, critic độc lập)

> Ngày: 2026-08-15 · Critic: AIOS critic agent · Đối tượng: `spec.md` (bản sau vòng 2 resolve)
> Trạng thái sau resolve: **RESOLVED 1/1 P1 + 1/1 P2 + 3/3 P3 — SPEC ĐẠT, không còn P1/P2**

## Phần 1 — Verify 9 resolution vòng 2 (a→i): ĐÚNG HẾT ✅

| # | Nội dung | Kiểm chứng |
|---|----------|-----------|
| (a) | AC-1 region (231..279, 210..258) | cam = 107−80+3 = 30; screen x = 77×3 = 231..279 ✓ |
| (b) | save/restore quanh translate | Có trong §3.2 (C2-P1-2) ✓ |
| (c) | e2e (288,50) cả AC-14a/14b | Có ✓ — nhưng thiếu đường đi (P1 mới) |
| (d) | Đèn hiên 287 | §3.2 (287,38) + §3.3 (287−cx)*GX khớp ✓ |
| (e) | Nhánh máu y ≤ 90 | (54,86,26,3)→89; (66,86,6,2)→88 ✓ |
| (f) | scare3 63..103/107..147 | Trigger x∈[141..179] → cam 64..102 → screen 108..146 ✓ |
| (g) | BUTTERFLY_CATCH cosmetic | butterflyHit dùng cứng 8/16 — đúng chú thích ✓ |
| (h) | AC-10 setScareZone(5)+freeze | Có thật trong debug API ✓ |
| (i) | Tủ bếp trái giữ nguyên | Khớp code hiện tại ✓ |

## Phần 2 — Rà toàn cục: KHÔNG thiếu tọa độ, mọi AC kiểm chứng được

Toàn bộ 7 scene (w/h/spawn/walls/zones/scareZones/butterflyWp), hằng số, core.test.js (27 test = AC-6), e2e.spec.js, visual.spec.js, sprites.js, game.js — đều đã liệt kê đủ trong spec, không chỗ nào bị bỏ sót chia 3.

## Phần 3 — Vấn đề MỚI (vòng xác nhận)

### P1 — (288,50) chưa đủ: wall nhà chặn đường tiếp cận cửa khi catch bướm tại y < 48
- Wall nhà (267,7,53,43) đáy y=50. Mèo chỉ thoát khi hitbox top ≥ 50 → p.y ≥ 48, và cần p.y ≤ 66 để chạm door zone (284,48,11,20) → hành lang hợp lệ y ∈ [48..66] (18px).
- `moveTo` tolerance |dy| ≤ 12: mèo dừng y ∈ [38..62] — đoạn [38..48) bị wall chặn tại x≈257 → kẹt G_DOOR → fail. Catch bướm tại y < 48 là thực tế (bướm wp y 40/30 → catch y ≈ b.y+6 ∈ [40..53]); 2 trace mô phỏng: catch y=40.4 → FAIL, y=50.8 → PASS — flaky thật.
- **Resolve**: đổi moveTo Y-tolerance `|dy| > 12` → `|dy| > 2` → mọi catch y hội tụ [48..52] ⊂ [48..66] ✓. Verify an toàn mọi target khác: (7,20)→20.6 (hitbox 22.6..34.6 clear sofa ✓), (3,20) ✓, (20,20) ✓, (147,50) ✓, (310/312,45) ✓. ✅ spec §3.4.

### P2 — Trigger bướm x > 260 sát cửa sổ dừng moveTo → margin âm flaky
- moveTo dừng |dx| < 10 → dừng x ∈ (257, 267); fail window (257, 260) → bướm không spawn. Landing danh định 260.6 chỉ hơn ngưỡng 0.6px (cũ: 780 vs dừng ≥ 790, margin 10px).
- **Resolve**: target GARDEN `(267,70)` → `(271,70)` → dừng (261..271) luôn > 260 ✓. ✅ spec §3.4.

### P3 — Góp ý (3)
| # | Ý kiến | Resolve |
|---|--------|---------|
| P3-1 | kitchen (73,70) áp dụng 2 shot; haunted (90,63) 2 shot; R1-determinism setPlayer → (107,63) | Ghi rõ cả 3 trong §3.4 ✅ |
| P3-2 | Comment e2e "x>780" chưa ghi đổi | → "x>260" ✅ |
| P3-3 | Spawn bướm (233,47) nằm trong nhánh G_INIT updateGame | Ghi rõ nguồn trong §3.1 ✅ |

## Kết luận

**Vòng 3: RESOLVED 1/1 P1 + 1/1 P2 + 3/3 P3 — SPEC ĐẠT, KHÔNG còn P1/P2.** Đủ 3 vòng critique (2 vòng phản biện + 1 vòng xác nhận). Sẵn sàng chuyển sang `tasks.md` + Review + Implement.
