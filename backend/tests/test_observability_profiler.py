"""Profiler tests (TASK-021)."""

import pytest

from aios_core.observability.profiler import Profiler


def test_profile_context_manager(tmp_path):
    clock = iter([10.0, 12.5])
    profiler = Profiler(clock=lambda: next(clock))
    with profiler.profile("wf", "run"):
        pass
    report = profiler.report()
    assert len(report) == 1
    assert report[0].name == "wf"
    assert report[0].section == "run"
    assert report[0].duration_ms == 2500.0


def test_start_stop_and_clear():
    clock = iter([1.0, 1.2])
    profiler = Profiler(clock=lambda: next(clock))
    profiler.start("a", "b")
    section = profiler.stop("a", "b")
    assert section.duration_ms == pytest.approx(200.0)
    assert len(profiler.report()) == 1
    profiler.clear()
    assert profiler.report() == []


def test_double_start_raises():
    profiler = Profiler(clock=lambda: 1.0)
    profiler.start("a", "b")
    with pytest.raises(ValueError):
        profiler.start("a", "b")


def test_stop_without_start_raises():
    profiler = Profiler()
    with pytest.raises(ValueError):
        profiler.stop("a", "b")


def test_multiple_sections_independent():
    clock = iter([0.0, 1.0, 0.0, 0.5])
    profiler = Profiler(clock=lambda: next(clock))
    with profiler.profile("n1", "s1"):
        pass
    with profiler.profile("n1", "s2"):
        pass
    assert len(profiler.report()) == 2
    assert profiler.report()[0].section == "s1"
    assert profiler.report()[1].section == "s2"
