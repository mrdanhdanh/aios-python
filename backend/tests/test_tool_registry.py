"""ToolRegistry + binding + factory tests (AC11, AC12, AC13, AC14)."""

import threading

import pytest

from aios_core.capabilities import CapabilityRegistry
from aios_core.tools import (
    ToolContext,
    ToolInput,
    PythonTool,
    ToolRegistry,
    build_default_tools,
    build_tool_registry,
)

ALLOW = ToolContext(permission_gate=lambda scopes: True)


@pytest.fixture
def registry():
    reg = ToolRegistry()
    for tool in build_default_tools():
        reg.register(tool)
    return reg


def test_register_get_list(registry):
    assert len(registry.list()) == 6
    assert registry.get("tool.python").name == "python"
    names = [t.id for t in registry.list()]
    assert names == ["tool.python", "tool.docker", "tool.rest", "tool.mcp", "tool.shell", "tool.git"]


def test_register_duplicate_raises(registry):
    with pytest.raises(ValueError, match="already registered"):
        registry.register(PythonTool())


def test_register_invalid_raises(registry):
    with pytest.raises(TypeError, match="Tool"):
        registry.register(object())  # type: ignore[arg-type]


def test_get_unknown_none(registry):
    assert registry.get("nope") is None


def test_list_by_capability_and_alias(registry):
    assert [t.id for t in registry.list_by_capability("execute_code")] == ["tool.python"]
    assert [t.id for t in registry.tools_for_capability("run_shell")] == ["tool.shell"]
    assert registry.list_by_capability("nope") == []


def test_all_available_filters(registry):
    registry.register(_UnavailablePython())  # tool.python-unavailable — khác id
    ids = [t.id for t in registry.all_available()]
    assert "tool.python" in ids
    assert "tool.python-unavailable" not in ids
    assert all(t.available() for t in registry.all_available())


class _UnavailablePython(PythonTool):
    def __init__(self):
        super().__init__(available=False)
        self.id = "tool.python-unavailable"
        self.name = "python-unavailable"


def test_capabilities_map(registry):
    mapping = registry.capabilities()
    assert mapping["execute_code"] == ["tool.python"]
    assert mapping["run_shell"] == ["tool.shell"]
    assert len(mapping) == 6


def test_concurrent_register_list():
    # STATS #23: prefix riêng cho mỗi thread.
    reg = ToolRegistry()
    errors = []

    def _worker(prefix):
        try:
            for i in range(25):
                tool = PythonTool()
                tool.id = f"{prefix}-{i}"
                tool.name = f"{prefix}-{i}"
                reg.register(tool)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_worker, args=(f"worker-{c}",)) for c in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len(reg.list()) == 50


def test_tool_concurrent_runs_same_instance():
    # C2-04: cùng 1 instance chạy 2 thread → cùng kết quả (stateless contract).
    tool = PythonTool()
    results = []

    def _run():
        out = tool.run(ToolInput(tool_id="tool.python", arguments={"code": "x=1"}), ALLOW)
        results.append((out.ok, out.result["syntax_ok"], out.usage["mode"]))

    threads = [threading.Thread(target=_run) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert all(r == (True, True, "stub") for r in results)


# -- Capability binding (AC12) ---------------------------------------------------

def _cap_registry():
    cr = CapabilityRegistry()
    for cap, desc in (
        ("execute_code", "run python code"),
        ("manage_container", "docker containers"),
        ("call_api", "http calls"),
        ("mcp_call", "mcp servers"),
        ("run_shell", "shell commands"),
        ("git_ops", "git operations"),
    ):
        cr.register_capability(cap, desc)
    return cr


def test_bind_capabilities_with_real_registry(registry):
    cr = _cap_registry()
    n = registry.bind_capabilities(lambda cap, tid: cr.bind_tool(cap, tid))
    assert n == 6
    assert cr.tools_for("execute_code") == ["tool.python"]
    assert cr.tools_for("run_shell") == ["tool.shell"]
    assert cr.tools_for("git_ops") == ["tool.git"]


def test_bind_idempotent(registry):
    cr = _cap_registry()
    registry.bind_capabilities(lambda cap, tid: cr.bind_tool(cap, tid))
    n2 = registry.bind_capabilities(lambda cap, tid: cr.bind_tool(cap, tid))
    assert n2 == 6  # C1-11: total pairs processed, even on 2nd call
    assert cr.tools_for("execute_code") == ["tool.python"]  # no duplicates


def test_bind_unknown_capability_raises(registry):
    cr = CapabilityRegistry()  # empty — first bind raises immediately
    with pytest.raises(Exception):
        registry.bind_capabilities(lambda cap, tid: cr.bind_tool(cap, tid))


def test_capability_swap_tools(registry):
    cr = _cap_registry()
    registry.bind_capabilities(lambda cap, tid: cr.bind_tool(cap, tid))
    # Tool swap: register a second tool exposing execute_code, bind again.
    alt = PythonTool()
    alt.id = "tool.python-alt"
    alt.name = "python-alt"
    registry.register(alt)
    registry.bind_capabilities(lambda cap, tid: cr.bind_tool(cap, tid))
    assert cr.tools_for("execute_code") == ["tool.python", "tool.python-alt"]
    # Tool contract unchanged:
    assert PythonTool.capabilities == ("execute_code",)


# -- Factory + metadata (AC13) ----------------------------------------------------

def test_build_default_tools():
    tools = build_default_tools()
    assert [t.id for t in tools] == [
        "tool.python", "tool.docker", "tool.rest", "tool.mcp", "tool.shell", "tool.git",
    ]


def test_build_tool_registry():
    reg = build_tool_registry()
    assert len(reg.list()) == 6
    assert isinstance(reg.get("tool.python"), PythonTool)


def test_tool_metadata_valid():
    import re

    for tool in build_default_tools():
        assert re.match(r"^\d+\.\d+\.\d+$", tool.metadata.version)
        assert tool.metadata.license == "MIT"
        assert tool.available() is True


# -- Determinism (AC14) ------------------------------------------------------------

def test_tools_deterministic_repeat_run():
    cases = [
        (PythonTool(), {"code": "x=1"}),
        (build_default_tools()[1], {"action": "status"}),
        (build_default_tools()[2], {"method": "GET", "url": "https://e.com"}),
        (build_default_tools()[3], {"server": "filesystem", "method": "read_file"}),
        (build_default_tools()[4], {"command": "ls"}),
        (build_default_tools()[5], {"action": "status"}),
    ]
    for tool, args in cases:
        a = tool.run(ToolInput(tool_id=tool.id, arguments=args), ALLOW)
        b = tool.run(ToolInput(tool_id=tool.id, arguments=args), ALLOW)
        assert a.result == b.result and a.ok == b.ok and a.usage == b.usage
