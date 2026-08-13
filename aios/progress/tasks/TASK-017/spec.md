# TASK-017 — M3-P5: Backend API server (FastAPI REST + WebSocket) cho Dashboard

**Metadata**
- Task ID: `TASK-017`
- Milestone / Phase: M3 (Desktop Edition) / P5 (Dashboard)
- Ngày: 2026-08-13
- Trạng thái: `draft`
- Owner: AIOS Orchestrator
- Module đích: `backend/src/aios_core/api/` (package mới) + CLI subcommand `aiagent serve`

---

## 1. Mục tiêu

Cung cấp REST API + WebSocket cho Dashboard SPA (TASK-018) và VS Code extension (TASK-019) đọc/điều khiển hệ thống AIOS: system status, events (timeline realtime), catalog, goals, skills, tools, memory/artifacts, prompts, models, chat/completion. Tất cả endpoint đều **đọc-only + 1 action chat** (v1 — không mutation phức tạp).

## 2. Phạm vi

### In (`backend/src/aios_core/api/`)
1. `app.py` — FastAPI app factory `create_app(settings, kernel=None)`: CORS cho dashboard dev; routers mount; lifespan đóng kết nối
2. `routers/health.py` — `GET /api/v1/health` (HealthRegistry → components ok/fail + score)
3. `routers/events.py` — `GET /api/v1/events?limit=&type=` (EventService.query_audit — đọc DB) + `WS /api/v1/events/ws` (realtime: subscriber vào EventBus → forward JSON)
4. `routers/catalog.py` — `GET /api/v1/catalog` (SystemCatalog entries), `GET /api/v1/catalog/search?q=`
5. `routers/goals.py` — `GET /api/v1/goals?status=`, `GET /api/v1/goals/{id}`
6. `routers/skills.py` — `GET /api/v1/skills?state=`, `GET /api/v1/skills/{id}`
7. `routers/tools.py` — `GET /api/v1/tools`, `GET /api/v1/tools/{id}`
8. `routers/memory.py` — `GET /api/v1/artifacts`, `GET /api/v1/conversations?session_id=`
9. `routers/prompts.py` — `GET /api/v1/prompts`
10. `routers/models.py` — `GET /api/v1/models`
11. `routers/chat.py` — `POST /api/v1/chat` (body: {text, intent?}) → Orchestrator.handle → response (offline-first: mock model mặc định)
12. `serve.py` — `aiagent serve --host --port`: uvicorn runner (CLI subcommand mới trong `workflow/cli.py` hoặc script entry)
13. Wire: `RuntimeKernel.create()` + registries (SystemCatalog, AssistantRegistry, ToolRegistry, SkillManager, GoalManager, SandboxPool, PromptRegistry, ModelRegistry, HealthRegistry)

### Out
- KHÔNG auth/security (localhost dev — ghi rõ)
- KHÔNG mutation phức tạp (create/update goal, skill lifecycle qua API — chỉ đọc + chat)
- KHÔNG WebSocket cho mọi thứ (chỉ events)
- KHÔNG pagination nâng cao (limit/offset đơn giản)
- KHÔNG test E2E UI (TASK-018)
- KHÔNG SDK TS (TASK-019)

## 3. Input/Output

**Input:** mọi module M1/M2 (kernel, orchestrator, agents, tools, skills, sandbox, goals, catalog, prompts, models, memory)
**Output:** `api/` package + `aiagent serve` + tests (FastAPI TestClient, offline)

## 4. Kiến trúc

- `api/` nằm ở **Infra layer** (Tầng 1 — UI access) — ĐƯỢC import mọi thứ (không bị allow-list ràng buộc; đây là điểm nối UI, không phải Execution Plane)
- Dependencies: fastapi + uvicorn (đã cài) + pydantic v2
- Wiring: `create_app(settings)` tự build `RuntimeKernel` + registries nếu không inject (test inject fake)
- Response format thống nhất: `{"data": ...}` / `{"error": {"code": str, "message": str}}`
- WS events: `{"type": "event", "data": {event dict}}` — forward EventBus subscribe (sync handler → asyncio queue)

