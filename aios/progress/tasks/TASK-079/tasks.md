# TASK-079 — tasks.md (breakdown checklist)

> Spec: `spec.md` (đạt sau critique ×3) · Ngày: 2026-08-15

## P0 — core.js (logical grid)

- [ ] P0-1: Chia 3 hằng số: WALK_SPEED 120→40, BUTTERFLY_SPEED 60→20, KNOCKBACK 40→13, DARK_RECT (20,20,92,100)→(7,7,31,33), BUTTERFLY_STAY 40→13, BUTTERFLY_CATCH 12→4 (cosmetic)
- [ ] P0-2: GARDEN scene: w 960→320, h 270→90, spawn (320,210)→(107,70), butterflyWp ×3, walls ×3 (nhà (267,7,53,43), bụi (67,62,8,5)/(117,33,7,5)/(207,85,9,4)/(13,50,7,4), cây (230,13,6,23)), door zone (284,48,11,20)
- [ ] P0-3: LIVING scene: w 160, h 90, spawn (113,63), walls (10,53,30,15)/(63,67,23,4)/(127,70,10,17), door_kitchen (3,30,11,20)
- [ ] P0-4: KITCHEN scene: w 160, h 90, spawn (80,73), walls (100,47,30,15)/(127,7,33,43), zones blood (50,78,40,8)/dark=DARK_RECT/door_out (149,43,11,20)
- [ ] P0-5: HAUNTED scene: w 160, h 90, spawn (90,63), walls (10,53,30,15)/(67,68,20,4), zones door_front (143,33,15,33)/door_side (2,30,11,20)
- [ ] P0-6: HALLWAY scene: w 960→320, h 270→90, spawn (60,135)→(20,45), wall (0,33,9,23), scareZones ×3 (47/100/153/207/260, 33,30,20), door_dining (302,33,14,20)
- [ ] P0-7: BIRTHDAY scene: w 160, h 90, spawn (80,67), wall bàn (47,47,67,20)
- [ ] P0-8: Trigger bướm x>780→x>260; spawn bướm (700,140)→(233,47); clamp bướm 8..w−20; debug setButterfly (700,150)→(233,50)

## P1 — sprites.js (background khớp)

- [ ] P1-1: `sky(ctx, darkness, time, w)` — thêm width; sao `% (w-10)`; drawGarden/drawHallway truyền w=320
- [ ] P1-2: `drawGarden(ctx, state, time, cx)` — bọc save/translate(-cx*GX,0)/restore; trải cỏ/rào/đường 0..320; cây (230,13); nhà x 267..320 (thân 267,26,53,24; mái; cửa 285,42,9,8; sổ 271,32 & 300,32; hiên 265,49,55,2; đèn 287,38); owner (288,44) khi G_INIT; bụi/hoa theo 4 wall
- [ ] P1-3: `drawLiving` — sofa (10,52), bàn trà (63,66), kệ (126,70,12,17); giữ phần còn lại
- [ ] P1-4: `drawKitchen` — máu (50,78,40,8)+nhánh (54,86,26,3)+chấm (66,86,6,2)+drip; vùng tối (7,7,31,33)+mắt (17,19)/(23,19); tủ lạnh (128,12,16,30); bàn (100,47,30,3)+chân; cửa (149,40,4,20); K_CHOICE highlight (50,78,40,8); tủ trái giữ
- [ ] P1-5: `drawHaunted` — cửa chính (143,20,12,40), ghost (139,16), glow (143,34,12,20), cửa phụ (0,40,4,20)
- [ ] P1-6: `drawHallway(ctx, state, time, cx)` — bọc save/translate; trải 320; 11 đuốc `8+i*29`; cửa (0,40,4,20)/(316,40,4,20); scare 130/160/210/260/300

## P2 — game.js (camera + cleanup)

- [ ] P2-1: `camX()` → `Math.max(0, Math.min(player.x - 80 + 3, sc.w - 160))`
- [ ] P2-2: drawScene truyền cx vào drawGarden/drawHallway
- [ ] P2-3: Xóa `S.drawBlood(ctx, 68, 66, ...)` khỏi drawScene KITCHEN
- [ ] P2-4: Đèn hiên overlay `lx = (287 - cx) * S.GX`

## P3 — Test (cập nhật + thêm)

- [ ] P3-1: core.test.js — 11 chỗ tọa độ ÷3; xuyên tường (263,30); máu (63,73)
- [ ] P3-2: e2e.spec.js — moveTo tolerance |dy|>2; targets (271,70)/(288,50)/(7,20)/(3,20)/(20,20)/(147,50)/(310,45)/(312,45); comments 40/20 + x>260
- [ ] P3-3: e2e.spec.js — test AC-2 mới: hold "d" 1s → player.x tăng
- [ ] P3-4: visual.spec.js — setPlayer ÷3 (garden-day 107,70; garden-dusk 153,53 + bướm 160,43; garden-night 133,57; living 107,63; kitchen 73,70 ×2; haunted 90,63 ×2; hallway ×5; birthday 80,67; R1 (107,63))
- [ ] P3-5: AC-1 pixel test mới (region 231..279, 210..258, ≥30 px #f5a623) + AC-4 + AC-10 pixel tests (nhà hiện khi cam 160; hallway scare5) + **AC-5: pixel check catBody hiện diện trong 6 shot có player (garden-day, living, kitchen ×2, haunted ×2, hallway ×5, birthday)** (R4)

## P4 — Verify & đóng

- [ ] P4-1: `node test/core.test.js` — 27/27 PASS (AC-6)
- [ ] P4-2: `node test/smoke.test.js` — 4/4 PASS (AC-7)
- [ ] P4-3: `npx playwright test` — e2e + visual PASS (AC-3/AC-5/AC-8), không crash (AC-9)
- [ ] P4-4: AC-1/AC-2/AC-4/AC-10 verify qua screenshot pixel + test mới
- [ ] P4-5: Cập nhật PROGRESS.md + LOG.md + commit
