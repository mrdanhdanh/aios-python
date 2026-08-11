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
    assert svc.get_all(ContextScope.WORKFLOW) == {"a": 1}
    assert svc.get_all(ContextScope.AGENT) == {}


def test_scope_isolation():
    svc = ContextService(clock=FakeClock())
    svc.set(ContextScope.USER, "k", "user-value")
    assert svc.get(ContextScope.AGENT, "k") is None


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
