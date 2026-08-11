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
