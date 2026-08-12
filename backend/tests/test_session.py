"""Session memory tests (wrapper over ContextService with fake clock)."""

from aios_core.kernel.services import ContextService
from aios_core.memory import SessionMemory


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def make_session(tmp_path=None, session_id="s1"):
    clock = FakeClock()
    ctx = ContextService(clock=clock)
    return SessionMemory(ctx, session_id), clock


def test_set_get_delete():
    mem, _ = make_session()
    mem.set("key", {"v": 1})
    assert mem.get("key") == {"v": 1}
    mem.delete("key")
    assert mem.get("key") is None


def test_session_isolation():
    mem1, _ = make_session(session_id="a")
    mem2, _ = make_session(session_id="b")
    mem1.set("k", "va")
    assert mem2.get("k") is None


def test_clear_session():
    mem, _ = make_session()
    mem.set("a", 1)
    mem.set("b", 2)
    mem.clear_session()
    assert mem.get("a") is None
    assert mem.get("b") is None


def test_ttl_expiry():
    mem, clock = make_session()
    mem.set("temp", "v", ttl_s=10)
    assert mem.get("temp") == "v"
    clock.advance(11)
    assert mem.get("temp") is None


def test_ttl_none_never_expires():
    mem, clock = make_session()
    mem.set("forever", "v")
    clock.advance(10**6)
    assert mem.get("forever") == "v"
