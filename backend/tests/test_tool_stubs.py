"""6 tool stub tests (AC3-AC8) + no-exec invariants + global no-syscall (C2-03)."""

import pytest

from aios_core.tools import (
    ToolContext,
    ToolInput,
    DockerTool,
    GitTool,
    McpTool,
    PythonTool,
    RestTool,
    ShellTool,
)

ALLOW = ToolContext(permission_gate=lambda scopes: True)


# -- PythonTool (AC3) -----------------------------------------------------------

def test_python_tool_ok():
    out = PythonTool().run(ToolInput(tool_id="tool.python", arguments={"code": "x = 1"}), ALLOW)
    assert out.ok is True
    assert out.result["syntax_ok"] is True
    assert out.result["executed"] is False
    assert out.usage["mode"] == "stub"


def test_python_tool_syntax_error():
    out = PythonTool().run(ToolInput(tool_id="tool.python", arguments={"code": "def :"}), ALLOW)
    assert out.ok is False
    assert "python syntax error" in out.error


def test_python_tool_empty_code():
    out = PythonTool().run(ToolInput(tool_id="tool.python", arguments={"code": "   "}), ALLOW)
    assert out.ok is False
    assert "empty code" in out.error


def test_python_tool_invalid_argument():
    out = PythonTool().run(ToolInput(tool_id="tool.python", arguments={}), ALLOW)
    assert out.ok is False
    assert "invalid argument: code" in out.error


def test_python_tool_no_exec_side_effect(tmp_path):
    # C1-01 (assertion đúng chiều): marker VẪN tồn tại sau khi chạy code os.remove
    marker = tmp_path / "marker.txt"
    marker.write_text("x")
    code = f"import os; os.remove({str(marker)!r})"
    out = PythonTool().run(ToolInput(tool_id="tool.python", arguments={"code": code}), ALLOW)
    assert out.ok is True
    assert marker.exists() is True  # not executed — file not removed


def test_python_tool_execute_flag_no_exec():
    tool = PythonTool(execute=True)  # forward-compat only — still no exec
    out = tool.run(ToolInput(tool_id="tool.python", arguments={"code": "x = 1"}), ALLOW)
    assert out.ok is True
    assert out.result["executed"] is False


def test_python_tool_deterministic():
    tool = PythonTool()
    a = tool.run(ToolInput(tool_id="tool.python", arguments={"code": "x=1"}), ALLOW)
    b = tool.run(ToolInput(tool_id="tool.python", arguments={"code": "x=1"}), ALLOW)
    assert a.result == b.result and a.ok == b.ok and a.usage == b.usage


# -- DockerTool (AC4) -----------------------------------------------------------

def test_docker_tool_list_inspect_status():
    tool = DockerTool()
    out = tool.run(ToolInput(tool_id="tool.docker", arguments={"action": "list_images"}), ALLOW)
    assert out.ok is True and out.result["count"] == 3
    assert out.result["images"][0] == "python:3.12-slim"
    out = tool.run(ToolInput(tool_id="tool.docker", arguments={"action": "inspect"}), ALLOW)
    assert out.result["state"] == "mock running"
    out = tool.run(ToolInput(tool_id="tool.docker", arguments={"action": "status"}), ALLOW)
    assert out.result["daemon"] == "mock ok"


def test_docker_tool_unsupported_action():
    out = DockerTool().run(ToolInput(tool_id="tool.docker", arguments={"action": "rm -rf"}), ALLOW)
    assert out.ok is False and "unsupported action" in out.error


def test_docker_tool_invalid_argument():
    out = DockerTool().run(ToolInput(tool_id="tool.docker", arguments={}), ALLOW)
    assert out.ok is False and "invalid argument: action" in out.error


# -- RestTool (AC5) -------------------------------------------------------------

def test_rest_tool_ok():
    out = RestTool().run(
        ToolInput(tool_id="tool.rest", arguments={"method": "get", "url": "https://api.example.com/x"}),
        ALLOW,
    )
    assert out.ok is True
    assert out.result["status_code"] == 200
    assert out.result["body"]["echo"]["method"] == "GET"


def test_rest_tool_unsupported_method():
    out = RestTool().run(
        ToolInput(tool_id="tool.rest", arguments={"method": "TRACE", "url": "https://x.com"}),
        ALLOW,
    )
    assert out.ok is False and "unsupported method" in out.error


def test_rest_tool_invalid_url():
    for url in ("ftp://x.com", "not-a-url"):
        out = RestTool().run(
            ToolInput(tool_id="tool.rest", arguments={"method": "GET", "url": url}), ALLOW
        )
        assert out.ok is False and "invalid url" in out.error


def test_rest_tool_invalid_argument():
    out = RestTool().run(ToolInput(tool_id="tool.rest", arguments={}), ALLOW)
    assert out.ok is False and "invalid argument: method" in out.error


