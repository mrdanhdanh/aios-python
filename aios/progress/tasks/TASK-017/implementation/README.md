# Implementation — TASK-017 (M3-P5: Backend API server)

> Pointer tới code thật trong repo (git-tracked). Commit: `16c998f`.

## Cấu trúc đã implement

```
backend/src/aios_core/api/
├── __init__.py
├── app.py                 # create_app(settings, kernel, registries) — 11 routers + CORS + error handlers
├── wiring.py              # build_registries — RuntimeKernel.create + 10 registries + catalog populate
├── serve.py               # run(host, port) — uvicorn runner
└── routers/
    ├── health.py          # GET /health
    ├── events.py          # GET /events + WS /events/ws (call_soon_threadsafe + unsubscribe)
    ├── catalog.py         # GET /catalog, /catalog/search
    ├── goals.py           # GET /goals, /goals/{id}
    ├── skills.py          # GET /skills, /skills/{id}
    ├── tools.py           # GET /tools, /tools/{id}
    ├── memory.py          # GET /artifacts, /conversations
    ├── prompts.py         # GET /prompts
    ├── models.py          # GET /models
    ├── chat.py            # POST /chat — orchestrator → assistants.resolve_by_intent
    ├── sandbox.py         # GET /sandbox
    ├── observability.py   # GET /metrics, /prompt-history, /doctor, /arch-health, /evaluations
    └── orchestrator_v2.py # GET /orchestrator-v2/*

backend/src/aios_core/workflow/cli.py   # subcommand `aiagent serve --host --port` (lazy import)
backend/tests/test_api.py               # 14 tests (AC1–AC10)
backend/tests/test_api_chat_serve.py    # 6 tests (AC11/AC12 + WS realtime)
```

## Tiêu chí đạt

- 689 passed, 0 skipped, coverage 95.10% (tại M3).
- 12/12 AC (xem `evaluation.md`).
- Không vi phạm INV-001..010/013 (API là composition root, DI qua `RuntimeKernel.create`).
