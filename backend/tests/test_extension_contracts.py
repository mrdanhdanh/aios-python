"""TASK-045 — Extension Contracts (M8-E3) tests."""

import pytest

from aios_core.extension import (
    ApiNamespace,
    CompatibilityViolation,
    ContractRequirement,
    ExtensionContract,
    ExtensionError,
    assert_namespace_allowed,
    check_requires,
    parse_constraint,
)


def test_namespace_enum_four_values():
    assert {ns.value for ns in ApiNamespace} == {"internal", "public", "extension", "experimental"}


def test_contract_model_extra_forbidden():
    with pytest.raises(Exception):
        ExtensionContract(id="x", namespace=ApiNamespace.PUBLIC, version="1.0", unknown=1)
    req = ContractRequirement(contract="capability_contract", constraint="^2.0")
    assert req.contract == "capability_contract"


def test_parse_constraint_forms():
    assert parse_constraint("*")[0] == "*"
    assert parse_constraint("^2.0")[0] == "^"
    assert parse_constraint(">=1.8")[0] == ">="
    assert parse_constraint("1.8.0")[0] == "="
    assert parse_constraint("~1.9")[0] == "~"
    with pytest.raises(ExtensionError):
        parse_constraint("bogus")


def test_check_requires_caret_major_pinned():
    result = check_requires(
        [{"contract": "capability_contract", "constraint": "^2.0"}],
        {"capability_contract": "2.5.0"},
    )
    assert result.ok
    bad = check_requires(
        [{"contract": "capability_contract", "constraint": "^2.0"}],
        {"capability_contract": "3.0.0"},
    )
    assert not bad.ok
    assert any("capability_contract" in err for err in bad.errors)


def test_check_requires_missing_contract_fail_closed():
    result = check_requires(
        [{"contract": "unknown_contract", "constraint": ">=1.0"}],
        {"capability_contract": "2.0.0"},
    )
    assert not result.ok
    assert any("missing runtime contract" in err for err in result.errors)


def test_check_requires_ge_and_exact():
    ok_ge = check_requires([{"contract": "a", "constraint": ">=1.8"}], {"a": "1.9.0"})
    assert ok_ge.ok
    bad_exact = check_requires([{"contract": "a", "constraint": "1.8.0"}], {"a": "1.9.0"})
    assert not bad_exact.ok
    ok_any = check_requires([{"contract": "a", "constraint": "*"}], {"a": "0.1.0"})
    assert ok_any.ok


def test_tilde_constraint_warns_but_passes():
    result = check_requires([{"contract": "a", "constraint": "~1.9"}], {"a": "1.9.5"})
    assert result.ok
    assert any("deprecated" in w for w in result.warnings)


def test_namespace_allow_list_gate():
    assert_namespace_allowed(ApiNamespace.EXTENSION, ["extension", "public"])
    with pytest.raises(CompatibilityViolation):
        assert_namespace_allowed(ApiNamespace.INTERNAL, ["extension"])
