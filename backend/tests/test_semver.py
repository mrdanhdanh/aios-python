"""Semver helper tests: parse, compare, precedence."""

import pytest

from aios_core.semver import compare, parse_version


def test_parse_version_fields():
    v = parse_version("1.2.3-beta.1+build.5")
    assert (v.major, v.minor, v.patch) == (1, 2, 3)
    assert v.prerelease == ("beta", "1")
    assert v.build == "build.5"


def test_parse_invalid():
    for bad in ("1.0", "nope", "1.0.0-", "1.0.0+"):
        with pytest.raises(ValueError):
            parse_version(bad)


def test_compare_core():
    assert compare("1.0.0", "1.0.0") == 0
    assert compare("0.1.0", "0.2.0") == -1
    assert compare("2.0.0", "1.9.9") == 1


def test_compare_prerelease_precedence():
    # release > pre-release
    assert compare("1.0.0", "1.0.0-beta.1") == 1
    assert compare("1.0.0-beta.1", "1.0.0") == -1
    # numeric identifiers sort numerically: alpha.10 > alpha.2
    assert compare("1.0.0-alpha.10", "1.0.0-alpha.2") == 1
    assert compare("1.0.0-alpha.2", "1.0.0-alpha.10") == -1
    # alpha < beta
    assert compare("1.0.0-alpha", "1.0.0-beta") == -1
