# Test — TASK-018 (M3-P5: Dashboard SPA)

> Ngày chạy: 2026-08-13 | Môi trường: Node, vitest 2.1.9 (jsdom + testing-library)

## Lệnh chạy

```powershell
cd dashboard; npm install; npm run test   # vitest run
npm run build                             # tsc + vite build
```

## Kết quả

```
Test Files  3 passed (3)
     Tests  12 passed (12)   (api 6, ws 2, App 4)
vite build OK  (43 modules, dist 149KB)
```

## Chi tiết AC test (10/10)

| AC | Test file | Kết quả |
|----|-----------|---------|
| AC1 | `npm run build` | ✅ build 1.38s |
| AC2 | `App.test.tsx` "renders 10 tab labels" | ✅ 10 `tab-*` testid |
| AC3 | `api.test.ts` (6 cases) | ✅ 200+error, 400+detail, 500+error, malformed |
| AC4 | `ws.test.ts` (2 cases) | ✅ raw frame + reconnect 3s |
| AC5 | `App.test.tsx` ChatView | ✅ POST + render response |
| AC6 | `App.test.tsx` EventTimeline | ✅ GET + WS append |
| AC7 | `App.test.tsx` HealthView | ✅ score + components |
| AC8 | `App.test.tsx` no-data | ✅ workflows/skills empty |
| AC9 | `vite.config.ts` | ✅ proxy /api ws:true |
| AC10 | `npm run test` + `npm run build` | ✅ 12 pass + build |

## Ghi chú

- Tại M3: 12 vitest pass. Full suite sau này không ảnh hưởng Dashboard (độc lập).
