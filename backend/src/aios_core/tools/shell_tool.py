"""ShellTool — run_shell capability, NO execution (v1 stub), shell scope REQUIRED."""

from __future__ import annotations

from .base import Tool, ToolContext, ToolInput, ToolOutput


class ShellTool(Tool):
    tool_type = "shell"
    required_scopes = ("shell",)  # ALWAYS required (safety — even for stubs)
    capabilities = ("run_shell",)

    def _describe(self) -> str:
        return "Shell command stub (never executes — scope 'shell' mandatory)"

    def _run(self, input: ToolInput, context: ToolContext) -> ToolOutput:
        args = input.arguments
        command = args.get("command")
        if not isinstance(command, str):
            return ToolOutput(ok=False, error="invalid argument: command (expected str)")
        if not command.strip():
            return ToolOutput(ok=False, error="empty command")
        return ToolOutput(
            ok=True,
            result={
                "mode": "stub",
                "executed": False,
                "exit_code": 0,
                "stdout": "stub: no execution",
                "stderr": "",
            },
            usage=self._stub_usage(),
        )
