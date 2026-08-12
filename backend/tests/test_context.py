"""Context service tests — fake clock, TTL, scopes."""

import pytest

from aios_core.kernel.services import Context, ContextScope, ContextService


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_set_get_delete():
    svc = ContextService(clock=FakeClock())
    svc.set(ContextScope.WORKFLOW, "request", {"x": 1})
    assert svc.get(ContextScope.WORKFLOW, "request") == {"x": 1}
    svc.delete(ContextScope.WORKFLOW, "request")
    assert svc.get(ContextScope.WORKFLOW, "request") is None


def test_delete_idempotent():
    svc = ContextService(clock=FakeClock())
    svc.delete(ContextScope.AGENT, "missing")
    svc.delete(ContextScope.AGENT, "missing")  # no error


def test_ttl_expiry_lazy():
    clock = FakeClock()
    svc = ContextService(clock=clock)
    svc.set(ContextScope.USER, "session", "abc", ttl_s=10)
    assert svc.get(ContextScope.USER, "session") == "abc"
    clock.advance(11)
    assert svc.get(ContextScope.USER, "session") is None


def test_ttl_none_never_expires():
    clock = FakeClock()
    svc = ContextService(clock=clock)
    svc.set(ContextScope.SHARED, "forever", "v")
    clock.advance(10**6)
    assert svc.get(ContextScope.SHARED, "forever") == "v"


def test_empty_key_raises():
    svc = ContextService(clock=FakeClock())
    with pytest.raises(ValueError, match="key"):
        svc.set(ContextScope.SYSTEM, "", "v")


def test_get_all_dict_and_expiry():
    clock = FakeClock()
    svc = ContextService(clock=clock)
    svc.set(ContextScope.WORKFLOW, "a", 1)
    svc.set(ContextScope.WORKFLOW, "b", 2, ttl_s=5)
    clock.advance(6)
    assert svc.get_all(ContextScope.WORKFLOW, inherit=False) == {"a": 1}
    assert svc.get_all(ContextScope.AGENT, inherit=False) == {}


def test_scope_isolation():
    svc = ContextService(clock=FakeClock())
    svc.set(ContextScope.USER, "k", "user-value")
    # inherit=False → isolated; inherit=True → falls back to USER
    assert svc.get(ContextScope.AGENT, "k", inherit=False) is None
    assert svc.get(ContextScope.AGENT, "k", inherit=True) == "user-value"


def test_context_frozen():
    ctx = Context(scope=ContextScope.SYSTEM, key="k", value=1)
    with pytest.raises(Exception):
        ctx.key = "other"  # frozen dataclass rejects mutation


def test_is_expired_with_clock():
    clock = FakeClock()
    ctx = Context(scope=ContextScope.SYSTEM, key="k", value=1, ttl_s=5, _created_mono=clock())
    assert ctx.is_expired(clock) is False
    clock.advance(5)
    assert ctx.is_expired(clock) is True


def test_inheritance_fallback_to_parent():
    # F-004: a key set in an ancestor scope is visible from a descendant scope.
    svc = ContextService(clock=FakeClock())
    svc.set(ContextScope.WORKFLOW, "tenant", "acme")
    # EXECUTION is a descendant of WORKFLOW (EXECUTION->AGENT->WORKFLOW).
    assert svc.get(ContextScope.EXECUTION, "tenant", inherit=True) == "acme"
    assert svc.get_context(ContextScope.EXECUTION, "tenant", inherit=True) is not None
    # get_all merges ancestor scopes (most-specific wins).
    svc.set(ContextScope.EXECUTION, "local", "x")
    all_exec = svc.get_all(ContextScope.EXECUTION, inherit=True)
    assert all_exec["tenant"] == "acme"
    assert all_exec["local"] == "x"


def test_inheritance_disabled_is_isolated():
    # inherit=False must NOT fall back to parent scope.
    svc = ContextService(clock=FakeClock())
    svc.set(ContextScope.WORKFLOW, "tenant", "acme")
    assert svc.get(ContextScope.EXECUTION, "tenant", inherit=False) is None


def test_shared_scope_has_no_parent():
    # SHARED is a root scope; nothing inherits from it.
    svc = ContextService(clock=FakeClock())
    svc.set(ContextScope.SYSTEM, "global", "g")
    assert svc.get(ContextScope.SHARED, "global", inherit=True) is None
    svc.set(ContextScope.SHARED, "team", "t")
    assert svc.get(ContextScope.EXECUTION, "team", inherit=True) is None
