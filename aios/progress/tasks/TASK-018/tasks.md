# Tasks — TASK-018 (M3-P5: Dashboard SPA)

> Breakdown checklist các bước implement. Mọi bước ghi LOG.md song song.

## Checklist

- [x] T1 — Scaffold Vite + React 18 + TS: package.json, tsconfig, vite.config.ts (proxy /api ws:true), index.html
- [x] T2 — `src/api.ts`: 3-envelope fetch wrapper (C1-02)
- [x] T3 — `src/ws.ts`: WebSocket reconnect 3s + MockWebSocket stub (C1-03/05)
- [x] T4 — `src/App.tsx`: 10 tabs nav + view switch (AC2)
- [x] T5 — `src/views/ChatView.tsx`: POST /chat + render (AC5)
- [x] T6 — `src/views/EventTimeline.tsx`: GET /events + WS live append (AC6)
- [x] T7 — `src/views/HealthView.tsx`: score + components (AC7)
- [x] T8 — `src/views/MemoryView.tsx`: ?session_id=api (C1-01)
- [x] T9 — Các view còn lại (Workflow/Tools/Artifacts/Skills/Models/Prompts) + no-data states (AC8)
- [x] T10 — `src/views/ArtifactBrowser.tsx`: list-only render artifact_type (C1-06)
- [x] T11 — Tests: `src/__tests__/api.test.ts` (6) + `ws.test.ts` (2) + `App.test.tsx` (4)
- [x] T12 — `npm run build` (tsc + vite build) + README ngắn