## 5. Đặc tả chi tiết

### 5.1 `create_app(settings: Settings | None = None, kernel: RuntimeKernel | None = None, registries: dict | None = None) -> FastAPI`
- settings None → `Settings()`; kernel None → `RuntimeKernel.create(settings)`
- registries dict: {"catalog", "assistants", "tools", "skills", "goals", "sandbox", "prompts", "models", "health"} — None → tự build (build_default_tools, build_skill_manager cần db_path từ settings — GoalsSettings/MemorySettings...)
- CORS: allow_origins=["*"] (dev)
- Error handler chung: SkillError/GoalError/ValueError → 400; Exception → 500 {"error": ...}

### 5.2 Routers (mỗi router: prefix /api/v1/<name>)

**health**: GET / → {"data": {"components": [{name, ok, detail}], "health_score": float}}
**events**: GET / → {"data": [event dicts]} (limit mặc định 100); WS /ws → realtime
**catalog**: GET / → entries; GET /search?q= → tìm theo name/type/capability
**goals**: GET /?status= → list; GET /{id} → chi tiết + tasks
**skills**: GET /?state= → list; GET /{id} → chi tiết
**tools**: GET / → list (id, name, tool_type, capabilities, available); GET /{id}
**memory**: GET /artifacts → ArtifactService list; GET /conversations?session_id=
**prompts**: GET / → PromptRegistry list
**models**: GET / → ModelRegistry list (name, available)
**chat**: POST / {text, intent?} → normalizer→rule→matcher→planner → assistants registry resolve_by_intent → handle → {"data": {"response": str, "intent": str, "status": str}}; lỗi → 400

### 5.3 `serve.py` + CLI
- `aios_core/api/serve.py`: `run(host="127.0.0.1", port=8000)` → `uvicorn.run(app, host, port)`
- `workflow/cli.py` thêm subcommand `serve` (parser riêng: --host, --port) — gọi `run()`

## 6. Ràng buộc & bài học

- Offline-first: chat dùng mock model mặc định; không gọi LLM nếu không cấu hình
- FastAPI TestClient (starlette) — test không cần server thật
- WS test: `TestClient.websocket_connect` — kiểm tra 1 event forward
- Không phá baseline 669; coverage api/ ≥ 80%
- pydantic v2 extra="forbid" cho request models

## 7. Tiêu chí chấp nhận

- [ ] AC1 — `create_app()` khởi tạo được + routers mount (test: GET /docs 200? — docs auto; GET /api/v1/health 200 JSON đúng format)
- [ ] AC2 — /health trả components + score từ HealthRegistry thật
- [ ] AC3 — /events trả audit events (limit/type filter) từ EventService.query_audit
- [ ] AC4 — /events/ws: client nhận event khi bus publish (TestClient WS)
- [ ] AC5 — /catalog list + search hoạt động (SystemCatalog)
- [ ] AC6 — /goals list + detail (GoalManager — goals.db)
- [ ] AC7 — /skills list + detail (SkillManager — skills.db)
- [ ] AC8 — /tools list + detail (ToolRegistry)
- [ ] AC9 — /artifacts + /conversations (ArtifactService, ConversationMemory)
- [ ] AC10 — /prompts + /models list
- [ ] AC11 — POST /chat: intent "coding" → response từ CoderAssistant (offline); lỗi → 400 format đúng
- [ ] AC12 — `aiagent serve --port 0` chạy (subprocess smoke) hoặc import serve.run không lỗi; pytest toàn bộ pass (669 + mới); coverage api/ ≥ 80%

## 8. Kế hoạch test

- `tests/test_api_health.py` (AC1-2)
- `tests/test_api_events.py` (AC3-4)
- `tests/test_api_catalog.py` (AC5)
- `tests/test_api_goals.py` (AC6)
- `tests/test_api_skills.py` (AC7)
- `tests/test_api_tools.py` (AC8)
- `tests/test_api_memory.py` (AC9)
- `tests/test_api_prompts_models.py` (AC10)
- `tests/test_api_chat.py` (AC11)
- `tests/test_api_serve.py` (AC12 — import + CLI parser)
