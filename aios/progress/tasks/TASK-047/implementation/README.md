# TASK-047 — M8-E5 Developer Kit — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `ecosystem/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/ecosystem/devkit.py` — `create_scaffold` 5 kinds (plugin/agent/capability/tool/workflow) deterministic no-overwrite; stub dùng SDK public (không import internal)
- `backend/src/aios_core/ecosystem/contracts.py` — manifest contract
- `backend/src/aios_core/workflow/cli.py` — CLI `plugin create`

## Key behavior
- `aios create plugin github` → scaffold `aios.plugin.yaml` + `src/plugin.py` + `tests/` + `README.md` + `pyproject.toml`
- Deterministic: cùng input → cùng output bytes (no timestamp/random)
- Overwrite file tồn tại → lỗi rõ (refusing to overwrite) — không ghi đè
- Kind không hợp lệ → lỗi rõ
- Stub plugin.py compile được (import test)

## Verification
- `pytest` full suite: **1639 passed** — xem `test.md` + `tests/test_ecosystem_devkit.py`
