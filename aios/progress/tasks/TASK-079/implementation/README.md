# TASK-079 — implementation/

> Pointer tới code đã sửa (TASK-079 — Fix mèo biến mất sau START, logical grid).

## File đã thay đổi

| File | Nội dung thay đổi |
|------|-------------------|
| `games/yuniebel/src/core.js` | Chuyển toàn bộ scene/hằng số về logical grid (÷3): GARDEN/HALLWAY 320×90, còn lại 160×90; spawn/walls/zones/scareZones/butterflyWp; WALK_SPEED 40, BUTTERFLY_SPEED 20, KNOCKBACK 13, DARK_RECT (7,7,31,33); trigger bướm x>260, spawn (233,47); debug setButterfly (233,50) |
| `games/yuniebel/src/sprites.js` | `sky(ctx,darkness,time,w)` thêm width; `drawGarden(ctx,state,time,cx)` mở rộng 320 + nhà (267..320) + save/translate/restore; `drawLiving`/`drawKitchen`/`drawHaunted` khớp walls logical; `drawHallway(ctx,state,time,cx)` mở rộng 320 + 5 scare vị trí tuyệt đối (130/160/210/260/300) + save/translate/restore |
| `games/yuniebel/src/game.js` | `camX()` thay toàn bộ (giữ !sc guard, bỏ sc.w<=CW, viewport 160); drawScene truyền cx; xóa `drawBlood(68,66)`; đèn hiên (287−cx)*GX, y 38*GX |
| `games/yuniebel/test/core.test.js` | 11 vị trí player ÷3; xuyên tường (263,30); máu (63,73) |
| `games/yuniebel/test/e2e.spec.js` | moveTo hai tầng (120ms/40ms, dừng |dx|<2&&|dy|<2); targets logical; test AC-2 mới |
| `games/yuniebel/test/visual.spec.js` | setPlayer ÷3 mọi shot; +4 pixel tests AC-1/AC-4/AC-10/AC-5 |

## Kết quả test

- `node test/core.test.js` — 27/27 PASS
- `node test/smoke.test.js` — 4/4 PASS
- `npx playwright test` — 28/28 PASS
- Tổng: **59/59 PASS** (chi tiết: `test.md`, `evaluation.md`)
