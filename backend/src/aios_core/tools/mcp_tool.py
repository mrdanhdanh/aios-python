"""McpTool — mcp_call capability, fake MCP server registry, no connections."""

from __future__ import annotations

from typing import Any

from .base import Tool, ToolContext, ToolInput, ToolOutput

MCP_SERVERS: dict[str, list[str]] = {
    "filesystem": ["read_file", "write_file", "list_dir"],
    "fetch": ["fetch_url"],
}


def _validate_servers(servers: dict) -> None:
    # C1-10/C2-08: dict[str, list[str]] — key non-empty, methods str non-empty;
    # empty dict allowed; empty method LIST allowed (all calls -> unknown method).
    if not isinstance(servers, dict):
        raise ValueError("servers must be a dict[str, list[str]]")
    for name, methods in servers.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("server name must be a non-empty str")
        if not isinstance(methods, list) or not all(
            isinstance(m, str) and m.strip() for m in methods
        ):
            raise ValueError(f"server {name!r} methods must be list[str] of non-empty str")


class McpTool(Tool):
    tool_type = "mcp"
    required_scopes = ("network",)
    capabilities = ("mcp_call",)

    def _describe(self) -> str:
        return "MCP stub (fake server registry — no real connections)"

    def _configure(self, **kwargs: Any) -> None:
        servers = kwargs.get("servers")
        if servers is None:
            servers = MCP_SERVERS
        _validate_servers(servers)
        self._servers = servers  # read-only after init (C1-14 thread-safe)

    def _run(self, input: ToolInput, context: ToolContext) -> ToolOutput:
        args = input.arguments
        server = args.get("server")
        method = args.get("method")
        if not isinstance(server, str):
            return ToolOutput(ok=False, error="invalid argument: server (expected str)")
        if not isinstance(method, str):
            return ToolOutput(ok=False, error="invalid argument: method (expected str)")
        if server not in self._servers:
            return ToolOutput(ok=False, error=f"unknown mcp server: {server}")
        if method not in self._servers[server]:
            return ToolOutput(ok=False, error=f"unknown method: {server}.{method}")
        params = args.get("params", {})
        if not isinstance(params, dict):
            return ToolOutput(ok=False, error="invalid argument: params (expected dict)")
        return ToolOutput(
            ok=True,
            result={"mode": "stub", "server": server, "method": method,
                    "result": {"mock": True, "params": params}},
            usage=self._stub_usage(),
        )
