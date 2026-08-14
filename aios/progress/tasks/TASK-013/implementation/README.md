# TASK-013 — Implementation artifacts

| Artifact | Đường dẫn |
|----------|-----------|
| Assistant base (template method `handle` + event sink best-effort) | `backend/src/aios_core/agents/base.py` |
| General assistant (deterministic template, model optional) | `backend/src/aios_core/agents/general.py` |
| Coder assistant (7 steps + Self-Fix loop) | `backend/src/aios_core/agents/coder.py` |
| Doctor assistant (6 bước + Safety Layer 4 bất biến) | `backend/src/aios_core/agents/doctor.py` |
| System Doctor (probe + score + FIX_HINTS) | `backend/src/aios_core/agents/system_doctor.py` |
| Registry (`resolve_by_intent` qua selector) | `backend/src/aios_core/agents/registry.py` |
| Tests | `test_agents_base.py`, `test_coder_assistant.py`, `test_doctor_assistant.py`, `test_system_doctor.py`, `test_assistant_registry.py` |

## Quyết định kỹ thuật (qua critique ×2 + review)
- Hard isolation (INV-001/002): package CHỈ import `models.base`/`models.errors` + pydantic
  + stdlib; mọi service qua callable injectable (`event_sink`, pipeline steps).
- Agent KHÔNG import `tools`/`capabilities`/`kernel` (verified by grep + AST scan).
- Safety Layer: Doctor không bao giờ kê đơn trước (d), disclaimer chỉ khi ok,
  high→emergency redirect.
