"""Resource service tests."""

from aios_core.config import ResourcesSettings
from aios_core.kernel.services import ResourceService


def test_unlimited_defaults():
    svc = ResourceService()
    assert svc.acquire_tokens(100) is True
    assert svc.acquire_slot() is True
    assert svc.stats()["used_tokens"] == 100
    assert svc.stats()["running"] == 1


def test_token_budget():
    svc = ResourceService(ResourcesSettings(max_tokens=100))
    assert svc.acquire_tokens(60) is True
    assert svc.acquire_tokens(60) is False  # would exceed
    assert svc.stats()["used_tokens"] == 60
    svc.release_tokens(60)
    assert svc.stats()["used_tokens"] == 0


def test_release_clamps_non_negative():
    svc = ResourceService(ResourcesSettings(max_tokens=10))
    svc.acquire_tokens(5)
    svc.release_tokens(50)
    assert svc.stats()["used_tokens"] == 0
    svc.release_slot()
    assert svc.stats()["running"] == 0


def test_concurrent_limit():
    svc = ResourceService(ResourcesSettings(max_concurrent=2))
    assert svc.acquire_slot() is True
    assert svc.acquire_slot() is True
    assert svc.acquire_slot() is False
    svc.release_slot()
    assert svc.acquire_slot() is True


def test_stats_snapshot():
    svc = ResourceService(ResourcesSettings(max_tokens=50, max_concurrent=1))
    svc.acquire_tokens(10)
    svc.acquire_slot()
    stats = svc.stats()
    assert stats == {
        "used_tokens": 10,
        "running": 1,
        "max_tokens": 50,
        "max_concurrent": 1,
    }


def test_negative_tokens_rejected():
    svc = ResourceService()
    assert svc.acquire_tokens(-5) is False


def test_acquire_slot_wait_blocks_until_release():
    # F-003: blocking acquire_slot_wait queues when full, FIFO wake on release.
    import threading
    import time

    svc = ResourceService(ResourcesSettings(max_concurrent=1))
    assert svc.acquire_slot_wait() is True  # first grants immediately
    assert svc.pending() == 0

    started = threading.Event()
    granted = threading.Event()

    def worker():
        started.wait(1.0)
        ok = svc.acquire_slot_wait(timeout=2.0)  # should block until release
        if ok:
            granted.set()

    t = threading.Thread(target=worker)
    t.start()
    started.set()
    # Poll until the worker has actually enqueued itself (blocked on the slot).
    for _ in range(200):
        if svc.pending() == 1:
            break
        time.sleep(0.005)
    # While blocked, pending should be 1 and running must not exceed limit.
    assert svc.pending() == 1
    assert svc.stats()["running"] == 1
    svc.release_slot()  # wake the waiter
    assert granted.wait(2.0)
    assert svc.stats()["running"] == 1
    t.join(2.0)
    svc.release_slot()


def test_acquire_slot_wait_timeout():
    svc = ResourceService(ResourcesSettings(max_concurrent=1))
    assert svc.acquire_slot_wait() is True
    assert svc.acquire_slot_wait(timeout=0.1) is False  # times out, no slot
    assert svc.pending() == 0  # timeout removed itself from queue
    svc.release_slot()


def test_nonblocking_acquire_slot_backward_compat():
    # F-003/R2: original non-blocking API still returns False when full.
    svc = ResourceService(ResourcesSettings(max_concurrent=1))
    assert svc.acquire_slot() is True
    assert svc.acquire_slot() is False
    svc.release_slot()
