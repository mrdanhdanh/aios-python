# TASK-079 — test.md

> Ngày: 2026-08-15 · Cách chạy: `cd games/yuniebel && npm test`

## Kết quả: 59/59 PASS

| Bộ test | Lệnh | Kết quả |
|---------|------|---------|
| Core logic (27) | `node test/core.test.js` | **27/27 PASS** — chuỗi kịch bản, thoại, task, scare 5/5, choice, collision, debug API |
| Smoke (4) | `node test/smoke.test.js` | **4/4 PASS** — script load, UI element, debug hook, createGame |
| Playwright (28) | `npx playwright test` | **28/28 PASS** — 1.2m |

## Chi tiết Playwright 28 test

- **e2e (5)**: AC-2 (mới — mèo di chuyển), AC-14a chơi thật title→sinh nhật (45s), AC-14b title→game over (22s), AC-3/AC-4 mood+SFX, AC-13 debug API
- **visual (23)**: 17 shot scene + R1 freeze determinism + **AC-1 pixel mèo tại spawn** (mới) + **AC-4 pixel nhà khớp wall cam=160** (mới) + **AC-10 camera scroll HALLWAY scare5** (mới) + **AC-5 mèo hiện diện 6 shot** (mới) + AC-12 COMPARISON.md

## Tọa độ test đã cập nhật (÷3 logical)

- core.test.js: 11 vị trí player (263/287/7/63,73/13/143/3/303/53,43 + xuyên tường 263,30)
- e2e.spec.js: moveTo hai tầng (120ms/40ms) + targets (271,70)/(288,50)/(7,20)/(3,20)/(20,20)/(147,50)/(310,45)/(312,45)
- visual.spec.js: setPlayer ÷3 mọi shot + R1 (107,63)

## Verify thủ công

- Playwright repro: START → mèo hiện ở giữa màn hình (cam 30, screen x 77) — ảnh chụp xác nhận
- Camera scroll: player(300,50) GARDEN → nhà mái đỏ hiện nửa phải; HALLWAY player(300,45)+scare5 → skull hiện — ảnh chụp xác nhận
