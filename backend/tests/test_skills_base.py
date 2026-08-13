"""Skills base contract tests (AC2, AC3, AC13)."""

import pytest

from aios_core.kernel import EventType
from aios_core.skills import (
    SkillManifest,
    SkillSource,
    SkillState,
    assert_transition,
)
from aios_core.skills.errors import SkillStateError


def _manifest(**over):
    data = {
        "id": "s1", "name": "S1", "version": "1.0.0", "source": "zip",
        "description": "d", "dependencies": [], "capabilities": ["c"],
        "permissions": ["filesystem"],
    }
    data.update(over)
    return SkillManifest.validate_manifest(**data)


def test_manifest_valid():
    m = _manifest()
    assert m.id == "s1" and m.version == "1.0.0" and m.source == SkillSource.ZIP


def test_manifest_invalid_version():
    for bad in ("1.0", "abc", "", "1.0.0.0"):
        with pytest.raises(ValueError, match="semver"):
            _manifest(version=bad)


def test_manifest_invalid_source():
    with pytest.raises(ValueError):
        _manifest(source="file")


def test_manifest_empty_id_name():
    with pytest.raises(ValueError, match="id"):
        _manifest(id="  ")
    with pytest.raises(ValueError, match="name"):
        _manifest(name="")


def test_manifest_extra_field_forbidden():
    with pytest.raises(Exception):
        _manifest(bogus=1)


def test_manifest_defaults():
    m = _manifest(description="", dependencies=[], capabilities=[], permissions=[])
    assert m.dependencies == [] and m.description == "" and m.permissions == []


def test_transition_table_parameterized():
    # Every valid transition from the table must return the documented target.
    cases = [
        (SkillState.RESOLVED, "validate", SkillState.VALIDATED),
        (SkillState.VALIDATED, "install", SkillState.INSTALLED),
        (SkillState.INSTALLED, "enable", SkillState.ENABLED),
        (SkillState.DISABLED, "enable", SkillState.ENABLED),
        (SkillState.UPGRADED, "enable", SkillState.ENABLED),
        (SkillState.ROLLED_BACK, "enable", SkillState.ENABLED),
        (SkillState.ENABLED, "disable", SkillState.DISABLED),
        (SkillState.RELOADED, "disable", SkillState.DISABLED),
        (SkillState.UPGRADED, "disable", SkillState.DISABLED),
        (SkillState.ROLLED_BACK, "disable", SkillState.DISABLED),
        (SkillState.ENABLED, "unload", SkillState.UNLOADED),
        (SkillState.RELOADED, "unload", SkillState.UNLOADED),
        (SkillState.UNLOADED, "reload", SkillState.RELOADED),
        (SkillState.INSTALLED, "upgrade", SkillState.UPGRADED),
        (SkillState.ENABLED, "upgrade", SkillState.UPGRADED),
        (SkillState.ROLLED_BACK, "upgrade", SkillState.UPGRADED),
        (SkillState.UPGRADED, "rollback", SkillState.ROLLED_BACK),
        (SkillState.ENABLED, "rollback", SkillState.ROLLED_BACK),
        (SkillState.RESOLVED, "remove", SkillState.REMOVED),
        (SkillState.REMOVED, "remove", None),  # terminal — raised
    ]
    for current, op, target in cases:
        if target is None:
            with pytest.raises(SkillStateError):
                assert_transition(current, op)
        else:
            assert assert_transition(current, op) == target


def test_invalid_transitions_raise():
    # C1-01: unloaded -> enable is FORBIDDEN (must reload).
    with pytest.raises(SkillStateError, match="invalid transition"):
        assert_transition(SkillState.UNLOADED, "enable")
    with pytest.raises(SkillStateError, match="invalid transition"):
        assert_transition(SkillState.VALIDATED, "enable")
    with pytest.raises(SkillStateError, match="invalid transition"):
        assert_transition(SkillState.INSTALLED, "rollback")  # C2-02 replacement case
    with pytest.raises(SkillStateError, match="terminal"):
        assert_transition(SkillState.REMOVED, "enable")


def test_event_strings_match_eventtype():
    from aios_core.skills import manager as m

    assert m._EVENT_INSTALLED == EventType.SKILL_INSTALLED.value
    assert m._EVENT_UPDATED == EventType.SKILL_UPDATED.value
    assert m._EVENT_REMOVED == EventType.SKILL_REMOVED.value
