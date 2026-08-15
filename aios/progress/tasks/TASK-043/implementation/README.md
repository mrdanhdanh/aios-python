# TASK-043 — M8-E1 Public AIOS SDK — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in `sdk/python/`
> (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `sdk/python/aios/` — Public SDK Python v1:
  - `contracts.py` / DTO (extra=forbid, strict)
  - `agent.py`, `tool.py`, `capability.py`, `workflow.py` — component decorators + base classes
  - `client.py` — `Client` 4 operation (chat/execute/status/evaluate) qua `Transport` injection
  - `metadata.py` — component metadata + validation deterministic
  - `README.md` — quickstart
- KHÔNG import `aios_core`/`backend` (public API độc lập)

## Key behavior
- Developer viết `class MyAgent(Agent)` / `@aios.tool` — không cần biết RuntimeKernel
- Client dùng transport injection (test bằng mock transport)
- DAG validation cho Workflow engine-independent

## Verification
- SDK tests: **5 passed** (offline, không cần backend)
- Backend full suite regression: **1793 passed** (M9 baseline) — không đổi backend
