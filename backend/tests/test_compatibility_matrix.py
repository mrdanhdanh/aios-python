"""M12-P0 (TASK-084): Compatibility Matrix + CLI compat + version bump checks."""

from __future__ import annotations

import json

import pytest

from aios_core import __version__
from aios_core.contracts.catalog import CONTRACTS
from aios_core.contracts.compatibility import CompatibilityChecker
from aios_core.upgrade.compatibility import (
    AIOS_VERSION,
    CompatibilityMatrix,
)


# -- version bump (AC1/AC2/AC3) ----------------------------------------------

def test_version_bumped_to_110():
    assert __version__ == "1.1.0"
    assert AIOS_VERSION == "1.1.0"


def test_contracts_catalog_bumped_to_110():
    assert len(CONTRACTS) == 10
    for contract in CONTRACTS:
        assert contract.version == "1.1.0", f"{contract.id} vẫn 1.0.0"
    # deprecated_in của plugin GIỮ 1.0.0 (review R3 — test check-full phụ thuộc).
    plugin = next(c for c in CONTRACTS if c.id == "plugin")
    assert plugin.deprecated_in == "1.0.0"


def test_check_upgrade_100_to_110_backward_compatible():
    result = CompatibilityChecker.check_upgrade("1.0.0", "1.1.0")
    assert result.compatible is True
    assert result.breaking is False


# -- matrix registry (AC5) ----------------------------------------------------

def test_matrix_default_entries_14():
    rows = CompatibilityMatrix().list()
    assert len(rows) >= 14
    kinds = {r["kind"] for r in rows}
    assert kinds == {"plugin", "contract", "workflow", "skill", "sdk"}
    contract_ids = {r["id"] for r in rows if r["kind"] == "contract"}
    assert contract_ids == {c.id for c in CONTRACTS}


def test_matrix_entry_validation():
    from pydantic import ValidationError

    from aios_core.upgrade.compatibility import CompatibilityEntry

    with pytest.raises(ValidationError):
        CompatibilityEntry(kind="contract", id="agent", version="not-semver")
    with pytest.raises(ValidationError):
        CompatibilityEntry(kind="nope", id="x", version="1.0.0")


# -- check() fail-closed (AC6/AC7 + review R4) --------------------------------

def test_check_compatible_ok():
    result = CompatibilityMatrix().check("plugin", "demo", "1.0.0")
    assert result.compatible is True
    assert result.errors == []


def test_check_aios_min_fail_closed():
    result = CompatibilityMatrix().check("contract", "agent", "1.0.0",
                                         aios_version="0.9.0")
    assert result.compatible is False
    assert any("outside" in e for e in result.errors)


def test_check_aios_max_fail_closed():
    result = CompatibilityMatrix().check("workflow", "demo_flow", "1.0.0",
                                         aios_version="2.0.0")
    assert result.compatible is False


def test_check_max_1_1_x_accepts_patch():
    result = CompatibilityMatrix().check("workflow", "demo_flow", "1.0.0",
                                         aios_version="1.1.5")
    assert result.compatible is True


def test_check_unknown_kind_fail_closed():
    result = CompatibilityMatrix().check("gadget", "x", "1.0.0")
    assert result.compatible is False
    assert any("unknown kind" in e for e in result.errors)


def test_check_unknown_id_fail_closed():
    result = CompatibilityMatrix().check("contract", "unknown", "1.0.0")
    assert result.compatible is False
    assert any("no matrix entry" in e for e in result.errors)


def test_check_invalid_component_version_fail_closed():
    # review R4: version rác → error (fail-closed).
    result = CompatibilityMatrix().check("plugin", "demo", "abc")
    assert result.compatible is False
    assert any("invalid" in e for e in result.errors)


def test_check_version_mismatch_warns_but_compatible():
    result = CompatibilityMatrix().check("plugin", "demo", "2.0.0")
    assert result.compatible is True
    assert any("differs" in w for w in result.warnings)


def test_check_min_fail_keeps_warnings():
    # review R1: case contract agent 1.0.0 --aios-version 0.9.0 →
    # errors (aios_min) + warnings (version ≠ entry.version) đi cùng nhau.
    result = CompatibilityMatrix().check("contract", "agent", "1.0.0",
                                         aios_version="0.9.0")
    assert result.compatible is False
    assert result.errors
    assert any("differs" in w for w in result.warnings)


# -- CLI (AC5/AC6/AC7/AC8/AC12) ----------------------------------------------

def _run_cli(argv, capsys):
    from aios_core.workflow.cli import main

    code = main(argv)
    out = capsys.readouterr().out
    return code, out


def test_cli_compat_list(capsys):
    code, out = _run_cli(["compat", "list"], capsys)
    assert code == 0
    assert "contract" in out and "demo_flow" in out
    assert "entries" in out


def test_cli_compat_check_ok(capsys):
    code, out = _run_cli(["compat", "check", "plugin", "demo", "1.0.0"], capsys)
    assert code == 0
    data = json.loads(out)
    assert data["compatible"] is True
    assert data["errors"] == []


def test_cli_compat_check_out_of_range_exit_1(capsys):
    code, out = _run_cli(
        ["compat", "check", "workflow", "demo_flow", "1.0.0",
         "--aios-version", "2.0.0"],
        capsys,
    )
    assert code == 1
    data = json.loads(out)
    assert data["compatible"] is False
    assert data["errors"]


def test_cli_compat_check_unknown_exit_1(capsys):
    code, out = _run_cli(["compat", "check", "contract", "unknown", "1.0.0"], capsys)
    assert code == 1
    data = json.loads(out)
    assert data["compatible"] is False


def test_cli_compat_check_override_accepts_patch(capsys):
    code, out = _run_cli(
        ["compat", "check", "workflow", "demo_flow", "1.0.0",
         "--aios-version", "1.1.5"],
        capsys,
    )
    assert code == 0
    data = json.loads(out)
    assert data["compatible"] is True
