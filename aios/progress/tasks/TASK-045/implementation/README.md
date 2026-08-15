# TASK-045 — M8-E3 Extension Contracts — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `extension/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/extension/contracts.py` — `ApiNamespace` enum (internal/public/extension/experimental) + `ExtensionContract` (id, version, namespace, requires list, extra=forbid) + `CompatibilityResult` (ok, errors, warnings)
- `backend/src/aios_core/extension/matrix.py` — `CompatibilityMatrix.check(requires, runtime_versions)` constraint `^X.Y.Z`/`>=X.Y.Z`/`X.Y.Z`/`*`; fail-fast khi thiếu runtime contract
- `backend/src/aios_core/extension/errors.py`
- `backend/src/aios_core/extension/__init__.py`

## Key behavior
- 4 API namespace: Internal (aios.core.internal.*) ❌ / Public (aios.sdk.*) ✅ / Extension (aios.extension.*) ✅ / Experimental (aios.experimental.*) ⚠️
- Compatibility Matrix fail-closed: plugin không được load nếu incompatible (không crash Runtime lúc startup)
- Import allow-list: extension/ chỉ pydantic/stdlib + semver

## Verification
- `pytest` full suite: **1639 passed (baseline 1584 + 55 cho batch TASK-045..049)** — xem `test.md`
