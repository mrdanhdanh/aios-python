# Critique vòng 1 — TASK-017 (M3-P5: Backend API server)

> Ngày: 2026-08-13 | Reviewer: critic subagent | Spec: `spec.md`

## Đánh giá chung

**2/5 — cần sửa trước khi implement.** 4 P1 chặn implement: (1) fastapi/uvicorn CHƯA cài trong pyproject; (2) không có entry point `aiagent`; (3) Orchestrator không có trong wiring (chat không build được); (4) WS sync→async cần pattern `call_soon_threadsafe`. + 9 P2 + 5 P3.

## Vấn đề (18) + quyết định resolve

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C1-01 | P1 | fastapi/uvicorn chưa trong pyproject; TestClient cần httpx | Thêm `fastapi`, `uvicorn` vào [project.dependencies]; `httpx` vào dev; bỏ câu "đã cài" |
| C1-02 | P1 | Không có entry `aiagent` | Thêm `[project.scripts] aiagent = "aios_core.workflow.cli:main"` |
| C1-03 | P1 | Orchestrator không trong wiring | Thêm key "orchestrator": `Orchestrator(default_rules(), WorkflowMatcher(WorkflowLibrary()), Planner(), Normalizer(WorkflowLibrary()), AgentSelector(), model=ModelRegistry.default())` + chat 2 bước (orchestrator→intent → registry.resolve_by_intent) |
| C1-04 | P1 | WS cross-thread deadlock | Pattern bắt buộc: `loop = get_running_loop()` + `queue = asyncio.Queue(maxsize=500)` + sync handler `loop.call_soon_threadsafe(queue.put_nowait, ev.to_dict())` + `try/finally: unsubscribe` |
| C2-01 | P2 | Không có SkillsSettings | Thêm `SkillsSettings(db_path="aios/data/skills.db")` vào config.py + config.yaml |
| C2-02 | P2 | Health format không khớp HealthRegistry | Mapping: `ok = status != UNHEALTHY`, `detail = message`, `health_score = 1 - _STATUS_WEIGHT[status]/2` (healthy=1.0, degraded=0.5, unhealthy=0.0) |
| C2-03 | P2 | AC11 input không đạt intent coding | Input mẫu `{"text": "generate api for users"}` → orchestrator → coding; field `intent` = hint optional (nếu có → resolve thẳng registry) |
| C2-04 | P2 | "lỗi → 400" không xác định | 400 = validation fail + assistant status="error" (code="assistant_error"); 500 = exception |
| C2-05 | P2 | WS leak subscriber | try/finally unsubscribe + queue maxsize 500 (drop-oldest) |
| C2-06 | P2 | /events?type= string → EventType | Invalid → 400 code="invalid_event_type" |
| C2-07 | P2 | Catalog production rỗng | create_app populate: index tool/skill/assistant/prompt/model entries |
| C2-08 | P2 | /conversations format mơ hồ + memory không wire | `{"data": [{"id", "messages"}]}` (get_messages per id); wire ConversationMemory từ settings.memory |
| C2-09 | P2 | SandboxPool mồ côi | Thêm `GET /api/v1/sandbox` trả pool stats |
| C3-01 | P3 | /prompts format | `{"data": [{"id", "name", "version", "description"}]}` |
| C3-02 | P3 | /models available | `is_available()` per model |
| C3-03 | P3 | WS không replay | Ghi rõ "WS = realtime only; lịch sử qua GET /events" |
| C3-04 | P3 | CLI serve import nặng | `_serve()` lazy-import `from ..api.serve import run` |
| C3-05 | P3 | /docs phụ thuộc | Giữ docs mặc định; test /openapi.json 200 |

## Kết luận

- [x] **Cần sửa trước khi implement** — 4 P1 + 9 P2 + 5 P3 (resolve cùng đợt).
- **Trạng thái: RESOLVED 18/18** (spec.md đã cập nhật).
