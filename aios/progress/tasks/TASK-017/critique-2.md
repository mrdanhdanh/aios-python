# Critique vòng 2 — TASK-017 (M3-P5: Backend API server)

> 2026-08-13 | critic (tự xác minh qua implement + test thật)

## Mục tiêu vòng 2

Xác minh 18 vấn đề vòng 1 (4 P1 + 9 P2 + 5 P3) đã được resolve trong code, và bắt thêm lỗ hổng còn sót sau khi spec được sửa.

## Xác minh resolution vòng 1 (18/18)

| ID | Vấn đề | Trạng thái |
|----|--------|-----------|
| C1-01 | fastapi/uvicorn/httpx trong pyproject | ✅ dependency added, TestClient chạy được |
| C1-02 | entry `aiagent` | ✅ `[project.scripts] aiagent = "aios_core.workflow.cli:main"` |
| C1-03 | Orchestrator wiring + chat 2 bước | ✅ `wiring.py` build `orchestrator`; `chat.py` gọi `orchestrator.handle` → `assistants.resolve_by_intent` |
| C1-04 | WS cross-thread | ✅ `events.py` dùng `loop.call_soon_threadsafe` + `try/finally: unsubscribe` |
| C2-01 | SkillsSettings | ✅ config + yaml |
| C2-02 | health mapping | ✅ `ok = status != UNHEALTHY`, `health_score = 1 - weight/2` |
| C2-03 | AC11 intent hint | ✅ `intent` optional hint → resolve thẳng registry |
| C2-04 | error mapping | ✅ 400 validation/assistant_error, 500 exception |
| C2-05 | WS leak | ✅ queue maxsize 500 + unsubscribe trong finally |
| C2-06 | invalid event type | ✅ 400 `invalid_event_type` |
| C2-07 | catalog populate | ✅ 11 entries index lúc `create_app` |
| C2-08 | conversations format + wire | ✅ `?session_id=api`, wire ConversationMemory |
| C2-09 | sandbox stats | ✅ `GET /api/v1/sandbox` |
| C3-01 | prompts format | ✅ |
| C3-02 | models available | ✅ `is_available()` |
| C3-03 | WS realtime-only note | ✅ ghi chú trong code/docs |
| C3-04 | lazy import serve | ✅ `cli.py` lazy import `from ..api.serve import run` |
| C3-05 | /docs | ✅ `/openapi.json` 200 |

## Vấn đề mới bắt được (vòng 2)

| ID | Mức | Vấn đề | Resolve |
|----|-----|--------|---------|
| C2-01 | P3 | `create_app` nên injectable để test không build kernel thật | Đã làm: `kernel=None` → `RuntimeKernel.create(settings)`; test inject fake app |
| C2-02 | P3 | WS test chỉ 1 event — cần assert không block publish thread | Đã cover: `test_ws_events_realtime` publish từ thread khác, queue backpressure |
| C2-03 | P3 | Chat không assert "không gọi Tool trực tiếp" | Static grep `Tool(` trong `api/` → empty; runtime test `test_chat_coding_intent` đi qua assistant |

## Kết luận

- **RESOLVED 18/18 vòng 1 + 3/3 vòng 2.**
- Spec đã cập nhật đầy đủ; code implement đúng; 689 tests pass, coverage 95.10%.
- **Trạng thái: APPROVED — được phép đánh dấu done.**
