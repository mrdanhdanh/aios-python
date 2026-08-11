"""Scheduler service tests."""

import threading
import time

import pytest

from aios_core.kernel.services import SchedulerService


@pytest.fixture
def svc():
    s = SchedulerService(poll_interval_s=0.02)
    yield s
    s.stop()


def test_one_shot_runs_after_delay(svc):
    done = threading.Event()
    svc.start()
    svc.schedule_one_shot("j1", 0.05, done.set)
    assert done.wait(1.0) is True


def test_interval_runs_multiple_times(svc):
    count = []
    svc.start()
    svc.schedule_interval("j2", 0.03, lambda: count.append(1))
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        if len(count) >= 3:
            break
        time.sleep(0.02)
    svc.cancel("j2")
    assert len(count) >= 3


def test_interval_skips_overlap(svc):
    overlap_entered = threading.Event()
    release = threading.Event()
    calls = []

    def slow():
        calls.append(1)
        overlap_entered.set()
        release.wait(1.0)

    svc.start()
    svc.schedule_interval("j3", 0.02, slow)
    assert overlap_entered.wait(1.0)
    time.sleep(0.1)  # several ticks while callback still running
    assert len(calls) == 1  # no overlap
    svc.cancel("j3")  # cancel first, then release (no new ticks)
    release.set()
    time.sleep(0.1)
    assert len(calls) == 1  # cancelled → no more calls


def test_interval_error_continues(svc):
    calls = []
    state = {"fail": True}

    def flaky():
        if state["fail"]:
            state["fail"] = False
            raise RuntimeError("boom")
        calls.append(1)

    svc.start()
    svc.schedule_interval("j4", 0.03, flaky)
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        if len(calls) >= 1:
            break
        time.sleep(0.02)
    svc.cancel("j4")
    assert len(calls) >= 1  # kept ticking after error


def test_cancel_unknown_noop(svc):
    svc.cancel("missing")  # no error


def test_start_idempotent(svc):
    svc.start()
    svc.start()
    svc.stop()
    svc.stop()  # idempotent


def test_duplicate_name_replaces(svc):
    calls = []
    svc.start()
    svc.schedule_one_shot("j5", 0.05, lambda: calls.append(1))
    svc.schedule_one_shot("j5", 0.05, lambda: calls.append(2))
    time.sleep(0.2)
    assert calls == [2]  # old job replaced


def test_list_jobs(svc):
    svc.start()
    svc.schedule_one_shot("a", 1.0, lambda: None)
    svc.schedule_interval("b", 1.0, lambda: None)
    jobs = svc.list_jobs()
    assert ("a", "one_shot", False) in jobs
    assert ("b", "interval", False) in jobs


def test_hooks_via_container_start():
    """on_startup/on_shutdown lifecycle hooks."""
    svc = SchedulerService(poll_interval_s=0.02)
    svc.on_startup()
    done = threading.Event()
    svc.schedule_one_shot("h", 0.05, done.set)
    assert done.wait(1.0)
    svc.on_shutdown()
