# TASK-064 — Test (Contract 1.0)

## Kết quả test — 2026-08-15

`tests/test_contracts_catalog.py` — **20/20 pass** (`--no-cov`):

| Test | AC | Kết quả |
|------|----|---------|
| test_catalog_has_10_contracts | AC1 | ✅ |
| test_every_contract_has_7_fields | AC2 | ✅ |
| test_schema_refs_importable (importlib thật) | AC2/C1-01 | ✅ |
| test_definition_extra_forbid + id lowercase | AC2 | ✅ |
| test_semver_compat_via_compatibility_checker (patch/minor/major) | AC3 | ✅ |
| test_catalog_versions_are_semver | AC3 | ✅ |
| test_plugin_is_deprecated_with_migration | AC4 | ✅ |
| test_deprecated_requires_migration_path (fail-closed) | AC4 | ✅ |
| test_runtime_artifact_frozen | AC4 | ✅ |
| test_matrix_default_all_ok_except_plugin_warning (0 breaking/1 warning) | AC5 | ✅ |
| test_matrix_removed_is_breaking + broken_schema_ref_is_breaking | AC5 | ✅ |
| test_deprecated_usage_detected / clean / unknown ignored | AC6 | ✅ |
| test_cli_contract_check / list / check-full | AC7/AC8 | ✅ |
| test_format_matrix_stable | AC7 | ✅ |

## CLI chạy thật

```
$ python -m aios_core.workflow.cli contract check
agent       | 1.0.0  | stable      | ✓ compatible
...
plugin      | 1.0.0  | deprecated  | ⚠ deprecated since 1.0.0 — migration: plugin v2 → Ecosystem Entry ...
Breaking changes: 0 · Warnings: 1        (exit 0)
$ python -m aios_core.workflow.cli contract list
plugin      | 1.0.0     | deprecated
runtime     | 1.0.0     | frozen
... (10 contract)
```

## Regression
Full suite backend: **1815 passed** (baseline 1793 + 20 TASK-064 + 2 INV-008/012 TASK-063).
Không breaking change với M1–M9 (AC9) ✅.
