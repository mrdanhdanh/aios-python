"""TASK-064 — Contract 1.0: catalog + checker + CLI (M10-F2)."""

from __future__ import annotations

import pytest

from aios_core.contracts.catalog import (
    CONTRACT_IDS,
    CONTRACTS,
    ContractCatalog,
    ContractDefinition,
    ContractLifecycle,
)
from aios_core.contracts.check import (
    CheckStatus,
    ContractChecker,
    format_matrix,
)


# ---------------------------------------------------------------------------
# AC1: đủ 10 contract
# ---------------------------------------------------------------------------

def test_catalog_has_10_contracts():
    catalog = ContractCatalog()
    assert set(catalog.ids()) == set(CONTRACT_IDS)
    assert len(CONTRACT_IDS) == 10


# ---------------------------------------------------------------------------
# AC2: mỗi contract đủ 7 trường + schema_ref import được thật
# ---------------------------------------------------------------------------

def test_every_contract_has_7_fields():
    for c in CONTRACTS:
        assert c.name
        assert c.version
        assert c.schema_ref and len(c.schema_ref) == 2
        assert c.compatibility
        assert c.lifecycle in ContractLifecycle
        # deprecation + migration: field tồn tại (None OK cho STABLE/FROZEN)
        assert hasattr(c, "deprecated_in")
        assert hasattr(c, "deprecated_reason")
        assert hasattr(c, "migration_path")
        assert hasattr(c, "notes")


def test_schema_refs_importable():
    """C1-01: schema_ref phải import được thật — không tên ảo."""
    catalog = ContractCatalog()
    broken = catalog.verify_schema_refs()
    assert broken == [], f"schema_ref không import được: {broken}"


def test_definition_extra_forbid():
    with pytest.raises(Exception):
        ContractDefinition(
            id="agent", name="x", version="1.0.0",
            schema_ref=("a", "b"), unknown_field=1,
        )


def test_id_must_be_lowercase():
    with pytest.raises(Exception):
        ContractDefinition(
            id="Agent", name="x", version="1.0.0", schema_ref=("a", "b"),
        )


# ---------------------------------------------------------------------------
# AC3: semantic versioning — patch/minor compatible, major breaking
# ---------------------------------------------------------------------------

def test_semver_compat_via_compatibility_checker():
    from aios_core.contracts.compatibility import CompatibilityChecker
    # minor bump (1.0.0 → 1.1.0): backward compatible
    assert CompatibilityChecker.is_compatible("1.1.0", "1.0.0")
    # patch bump: compatible
    assert CompatibilityChecker.is_compatible("1.0.1", "1.0.0")
    # major bump (1.x → 2.x): breaking
    assert not CompatibilityChecker.is_compatible("2.0.0", "1.0.0")
    # 0.x minor bump = breaking
    assert not CompatibilityChecker.is_compatible("0.2.0", "0.1.0")


def test_catalog_versions_are_semver():
    for c in CONTRACTS:
        assert c.version.count(".") == 2, f"{c.id}: version không semver: {c.version}"


# ---------------------------------------------------------------------------
# AC4: lifecycle validation — DEPRECATED bắt buộc đủ thông tin
# ---------------------------------------------------------------------------

def test_plugin_is_deprecated_with_migration():
    catalog = ContractCatalog()
    plugin = catalog.get("plugin")
    assert plugin.lifecycle == ContractLifecycle.DEPRECATED
    assert plugin.deprecated_in == "1.0.0"
    assert plugin.deprecated_reason
    assert plugin.migration_path


def test_deprecated_requires_migration_path():
    with pytest.raises(Exception):
        ContractDefinition(
            id="x", name="X", version="1.0.0", schema_ref=("a", "b"),
            lifecycle=ContractLifecycle.DEPRECATED,
            deprecated_in="1.0.0",  # thiếu deprecated_reason + migration_path
        )


def test_runtime_artifact_frozen():
    catalog = ContractCatalog()
    assert catalog.get("runtime").lifecycle == ContractLifecycle.FROZEN
    assert catalog.get("artifact").lifecycle == ContractLifecycle.FROZEN


# ---------------------------------------------------------------------------
# AC5: matrix — ✓/⚠/✗ + breaking/warning count
# ---------------------------------------------------------------------------

def test_matrix_default_all_ok_except_plugin_warning():
    checker = ContractChecker()
    report = checker.check_all()
    assert report.breaking_count == 0
    assert report.warning_count == 1  # plugin DEPRECATED
    by_id = {r.contract_id: r for r in report.results}
    assert by_id["plugin"].status == CheckStatus.WARNING
    assert by_id["runtime"].status == CheckStatus.OK
    assert not report.blocking


def test_matrix_removed_is_breaking():
    catalog = ContractCatalog(
        contracts=(
            ContractDefinition(
                id="tool", name="Tool", version="2.0.0",
                schema_ref=("aios_core.tools.base", "Tool"),
                lifecycle=ContractLifecycle.REMOVED,
            ),
        )
    )
    checker = ContractChecker(catalog)
    report = checker.check_all()
    assert report.breaking_count == 1
    assert report.blocking
    assert report.results[0].status == CheckStatus.BREAKING


def test_matrix_broken_schema_ref_is_breaking():
    catalog = ContractCatalog(
        contracts=(
            ContractDefinition(
                id="tool", name="Tool", version="1.0.0",
                schema_ref=("aios_core.nonexistent", "Nope"),
            ),
        )
    )
    checker = ContractChecker(catalog)
    report = checker.check_all()
    assert report.breaking_count == 1
    assert report.blocking


# ---------------------------------------------------------------------------
# AC6: deprecated API detector
# ---------------------------------------------------------------------------

def test_deprecated_usage_detected():
    checker = ContractChecker()
    warnings = checker.check_deprecated_usage(["plugin", "runtime"])
    assert len(warnings) == 1
    assert warnings[0].contract_id == "plugin"
    assert "TASK-074" in warnings[0].migration_path


def test_deprecated_usage_clean():
    checker = ContractChecker()
    assert checker.check_deprecated_usage(["runtime", "model", "tool"]) == []


def test_deprecated_usage_unknown_id_ignored():
    checker = ContractChecker()
    assert checker.check_deprecated_usage(["does_not_exist"]) == []


# ---------------------------------------------------------------------------
# AC7/AC8: CLI chạy thật
# ---------------------------------------------------------------------------

def test_cli_contract_check(tmp_path):
    from aios_core.workflow.cli import main

    assert main(["contract", "check"]) == 0


def test_cli_contract_list(tmp_path, capsys):
    from aios_core.workflow.cli import main

    assert main(["contract", "list"]) == 0
    out = capsys.readouterr().out
    assert "plugin" in out and "1.1.0" in out and "deprecated" in out
    assert "runtime" in out


def test_cli_contract_check_full_has_warnings(capsys):
    """check-full: scan deprecated usage → 1 warning plugin, vẫn exit 0."""
    from aios_core.workflow.cli import main

    assert main(["contract", "check-full"]) == 0
    out = capsys.readouterr().out
    assert "Breaking changes: 0" in out
    assert "Warnings: 2" in out  # 1 matrix (plugin) + 1 usage scan


def test_format_matrix_stable():
    checker = ContractChecker()
    report = checker.check_all()
    text = format_matrix(report, checker.catalog)
    assert "Breaking changes: 0" in text
    assert "✓" in text and "⚠" in text
