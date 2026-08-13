# Evaluation — TASK-017 (M3-P5: Backend API server)

> Ngày: 2026-08-13 | Chuỗi: Spec → Critique (18 vấn đề: 4 P1 + 9 P2 + 5 P3) → Implement → Test → Evaluate

## Kết quả test

- **689 passed, 0 skipped** (baseline 669 + 20 mới), coverage **95.10%**
- 20 test mới: test_api.py (14), test_api_chat_serve.py (6)

## Đối chiếu 12 AC

| AC | Nội dung | Kết quả |
|----|----------|---------|
| AC1 | create_app + routers + docs | ✅ /docs 200 |
| AC2 | /health components + score (mapping C2-02) | ✅ |
| AC3 | /events audit + filter (invalid type → code) | ✅ |
| AC4 | /events/ws realtime cross-thread (call_soon_threadsafe) | ✅ thread publish test |
| AC5 | /catalog list + search (populated C2-07 — 11 entries) | ✅ |
| AC6 | /goals list + detail | ✅ |
| AC7 | /skills list + detail | ✅ |
| AC8 | /tools list + detail (6 tools) | ✅ |
| AC9 | /artifacts + /conversations | ✅ |
| AC10 | /prompts + /models | ✅ mock available |
| AC11 | POST /chat → orchestrator → CoderAssistant (offline) | ✅ "generate api" → coding → code |
| AC12 | serve CLI + import; toàn bộ pytest | ✅ `serve --help` + 689 pass |

**12/12 AC đạt.**

## Xử lý critique (18)

- C1-01 pyproject fastapi/uvicorn/httpx ✅; C1-02 [project.scripts] aiagent ✅; C1-03 orchestrator wiring + chat 2 bước ✅; C1-04 WS call_soon_threadsafe + unsubscribe ✅
- C2-01 SkillsSettings ✅; C2-02 health mapping ✅; C2-03 intent hint ✅; C2-04 error mapping ✅; C2-05 queue maxsize + finally unsubscribe ✅; C2-06 invalid_event_type ✅; C2-07 catalog populate ✅; C2-08 conversations format + wire ✅; C2-09 /sandbox ✅
- C3-01..05 prompts format, models available, WS realtime-only note, lazy import serve, docs ✅

## Bài học mới

1. RuntimeKernel không có `.services` — resolve qua `kernel.container.resolve(X)`
2. ModelRegistry.default() cần register trước ("mock")
3. FastAPI pydantic extra=forbid → 422 (RequestValidationError), không phải 400
4. ArtifactService.list() không nhận limit — slice sau
5. `websocket.app.state.kernel.bus` (property `bus`, không phải `event_bus`)

## Kết luận

**TASK-017 ĐẠT — 12/12 AC, 689 tests pass, coverage 95.10%, git sạch sau commit.**