# -- McpTool (AC6) --------------------------------------------------------------

def test_mcp_tool_ok():
    out = McpTool().run(
        ToolInput(tool_id="tool.mcp", arguments={"server": "filesystem", "method": "read_file"}),
        ALLOW,
    )
    assert out.ok is True and out.result["server"] == "filesystem"


def test_mcp_tool_unknown_server():
    out = McpTool().run(
        ToolInput(tool_id="tool.mcp", arguments={"server": "nope", "method": "read_file"}), ALLOW
    )
    assert out.ok is False and "unknown mcp server" in out.error


def test_mcp_tool_unknown_method():
    out = McpTool().run(
        ToolInput(tool_id="tool.mcp", arguments={"server": "filesystem", "method": "nope"}), ALLOW
    )
    assert out.ok is False and "unknown method" in out.error


def test_mcp_tool_inject_servers():
    tool = McpTool(servers={"custom": ["do_thing"]})
    out = tool.run(
        ToolInput(tool_id="tool.mcp", arguments={"server": "custom", "method": "do_thing"}), ALLOW
    )
    assert out.ok is True


def test_mcp_tool_invalid_servers_raises():
    with pytest.raises(ValueError, match="server"):
        McpTool(servers={"ok": [123]})
    with pytest.raises(ValueError, match="server name"):
        McpTool(servers={"": ["a"]})


def test_mcp_tool_invalid_argument():
    out = McpTool().run(ToolInput(tool_id="tool.mcp", arguments={}), ALLOW)
    assert out.ok is False and "invalid argument: server" in out.error


# -- ShellTool (AC7) ------------------------------------------------------------

def test_shell_tool_ok():
    out = ShellTool().run(ToolInput(tool_id="tool.shell", arguments={"command": "ls -la"}), ALLOW)
    assert out.ok is True
    assert out.result["executed"] is False
    assert out.result["stdout"] == "stub: no execution"


def test_shell_tool_empty_command():
    out = ShellTool().run(ToolInput(tool_id="tool.shell", arguments={"command": " "}), ALLOW)
    assert out.ok is False and "empty command" in out.error


def test_shell_tool_no_exec_side_effect(tmp_path):
    marker = tmp_path / "created.txt"
    out = ShellTool().run(
        ToolInput(tool_id="tool.shell", arguments={"command": f"touch {marker}"}), ALLOW
    )
    assert out.ok is True
    assert not marker.exists()  # never executed


def test_shell_tool_invalid_argument():
    out = ShellTool().run(ToolInput(tool_id="tool.shell", arguments={}), ALLOW)
    assert out.ok is False and "invalid argument: command" in out.error


# -- GitTool (AC8) --------------------------------------------------------------

def test_git_tool_status_branch_log():
    tool = GitTool()
    assert tool.run(ToolInput(tool_id="tool.git", arguments={"action": "status"}), ALLOW).result["status"] == "clean"
    assert tool.run(ToolInput(tool_id="tool.git", arguments={"action": "branch"}), ALLOW).result["branch"] == "main"
    log = tool.run(ToolInput(tool_id="tool.git", arguments={"action": "log"}), ALLOW)
    assert log.result["commits"] == ["abc1234 init"]


def test_git_tool_unsupported_action():
    out = GitTool().run(ToolInput(tool_id="tool.git", arguments={"action": "push"}), ALLOW)
    assert out.ok is False and "unsupported action" in out.error


def test_git_tool_invalid_argument():
    out = GitTool().run(ToolInput(tool_id="tool.git", arguments={}), ALLOW)
    assert out.ok is False and "invalid argument: action" in out.error


# -- Global no-syscall (C2-03) ---------------------------------------------------

def test_no_syscall_all_tools(monkeypatch):
    """Monkeypatch socket/subprocess/os.system/urlopen → raise; 6 tools still ok."""
    import os
    import socket
    import subprocess

    def _forbid(*args, **kwargs):
        raise AssertionError("syscall/network detected")

    monkeypatch.setattr(socket, "socket", _forbid)
    monkeypatch.setattr(subprocess, "run", _forbid)
    monkeypatch.setattr(subprocess, "Popen", _forbid)
    monkeypatch.setattr(os, "system", _forbid)
    try:
        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", _forbid)
    except ImportError:
        pass

    cases = [
        (PythonTool(), {"code": "x = 1"}),
        (DockerTool(), {"action": "status"}),
        (RestTool(), {"method": "GET", "url": "https://example.com"}),
        (McpTool(), {"server": "filesystem", "method": "read_file"}),
        (ShellTool(), {"command": "ls"}),
        (GitTool(), {"action": "status"}),
    ]
    for tool, args in cases:
        out = tool.run(ToolInput(tool_id=tool.id, arguments=args), ALLOW)
        assert out.ok is True, f"{tool.id} failed: {out.error}"
