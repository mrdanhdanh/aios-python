"""Contract tests: versioning, compatibility, artifact."""

import pytest
from pydantic import ValidationError

from aios_core.contracts import (
    ArtifactContract,
    ArtifactType,
    CompatibilityChecker,
    ContractCompatibility,
    ContractMetadata,
    ContractVersion,
)

SHA256_64 = "a" * 64


def test_contract_version_valid():
    cv = ContractVersion(contract_version="1.0.0", schema_version="1.0.0-beta.1+build.5")
    assert cv.compatibility == ContractCompatibility.MINOR_COMPATIBLE


def test_contract_version_invalid_semver():
    with pytest.raises(ValidationError):
        ContractVersion(contract_version="1.0", schema_version="1.0.0")


# -- CompatibilityChecker.is_compatible (8 cases AC2) -------------------------

CASES = [
    # (installed, required, expected)
    ("1.0.0", "2.0.0", False),  # need newer major
    ("1.0.0", "1.2.0", False),  # required newer than installed
    ("1.2.0", "1.0.0", True),  # backward-compatible
    ("1.0.0", "0.9.0", False),  # strict policy: major downgrade
    ("0.1.0", "0.2.0", False),  # 0.x minor bump
    ("1.0.0-beta.1", "1.0.0", False),  # pre-release state differs
    ("1.0.0-alpha.10", "1.0.0-alpha.2", True),  # numeric precedence
    ("0.1.5", "0.1.2", True),  # 0.x same minor
]


@pytest.mark.parametrize("installed,required,expected", CASES)
def test_is_compatible(installed, required, expected):
    assert CompatibilityChecker.is_compatible(installed, required) is expected


# -- check_upgrade (4 cases AC17) ---------------------------------------------

UPGRADES = [
    # (old, new, compatible, breaking)
    ("1.0.0", "2.0.0", False, True),
    ("1.0.0", "1.2.0", True, False),
    ("0.1.0", "0.2.0", False, True),
    ("1.0.0", "0.9.0", False, True),
]


@pytest.mark.parametrize("old,new,compatible,breaking", UPGRADES)
def test_check_upgrade(old, new, compatible, breaking):
    result = CompatibilityChecker.check_upgrade(old, new)
    assert result.compatible is compatible
    assert result.breaking is breaking
    assert result.reason
    # invariant: breaking implies not compatible
    if result.breaking:
        assert not result.compatible


def test_check_upgrade_minor_downgrade_note():
    # (1.2.0 -> 1.0.0): incompatible, not breaking (documented policy)
    result = CompatibilityChecker.check_upgrade("1.2.0", "1.0.0")
    assert result.compatible is False
    assert result.breaking is False


# -- ArtifactContract ---------------------------------------------------------

def _artifact(**overrides):
    data = dict(
        id="art-1",
        name="report",
        version="1.0.0",
        author="AIOS",
        license="MIT",
        contract_version="1.0.0",
        schema_version="1.0.0",
        type=ArtifactType.MARKDOWN,
        storage_path="artifacts/report.md",
        checksum=None,
    )
    data.update(overrides)
    return ArtifactContract(**data)


def test_artifact_valid():
    a = _artifact(checksum=SHA256_64)
    assert a.checksum == SHA256_64
    assert a.validate() is True


def test_artifact_checksum_none_valid():
    assert _artifact().checksum is None
    assert _artifact().validate() is True


def test_artifact_checksum_invalid():
    with pytest.raises(ValidationError):
        _artifact(checksum="abc")


def test_artifact_version_invalid():
    with pytest.raises(ValidationError):
        _artifact(version="1.0")


def test_artifact_storage_path_empty():
    with pytest.raises(ValidationError):
        _artifact(storage_path="")


def test_artifact_contract_version_invalid():
    with pytest.raises(ValidationError):
        _artifact(contract_version="nope")


def test_artifact_unicode_path():
    a = _artifact(storage_path="artifacts/Báo cáo 2026.md")
    assert a.validate() is True


def test_artifact_validate_false_on_bad_checksum():
    a = _artifact(checksum=SHA256_64)
    a.checksum = "not-a-checksum"
    assert a.validate() is False


# -- schema-evolution regression (F-002) --------------------------------------
# Tests pydantic contract semantics with two standalone models (NOT the AIOS
# framework's CompatibilityChecker — that is semver-only). Label: schema
# field-evolution direction checks.

from pydantic import BaseModel, ConfigDict  # noqa: E402


class SampleContractV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str


class SampleContractV2AddOptional(SampleContractV1):
    model_config = ConfigDict(extra="forbid")

    note: str | None = None  # added optional field


class SampleContractV2RemoveRequired(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str  # removed "version" (required in V1)


class SampleContractV2Rename(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str  # renamed from "id"
    version: str


class SampleContractV2Required(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    owner: str  # optional→required in V1 would mean V1 had it optional


def test_evolution_add_optional_is_compatible():
    v1_payload = {"id": "x", "version": "1.0.0"}
    assert SampleContractV2AddOptional.model_validate(v1_payload)  # compatible


def test_evolution_remove_required_is_breaking():
    v1_payload = {"id": "x", "version": "1.0.0"}
    with pytest.raises(ValidationError):
        SampleContractV2RemoveRequired.model_validate(v1_payload)  # extra "version" forbidden


def test_evolution_rename_is_breaking():
    v1_payload = {"id": "x", "version": "1.0.0"}
    with pytest.raises(ValidationError):
        SampleContractV2Rename.model_validate(v1_payload)  # "id" forbidden, "identifier" missing


def test_evolution_optional_to_required_is_breaking():
    # V1 had "owner" optional; V2 makes it required → V1 payload without owner breaks.
    v1_payload = {"id": "x", "version": "1.0.0"}
    with pytest.raises(ValidationError):
        SampleContractV2Required.model_validate(v1_payload)  # missing "owner"


def test_validate_returns_false_instead_of_raising():
    # Contract.validate() is the enforcement point; ArtifactContract implements it.
    a = _artifact()
    assert a.validate() is True
