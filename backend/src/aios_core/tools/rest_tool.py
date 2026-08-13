"""RestTool — call_api capability, URL/method validation, NO network calls."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from .base import Tool, ToolContext, ToolInput, ToolOutput

_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"}


class RestTool(Tool):
    tool_type = "rest"
    required_scopes = ("network",)
    capabilities = ("call_api",)

    def _describe(self) -> str:
        return "REST API stub (validates method/URL, mock response — no network)"

    def _run(self, input: ToolInput, context: ToolContext) -> ToolOutput:
        args = input.arguments
        method = args.get("method")
        url = args.get("url")
        if not isinstance(method, str):
            return ToolOutput(ok=False, error="invalid argument: method (expected str)")
        if not isinstance(url, str):
            return ToolOutput(ok=False, error="invalid argument: url (expected str)")
        method_upper = method.upper()
        if method_upper not in _METHODS:
            return ToolOutput(ok=False, error=f"unsupported method: {method_upper}")
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return ToolOutput(ok=False, error=f"invalid url: {url}")
        body = args.get("body", {})
        if not isinstance(body, dict):
            return ToolOutput(ok=False, error="invalid argument: body (expected dict)")
        return ToolOutput(
            ok=True,
            result={
                "mode": "stub",
                "status_code": 200,
                "body": {"mock": True, "echo": {"method": method_upper, "url": url, "body": body}},
            },
            usage=self._stub_usage(),
        )
