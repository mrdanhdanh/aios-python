"""Sandbox pool tests (AC15-AC18) + source tests (AC14)."""

import threading

import pytest

from aios_core.sandbox import SandboxPool, SandboxPoolError
from aios_core.skills import GitSource, PipSource, ZipSource
from aios_core.skills import SkillSource
from aios_core.skills.errors import SkillError


# -- SandboxPool ----------------------------------------------------------------

def test_acquire_release_warm_reuse():
    pool = SandboxPool(max_size=2)
    sb1 = pool.acquire("python")
    assert sb1.warm is False
    pool.release(sb1.id)
    sb2 = pool.acquire("python")
    assert sb2.id == sb1.id and sb2.warm is True  # reused (C1-10 monotonic)
    pool.release(sb2.id)


def test_acquire_normalizes_language():
    pool = SandboxPool(max_size=2)
    pool.acquire("python")
    pool.release(pool._sandboxes[0].id)
    sb = pool.acquire("Python")  # C1-11: different case reuses
    assert sb.language == "python" and sb.warm is True


def test_acquire_different_language_new():
    pool = SandboxPool(max_size=4)
    a = pool.acquire("python")
    b = pool.acquire("node")
    assert a.id != b.id


def test_acquire_empty_language_raises():
    pool = SandboxPool()
    with pytest.raises(SandboxPoolError, match="language"):
        pool.acquire("   ")


def test_pool_full_raises():
    pool = SandboxPool(max_size=1, idle_timeout_s=0)
    pool.acquire("python")
    with pytest.raises(SandboxPoolError, match="full"):
        pool.acquire("node")


def test_evict_idle_expired():
    import time as _time

    pool = SandboxPool(max_size=4, idle_timeout_s=10)
    a = pool.acquire("python")
    pool.release(a.id)
    now = _time.monotonic()
    assert pool.evict_idle(now=now + 11) == 1
    assert pool.health()["total"] == 0


def test_evict_idle_not_expired_kept():
    pool = SandboxPool(max_size=4, idle_timeout_s=10)
    a = pool.acquire("python")
    pool.release(a.id)
    assert pool.evict_idle(now=a.last_used_at + 5) == 0
    assert pool.health()["total"] == 1


def test_evict_then_acquire_ok():
    import time as _time

    pool = SandboxPool(max_size=1, idle_timeout_s=10)
    a = pool.acquire("python")
    pool.release(a.id)
    pool.evict_idle(now=_time.monotonic() + 11)  # expired
    b = pool.acquire("python")
    assert b.id != a.id  # new cold sandbox


def test_execute_no_exec():
    pool = SandboxPool(max_size=2)
    sb = pool.acquire("python")
    out = pool.execute(sb.id, "import os; os.remove('x')")
    assert out.ok is True and out.result["executed"] is False


def test_release_not_busy_raises():
    pool = SandboxPool(max_size=2)
    sb = pool.acquire("python")
    pool.release(sb.id)
    with pytest.raises(SandboxPoolError, match="not busy"):
        pool.release(sb.id)


def test_health_report():
    pool = SandboxPool(max_size=4)
    pool.acquire("python")
    h = pool.health()
    assert h["total"] == 1 and h["busy"] == 1 and h["max_size"] == 4


def test_concurrent_acquire_release():
    pool = SandboxPool(max_size=4)
    errors = []

    def worker(i):
        try:
            sb = pool.acquire("python")
            pool.execute(sb.id, "x = 1")
            pool.release(sb.id)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert pool.health()["total"] <= 4


def test_pool_deterministic_repeat():
    pool = SandboxPool(max_size=2)
    sb = pool.acquire("python")
    r1 = pool.execute(sb.id, "x")
    r2 = pool.execute(sb.id, "x")
    assert r1.result == r2.result


def test_pool_invalid_config():
    with pytest.raises(ValueError, match="max_size"):
        SandboxPool(max_size=0)
    with pytest.raises(ValueError, match="idle"):
        SandboxPool(idle_timeout_s=-1)


# -- Skill sources (AC14) ---------------------------------------------------------

def test_zip_source_ok():
    src = ZipSource()
    manifest = src.load("demo-pack")
    assert manifest["id"] == "skill.demo_zip" and manifest["version"] == "1.0.0"


def test_git_source_ok():
    src = GitSource()
    manifest = src.load("https://github.com/aios/demo-skill")
    assert manifest["source"] == "git"
    assert manifest["dependencies"] == ["skill.demo_zip@>=1.0.0"]


def test_pip_source_ok():
    src = PipSource()
    assert src.load("aios-demo-skill")["id"] == "skill.demo_pip"


def test_source_empty_ref_valueerror():
    for src in (ZipSource(), GitSource(), PipSource()):
        with pytest.raises(ValueError, match="ref"):
            src.load("  ")


def test_source_unknown_ref_skillerror():
    for src in (ZipSource(), GitSource(), PipSource()):
        with pytest.raises(SkillError, match="unknown"):
            src.load("nope")


def test_no_syscall_all_sources(monkeypatch):
    import socket
    import subprocess

    def _forbid(*a, **k):
        raise AssertionError("syscall detected")

    monkeypatch.setattr(socket, "socket", _forbid)
    monkeypatch.setattr(subprocess, "run", _forbid)
    monkeypatch.setattr(subprocess, "Popen", _forbid)
    for src in (ZipSource(), GitSource(), PipSource()):
        for ref in ("demo-pack", "https://github.com/aios/demo-skill", "aios-demo-skill"):
            try:
                manifest = src.load(ref)
                assert manifest["id"]
            except SkillError:
                pass  # ref not in this source — fine
