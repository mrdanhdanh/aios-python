# TASK-044 — M8-E2 Plugin Runtime — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `plugins/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/plugins/contracts.py` — `PluginManifest`/`PluginType`/`PluginState` (alias SkillState — KHÔNG state machine thứ hai)
- `backend/src/aios_core/plugins/errors.py` — `PluginError` + `PluginStateError`
- `backend/src/aios_core/plugins/compat.py` — compat range parse `*`|`2.x`|semver + check (fail-fast)
- `backend/src/aios_core/plugins/schema.py` — SQLite schema (CHECK sinh từ hằng số)
- `backend/src/aios_core/plugins/manager.py` — lifecycle 10-state reuse `assert_transition` + optimistic concurrency + provides index + dependency check + events `plugin.*`
- `backend/src/aios_core/plugins/registry.py` — read-through
- `backend/src/aios_core/plugins/__init__.py` — facade
- `backend/src/aios_core/config.py` — `PluginSettings`
- `backend/src/aios_core/api/wiring.py` — PluginManager + PluginRegistry + 4 EventType PLUGIN_*
- `backend/src/aios_core/kernel/events.py` (+4 EventType)

## Key behavior
- Plugin lifecycle tái dụng Skills Manager 10 states: RESOLVE → VALIDATE → INSTALL → ENABLE → DISABLE → UNLOAD → RELOAD → UPGRADE → ROLLBACK → REMOVE
- Compat range fail-fast: plugin khai báo `aiOS: {min, max}`; `2.x` upper-bound semantics
- Provides chỉ active; dependent check trước khi disable/remove

## Verification
- `pytest` full suite: **1584 collected (baseline 1560 + 24)**, 115 subset pass; 20 test_plugins + 4 arch test m8_* (xem `test.md`)
