# Implementation — TASK-018 (M3-P5: Dashboard SPA)

> Pointer tới code thật trong repo (git-tracked). Commit: `33b6b05`.

## Cấu trúc đã implement

```
dashboard/
├── package.json            # react, react-dom, vite, typescript, vitest, testing-library
├── tsconfig.json
├── vite.config.ts          # dev proxy /api → 127.0.0.1:8000 (ws: true)
├── index.html
├── src/
│   ├── main.tsx            # root render
│   ├── App.tsx             # 10 tabs nav + view switch
│   ├── api.ts              # 3-envelope fetch wrapper
│   ├── ws.ts               # WebSocket reconnect 3s + MockWebSocket stub
│   └── views/
│       ├── ChatView.tsx
│       ├── WorkflowView.tsx
│       ├── EventTimeline.tsx
│       ├── ToolUsage.tsx
│       ├── MemoryView.tsx
│       ├── ArtifactBrowser.tsx   # render artifact_type
│       ├── SkillMarketplace.tsx
│       ├── ModelUsage.tsx
│       ├── PromptInspector.tsx
│       └── HealthView.tsx
└── src/__tests__/
    ├── api.test.ts         # 6 tests
    ├── ws.test.ts          # 2 tests
    └── App.test.tsx        # 4 tests (10 tabs, chat, health, no-data)
```

## Tiêu chí đạt

- vitest **12/12 pass**, `vite build` OK.
- 10/10 AC (xem `evaluation.md`).
- Không vi phạm INV-006 (chỉ gọi API qua HTTP).
