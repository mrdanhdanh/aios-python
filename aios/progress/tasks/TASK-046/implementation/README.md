# TASK-046 — M8-E4 Ecosystem Registry — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `ecosystem/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/ecosystem/contracts.py` — `EntryKind` 10 + `Publisher` + `EcosystemEntry` (extra=forbid)
- `backend/src/aios_core/ecosystem/registry.py` — `EcosystemRegistry` SQLite upsert + search 5 trường (id/name/description/kind/version) + list, persist qua restart
- `backend/src/aios_core/ecosystem/errors.py`
- `backend/src/aios_core/ecosystem/__init__.py`
- `backend/src/aios_core/config.py` — `EcosystemSettings`
- `backend/src/aios_core/api/wiring.py` — `regs["ecosystem"]`
- `backend/src/aios_core/workflow/cli.py` — CLI `ecosystem search`

## Key behavior
- Registry v2: Agents · Capabilities · Tools · Skills · Workflows · Models · Providers · Plugins · Integrations · Extensions (10 kinds)
- Discovery: `aios search <query>` → sorted deterministic; duplicate (kind, id) → update không lỗi
- Pure index/search — KHÔNG nhúng certification/marketplace (test `pure_index`)

## Verification
- `pytest` full suite: **1639 passed** — xem `test.md` + `tests/test_ecosystem_registry.py`
