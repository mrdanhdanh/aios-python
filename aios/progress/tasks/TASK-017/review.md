# Review — TASK-017 (M3-P5: Backend API server)

> 2026-08-13 | Reviewer: reviewer subagent (tự review qua code + test)

## Đánh giá

**APPROVED (có điều kiện → resolved).**

### Các điểm kiểm tra

1. **Kiến trúc (INV-003/006)**: `chat.py` gọi `regs["orchestrator"].handle()` → `regs["assistants"].resolve_by_intent()` → `assistant.handle()`. KHÔNG gọi `Tool(...)`/`ExecutionService(...)` trực tiếp. Grep `Tool(`/`ExecutionService(` trong `api/` → empty (duy nhất `bind_capabilities` lambda trong `wiring.py` là registry binding, không phải execution). ✅
2. **DI (INV-005)**: `create_app(settings, kernel, registries)` injectable; test inject fake app. ✅
3. **Contract (INV-008)**: `ChatRequest`/`ChatResponse` `extra="forbid"` → 422 test pass. ✅
4. **Event (INV-009)**: WS forward thực sự — `test_ws_events_realtime` publish cross-thread nhận đúng event. ✅
5. **Offline-first**: `test_chat_coding_intent` ("generate api for users" → coding, "generated code" trong response) chạy với MockModel 0 real call. ✅
6. **Testability**: 689 pass, 0 skip, coverage 95.10%, 12/12 AC. ✅

### Điều kiện (R2/R3 — resolved trong implement)

- R2-1: error envelope nhất quán `{error:{code,message}}` — done.
- R2-2: WS queue backpressure maxsize 500 — done.
- R3-1: `/sandbox` GET stats read-only — done.
- R3-2: catalog populate 11 entries — done.

## Kết luận

**APPROVED — TASK-017 đạt đủ tiêu chí, được phép đánh dấu done.**
