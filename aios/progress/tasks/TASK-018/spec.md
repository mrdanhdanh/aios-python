# TASK-018 — M3-P5: Dashboard SPA (React + Vite, 10 views)

**Metadata**: TASK-018 | M3/P5 | 2026-08-13 | draft | AIOS Orchestrator
**Module đích**: `dashboard/` (React + Vite SPA)

## 1. Mục tiêu
Dashboard web đọc hệ thống AIOS qua API (TASK-017): 10 views theo PLAN P5 — Chat, Workflow Viewer, Event Timeline (WebSocket), Tool Usage, Memory Viewer, Artifact Browser, Skill Marketplace, Model Usage, Prompt Inspector, Health Dashboard.

## 2. Phạm vi
**In**: `dashboard/` — Vite + React 18; 10 views; API client (`src/api.ts` — fetch wrapper với base URL từ env `VITE_API_BASE` default `http://127.0.0.1:8000`); WS client (`src/ws.ts` — EventSource? Không — WebSocket tới `/api/v1/events/ws`); router đơn giản (state-based tabs, không cần react-router); layout + nav.
**Out**: auth, deploy, test E2E, SSR, i18n, CSS framework nặng (dùng CSS thuần tối giản).

## 3. Kiến trúc
```
dashboard/
├── package.json          # react, react-dom, vite, typescript, vitest
├── vite.config.ts        # dev proxy /api → 127.0.0.1:8000
├── index.html
├── src/
│   ├── main.tsx          # root render
│   ├── App.tsx           # tab nav + view switch
│   ├── api.ts            # fetch wrapper: get(path) → data (parse {data}|{error})
│   ├── ws.ts             # connectEvents(onEvent): WebSocket wrapper (reconnect 3s)
│   └── views/
│       ├── ChatView.tsx        # text → POST /chat → response
│       ├── WorkflowView.tsx    # GET /goals + /catalog (workflow entries)
│       ├── EventTimeline.tsx   # GET /events + WS live append
│       ├── ToolUsage.tsx       # GET /tools + /sandbox
│       ├── MemoryView.tsx      # GET /conversations + /artifacts
│       ├── ArtifactBrowser.tsx # GET /artifacts (chi tiết)
│       ├── SkillMarketplace.tsx# GET /skills
│       ├── ModelUsage.tsx      # GET /models
│       ├── PromptInspector.tsx # GET /prompts
│       └── HealthView.tsx      # GET /health
```

## 4. AC
- AC1: `npm install` + `npm run build` thành công (vite build — TS check)
- AC2: App render 10 tabs; mỗi tab mount view tương ứng (test: vitest + render App → tìm tab labels)
- AC3: `api.ts get()` parse `{data}` / throw `{error.message}` (unit test với fetch mock)
- AC4: `ws.ts` connect + nhận event + reconnect khi đóng (unit test với mock WebSocket)
- AC5: ChatView gọi POST /chat và hiển thị response (test: mock fetch → render text)
- AC6: EventTimeline: GET /events render list + WS event append (test: mock fetch + ws)
- AC7: HealthView render score + components (test mock fetch)
- AC8: các view còn lại render "no data" state khi API rỗng (test: mock fetch [])
- AC9: dev proxy /api → 127.0.0.1:8000 trong vite.config
- AC10: vitest pass toàn bộ + build pass + README ngắn (chạy: `aiagent serve` + `npm run dev`)

## 5. Test
- `src/__tests__/api.test.ts`, `ws.test.ts`, `App.test.tsx` (vitest + jsdom + @testing-library/react)
- `npm run test` (vitest run) + `npm run build` (tsc + vite build)
