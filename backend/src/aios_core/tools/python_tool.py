"""PythonTool — execute_code capability, ast.parse validation, NO exec (v1 stub)."""

from __future__ import annotations

import ast
from typing import Any

from .base import Tool, ToolContext, ToolInput, ToolOutput


class PythonTool(Tool):
    tool_type = "python"
    required_scopes = ("filesystem",)
    capabilities = ("execute_code",)

    def _describe(self) -> str:
        return "Python code validation stub (ast.parse only — sandbox in P4)"

    def _configure(self, **kwargs: Any) -> None:
        # C1-08 note: real exec in P4 must renegotiate scopes via sandbox;
        # do NOT map python->filesystem by default ALLOW of PermissionService.
        self._execute = bool(kwargs.get("execute", False))  # forward-compat only

    def _run(self, input: ToolInput, context: ToolContext) -> ToolOutput:
        args = input.arguments
        code = args.get("code")
        if not isinstance(code, str):
            return ToolOutput(ok=False, error="invalid argument: code (expected str)")
        if not code.strip():
            return ToolOutput(ok=False, error="empty code")
        try:
            ast.parse(code)
        except SyntaxError as exc:
            return ToolOutput(
                ok=False,
                error=f"python syntax error: {exc.msg} (line {exc.lineno})",
            )
        return ToolOutput(
            ok=True,
            result={
                "mode": "stub",
                "syntax_ok": True,
                "executed": False,
                "note": "not executed (v1 stub — sandbox in P4)",
            },
            usage=self._stub_usage(),
        )
