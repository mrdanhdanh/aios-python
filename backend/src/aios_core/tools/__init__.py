"""AIOS Execution Plane tools (TASK-014) — 6 stub types + ToolRegistry.

Hard isolation: only aios_core.metadata + pydantic + stdlib; all runtime
interactions via ToolContext injectable callables.
"""

from .base import EVENT_TOOL_FINISHED, EVENT_TOOL_STARTED, Tool, ToolContext, ToolInput, ToolOutput
from .docker_tool import DockerTool
from .git_tool import GitTool
from .mcp_tool import MCP_SERVERS, McpTool
from .python_tool import PythonTool
from .registry import ToolRegistry
from .rest_tool import RestTool
from .shell_tool import ShellTool

__all__ = [
    "EVENT_TOOL_FINISHED",
    "EVENT_TOOL_STARTED",
    "Tool",
    "ToolContext",
    "ToolInput",
    "ToolOutput",
    "DockerTool",
    "GitTool",
    "MCP_SERVERS",
    "McpTool",
    "PythonTool",
    "ToolRegistry",
    "RestTool",
    "ShellTool",
    "build_default_tools",
    "build_tool_registry",
]


def build_default_tools() -> list[Tool]:
    """Deterministic fixed order: python, docker, rest, mcp, shell, git (AC13)."""
    return [
        PythonTool(),
        DockerTool(),
        RestTool(),
        McpTool(),
        ShellTool(),
        GitTool(),
    ]


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    for tool in build_default_tools():
        registry.register(tool)
    return registry
