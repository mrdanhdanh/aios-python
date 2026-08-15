# Tasks — TASK-017 (M3-P5: Backend API server)

> Breakdown checklist các bước implement. Mọi bước ghi LOG.md song song.

## Checklist

- [x] T1 — Cài fastapi/uvicorn/httpx; thêm `[project.scripts] aiagent` (C1-01/02)
- [x] T2 — `app.py`: `create_app(settings, kernel, registries)` + CORS + error handlers (AC1)
- [x] T3 — `wiring.py`: `build_registries` (orchestrator + 10 registries, catalog populate) (C1-03/07)
- [x] T4 — `routers/health.py`: mapping HealthRegistry (C2-02, AC2)
- [x] T5 — `routers/events.py`: GET audit + WS realtime `call_soon_threadsafe` + unsubscribe (C1-04/05/06, AC3/4)
- [x] T6 — `routers/catalog.py`: list + search (AC5)
- [x] T7 — `routers/goals.py`, `skills.py`, `tools.py`: list + detail (AC6/7/8)
- [x] T8 — `routers/memory.py`: /artifacts + /conversations (C2-08, AC9)
- [x] T9 — `routers/prompts.py`, `models.py`: list (C3-01/02, AC10)
- [x] T10 — `routers/chat.py`: ChatRequest/Response extra=forbid, orchestrator→assistant (C2-03/04, AC11)
- [x] T11 — `routers/sandbox.py`: GET stats (C2-09)
- [x] T12 — `serve.py` + `cli.py` subcommand `serve --host --port` (lazy import) (C3-04, AC12)
- [x] T13 — Tests: `test_api.py` (14) + `test_api_chat_serve.py` (6) — 689 pass, 95.10%
