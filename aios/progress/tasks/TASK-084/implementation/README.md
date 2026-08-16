# TASK-084 — Implementation artifacts

## Deliverables

| File | Nội dung |
|------|----------|
| `backend/src/aios_core/upgrade/compatibility.py` | **MỚI** — Compatibility Matrix registry (CompatibilityEntry + CompatibilityMatrix + DEFAULT_ENTRIES 14 entry + check fail-closed). `AIOS_VERSION = "1.1.0"` literal (R2 — không import `__version__` do allow-list upgrade/) |
| `backend/src/aios_core/__init__.py` | Bump `__version__` `"0.1.0"` → `"1.1.0"` (M12 Issue #7) |
| `backend/src/aios_core/api/app.py` | `FastAPI(version=__version__)` (bỏ hardcode "0.1.0") |
| `backend/src/aios_core/contracts/catalog.py` | 10 contract `1.0.0` → `1.1.0`; `deprecated_in` plugin GIỮ `1.0.0` (R3) |
| `backend/src/aios_core/plugins/manager.py` | Default `aios_version` → `"1.1.0"` |
| `backend/src/aios_core/ecosystem/marketplace.py` | 2 chỗ default → `"1.1.0"` (TrustChain + MarketplaceRegistry) |
| `backend/src/aios_core/workflow/cli.py` | CLI `compat list/check` (JSON 1 dòng, exit 0/1) |
| `backend/tests/test_compatibility_matrix.py` | **MỚI** — 19 test (unit + CLI) |
| `backend/tests/test_architecture.py` | Allow-list + `aios_core.plugins.compat` (C2-01) |
| `backend/tests/test_models.py` | `"0.1.0"` → `"1.1.0"` (assert system version) |
| `backend/tests/test_contracts_catalog.py` | `test_cli_contract_list` assert `"1.1.0"` |
| `aios/progress/tasks/TASK-084/implementation/survey.md` | Bảng phân loại bump/giữ ~25 vị trí |

## Kết quả

- Full suite: **2071 PASS / 0 FAIL** (baseline 2052 + 19 mới), coverage 93.02%
- CLI thật: `system status` 1.1.0 · `contract list` 1.1.0 · `compat list` 14 entries · `compat check` fail-closed exit 0/1 · openapi 1.1.0
- arch-health 0 violations · doctor healthy
