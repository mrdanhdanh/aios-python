# TASK-084 — Survey version `0.1.0` / `1.0.0` (bảng phân loại bump/giữ)

> Khảo sát toàn bộ `backend/src` + `backend/tests` (RESOLVED C1-06 + C2-04 + review R3).
> Phân loại: **AIOS version** (bump lên 1.1.0) vs **component version** (giữ nguyên).

## Src — AIOS version → BUMP

| File:dòng | Giá trị cũ | Giá trị mới | Lý do |
|-----------|-----------|-------------|-------|
| `src/aios_core/__init__.py:3` | `"0.1.0"` | `"1.1.0"` | System version — điểm gốc (AC1) |
| `src/aios_core/api/app.py:49` | `FastAPI(version="0.1.0")` | `version=__version__` | API metadata (AC11) |
| `src/aios_core/contracts/catalog.py` (10 contract) | `"1.0.0"` | `"1.1.0"` | Contract 1.1 — minor bump backward-compatible (AC2) |
| `src/aios_core/plugins/manager.py:68` | `"1.0.0"` | `"1.1.0"` | Plugin manager default aios version (AC4) |
| `src/aios_core/ecosystem/marketplace.py:85` | `"1.0.0"` | `"1.1.0"` | TrustChain default aios version (AC4) |
| `src/aios_core/ecosystem/marketplace.py:268` | `"1.0.0"` | `"1.1.0"` | MarketplaceRegistry property (AC4 — chỗ thứ 2) |

## Src — Component version → GIỮ NGUYÊN

| File:dòng | Giá trị | Lý do giữ |
|-----------|---------|-----------|
| `src/aios_core/contracts/catalog.py` (plugin `deprecated_in`) | `"1.0.0"` | R3 review: test check-full phụ thuộc plugin còn deprecated; deprecated_in = mốc deprecate lịch sử |
| `src/aios_core/ecosystem/devkit.py:34,108` | `"0.1.0"` | Scaffold template version riêng của devkit (C2-04) |
| `src/aios_core/kernel/services/policy.py:17` | `"0.1.0"` | `DEFAULT_POLICY_VERSION` — version schema policy, không phải system (C2-04) |
| `src/aios_core/upgrade/migration.py:215` | `"1.0.0"` | Default `compatible` trong migration data (component) |
| `src/aios_core/workflow/cli.py:727` | `"1.0.0"` | Sample manifest trong CLI (component data) |
| `src/aios_core/harness/{benchmark,doctor,evaluation,testing,verification}/*` | `"1.0.0"` | Version của từng harness component |
| `src/aios_core/enterprise/contracts.py:147` | `"1.0.0"` | Enterprise component |
| `src/aios_core/tools/base.py:78` | `"1.0.0"` | Tool component |
| `src/aios_core/skills/sources.py` | `"1.0.0"` | Skill component |
| `src/aios_core/rendering/workflows.py` | `"1.0.0"` | Rendering component |
| `src/aios_core/ecosystem/distiller.py:173` | `"1.0.0"` | Distiller component |
| `src/aios_core/harness/certification/golden.py:287-299` | `"1.0.0"` | Golden scenario component data (không assert system version) |

## Tests — SỬA (assert system version)

| File:dòng | Assert cũ | Assert mới | Lý do |
|-----------|-----------|-----------|-------|
| `tests/test_models.py:104` | `"0.1.0" in meta.version` | `"1.1.0" in meta.version` | System version (AC9) |
| `tests/test_contracts_catalog.py::test_cli_contract_list` | `"1.0.0" in out` | `"1.1.0" in out` | Output contract list (C2-03) |

## Tests — GIỮ NGUYÊN (component version / semantics)

- `test_cli.py:12`, `test_definition.py:101` — workflow YAML fixture version (component)
- `test_contracts.py:36,54`, `test_contracts_catalog.py:84` — CompatibilityChecker 0.x semantics
- `test_ecosystem_devkit.py:31`, `test_policy.py:71,126` — component version (C2-04 xác nhận KHÔNG sửa)
- `test_ecosystem_marketplace.py:21`, `test_plugins.py:159,176,194`, `test_metadata.py`, `test_semver.py` — fixtures/semantics component
- `test_import.py:25` — regex `\d+\.\d+\.\d+` vẫn khớp `1.1.0` (tự pass)
- `test_models.py:103,276,313` — `meta.version == __version__` (tự phản ánh, pass)
- `test_planner.py:40` — dùng `__version__` (tự phản ánh, pass)
- `test_contracts_catalog.py:100` — `plugin.deprecated_in == "1.0.0"` (giữ đúng R3)
