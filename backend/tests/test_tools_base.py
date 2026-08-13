"""Tool base contract tests (AC1-part, AC2, AC9, AC10)."""

import pytest

from aios_core.kernel.services import PermissionScope
from aios_core.tools import (
    Tool,
    ToolContext,
    ToolInput,
    ToolOutput,
    PythonTool,
    DockerTool,
    RestTool,
    McpTool,
    ShellTool,
    GitTool,
)

ALL_TOOLS = [PythonTool(), DockerTool(), RestTool(), McpTool(), ShellTool(), GitTool()]

EXPECTED_SCOPES = {
    "tool.python": "filesystem",
    "tool.docker": "docker",
    "tool.rest": "network",
    "tool.mcp": "network",
    "tool.shell": "shell",
    "tool.git": "git",
}


def _valid_args(tool_id: str) -> dict:
    return {
        "tool.python": {"code": "x = 1"},
        "tool.docker": {"action": "status"},
        "tool.rest": {"method": "GET", "url": "https://example.com"},
        "tool.mcp": {"server": "filesystem", "method": "read_file"},
        "tool.shell": {"command": "ls"},
        "tool.git": {"action": "status"},
    }[tool_id]


def test_tool_contract_models():
    with pytest.raises(Exception):
        ToolInput(tool_id="x", arguments={}, extra="nope")  # extra=forbid
    out = ToolOutput(ok=True)
    assert out.duration_s == 0.0
    assert out.usage == {}


def test_tool_id_mismatch_error():
    tool = PythonTool()
    out = tool.run(ToolInput(tool_id="tool.docker"), ToolContext())
    assert out.ok is False
    assert "tool_id mismatch" in out.error
    assert "expected tool.python" in out.error


def test_run_process_raises_error_status():
    class _BoomTool(PythonTool):
        id = "tool.python"

        def _run(self, input, context):
            raise RuntimeError("kaboom")

    tool = _BoomTool()
    out = tool.run(ToolInput(tool_id="tool.python"), ToolContext(permission_gate=lambda s: True))
    assert out.ok is False
    assert "kaboom" in out.error
    assert out.duration_s == 0.0  # R1: error path -> 0.0


@pytest.mark.parametrize("tool", ALL_TOOLS, ids=lambda t: t.id)
def test_permission_gate_denied_all_tools(tool):
    out = tool.run(ToolInput(tool_id=tool.id, arguments=_valid_args(tool.id)),
                   ToolContext(permission_gate=lambda scopes: False))
    assert out.ok is False
    scope = EXPECTED_SCOPES[tool.id]
    assert f"permission denied: {scope}" in out.error


@pytest.mark.parametrize("tool", ALL_TOOLS, ids=lambda t: t.id)
def test_permission_gate_none_fail_closed(tool):
    out = tool.run(ToolInput(tool_id=tool.id, arguments=_valid_args(tool.id)), ToolContext())
    assert out.ok is False
    assert "(no gate)" in out.error


@pytest.mark.parametrize("tool", ALL_TOOLS, ids=lambda t: t.id)
def test_permission_gate_raises_fail_closed(tool):
    # R2: gate raise -> ok=False "(gate error)" + no events
    events = []

    def _sink(et, pl):
        events.append(et)

    def _boom(scopes):
        raise RuntimeError("gate down")

    out = tool.run(
        ToolInput(tool_id=tool.id, arguments=_valid_args(tool.id)),
        ToolContext(permission_gate=_boom, event_sink=_sink),
    )
    assert out.ok is False
    assert "(gate error)" in out.error
    assert events == []  # no started/finished emitted


def test_scope_strings_match_permission_scope():
    values = {s.value for s in PermissionScope}
    for scope in EXPECTED_SCOPES.values():
        assert scope in values, f"scope {scope!r} không khớp PermissionScope"


def test_tool_events_started_finished():
    events = []
    tool = PythonTool(event_sink=lambda et, pl: events.append((et, pl)))
    out = tool.run(
        ToolInput(tool_id="tool.python", arguments={"code": "x=1"}, session_id="s1"),
        ToolContext(permission_gate=lambda s: True),
    )
    assert out.ok is True
    assert [et for et, _ in events] == ["tool.started", "tool.finished"]
    started = events[0][1]
    finished = events[1][1]
    assert started["tool_id"] == "tool.python"
    assert started["capabilities"] == ["execute_code"]
    assert finished["ok"] is True
    assert finished["capabilities"] == ["execute_code"]  # C1-13 symmetric


def test_tool_events_on_error():
    class _BoomTool(PythonTool):
        def _run(self, input, context):
            raise RuntimeError("boom")

    events = []
    tool = _BoomTool(event_sink=lambda et, pl: events.append(pl))
    out = tool.run(
        ToolInput(tool_id="tool.python", arguments={"code": "x=1"}),
        ToolContext(permission_gate=lambda s: True),
    )
    assert out.ok is False
    assert events[-1]["ok"] is False  # finished emitted with ok=False (R4)


def test_event_sink_raises_best_effort():
    def _boom(et, pl):
        raise RuntimeError("sink down")

    tool = PythonTool(event_sink=_boom)
    out = tool.run(
        ToolInput(tool_id="tool.python", arguments={"code": "x=1"}),
        ToolContext(permission_gate=lambda s: True),
    )
    assert out.ok is True  # sink failure must not break output


def test_event_sink_none_ok():
    tool = PythonTool()
    out = tool.run(
        ToolInput(tool_id="tool.python", arguments={"code": "x=1"}),
        ToolContext(permission_gate=lambda s: True),
    )
    assert out.ok is True


def test_required_scopes_empty_raises():
    with pytest.raises(ValueError, match="required_scopes"):
        class _Bad(Tool):
            tool_type = "python"
            required_scopes = ()
            capabilities = ("execute_code",)

            def _describe(self):
                return "bad"

            def _run(self, input, context):
                return ToolOutput(ok=True)

        _Bad()
