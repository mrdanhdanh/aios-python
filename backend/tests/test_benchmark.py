"""Benchmark harness (F-009) — honest, non-flaky, skippable.

Run with `pytest -m "not benchmark"` in CI to skip. Markers defined in
pyproject.toml (`markers = ["benchmark: performance smoke tests"]`).
"""

import time

import pytest

from aios_core.catalog import SystemCatalog
from aios_core.orchestrator import AgentSelector
from aios_core.workflow import MockCompiler, WorkflowDefinition

pytestmark = pytest.mark.benchmark


def _p95(times: list[float]) -> float:
    ordered = sorted(times)
    idx = max(0, int(len(ordered) * 0.95) - 1)
    return ordered[idx]


def test_catalog_get_is_o1(tmp_path):
    catalog = SystemCatalog()
    n = 500
    for i in range(n):
        catalog.index_entry("workflow", f"wf-{i}", {"i": i})

    # Warm up + measure p95 of get().
    times = []
    for _ in range(200):
        start = time.perf_counter()
        catalog.get("workflow", "wf-250")
        times.append((time.perf_counter() - start) * 1000)
    assert _p95(times) < 5.0, f"p95 {_p95(times):.3f}ms >= 5ms"

    # Structural O(1): dict-backed store (no scan).
    assert isinstance(catalog._entries, dict)  # noqa: SLF001


def test_catalog_get_ratio_scales_sublinear():
    def median_ms(count: int) -> float:
        catalog = SystemCatalog()
        for i in range(count):
            catalog.index_entry("workflow", f"wf-{i}", {"i": i})
        samples = []
        for _ in range(100):
            start = time.perf_counter()
            catalog.get("workflow", f"wf-{count // 2}")
            samples.append((time.perf_counter() - start) * 1000)
        return sorted(samples)[len(samples) // 2]

    small, large = median_ms(1000), median_ms(10000)
    assert large / max(small, 1e-9) < 5.0, f"ratio {large / max(small, 1e-9):.2f}x >= 5x"


def test_workflow_compile_smoke():
    nodes = [{"id": f"n{i}", "type": "task", "name": f"N{i}"} for i in range(50)]
    definition = WorkflowDefinition(name="big", version="1.0.0", nodes=nodes)
    start = time.perf_counter()
    MockCompiler().compile(definition)
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 50.0, f"compile {elapsed:.1f}ms >= 50ms"


def test_capability_lookup_o1():
    selector = AgentSelector()
    n = 1000
    for i in range(n):
        selector._mapping[f"intent-{i}"] = f"agent-{i}"  # noqa: SLF001
    start = time.perf_counter()
    for i in range(1000):
        selector.select(f"intent-{i}")
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 50.0, f"1000 lookups {elapsed:.1f}ms (dict-backed, O(1))"
    assert isinstance(selector._mapping, dict)  # noqa: SLF001


def test_capability_registry_o1():
    # F-009: capability lookup (get) must be O(1) (dict-backed), not a scan.
    from aios_core.capabilities import CapabilityRegistry

    reg = CapabilityRegistry()
    reg.register_capability("search")
    for i in range(1000):
        reg.bind_tool("search", f"tool-{i}")

    def median_ms(count: int) -> float:
        reg2 = CapabilityRegistry()
        reg2.register_capability("search")
        for i in range(count):
            reg2.bind_tool("search", f"tool-{i}")
        samples = []
        for _ in range(100):
            start = time.perf_counter()
            reg2.get("search")
            samples.append((time.perf_counter() - start) * 1000)
        return sorted(samples)[len(samples) // 2]

    small, large = median_ms(1000), median_ms(10000)
    assert large / max(small, 1e-9) < 5.0, f"ratio {large / max(small, 1e-9):.2f}x >= 5x"
    # Faithfulness: get returns the capability; tools_for returns the bound tools.
    assert reg.get("search") is not None
    assert set(reg.tools_for("search")) == {f"tool-{i}" for i in range(1000)}
