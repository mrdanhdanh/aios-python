# Evaluation — TASK-018 (M3-P5: Dashboard SPA)

> 2026-08-13 | Spec → Critique (6 vấn đề: 2 P1 + 4 P2) → Implement → Test → Evaluate

## Kết quả

- **vitest 12/12 pass** (api 6, ws 2, App 4)
- **vite build thành công** (tsc + build — 43 modules, dist 149KB)
- 10 views đủ theo PLAN P5

## Đối chiếu 10 AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | npm install + build | ✅ build 1.38s |
| AC2 | 10 tabs render | ✅ App.test |
| AC3 | api.ts 3 envelope | ✅ 6 test (200+error, 400+detail, 500+error, malformed) |
| AC4 | ws.ts connect + reconnect | ✅ 2 test (raw frame + reconnect 3s) |
| AC5 | ChatView POST + render | ✅ |
| AC6 | EventTimeline GET + WS | ✅ (render + ws test) |
| AC7 | HealthView score + components | ✅ |
| AC8 | no-data states | ✅ workflows/skills empty |
| AC9 | proxy /api ws:true | ✅ vite.config |
| AC10 | vitest + build + README | ✅ |

**10/10 AC đạt.**

## Xử lý critique

C1-01 MemoryView `?session_id=api` ✅ · C1-02 api.ts 3 envelope ✅ · C1-03 WS raw dict ✅ · C1-04 relative + proxy ws:true ✅ · C1-05 setup.ts stub WebSocket + deps ✅ · C1-06 ArtifactBrowser list-only ✅

## Bài học

1. `vi.unstubAllGlobals` xóa cả WebSocket stub giữa test files — dùng beforeEach reset instances thay vì unstub
2. jsdom không có WebSocket — phải stub global + export class cho test
3. import.meta.env cần cast khi không có vite/client types

## Kết luận

**TASK-018 ĐẠT — 10/10 AC, vitest 12 pass, build OK.**
