"""GitTool — git_ops capability, mock repo state, no git CLI calls."""

from __future__ import annotations

from .base import Tool, ToolContext, ToolInput, ToolOutput

MOCK_REPO_STATE: dict = {"branch": "main", "status": "clean", "commits": ["abc1234 init"]}
_ACTIONS = {"status", "branch", "log"}


class GitTool(Tool):
    tool_type = "git"
    required_scopes = ("git",)
    capabilities = ("git_ops",)

    def _describe(self) -> str:
        return "Git operations stub (mock repo state — no git CLI)"

    def _run(self, input: ToolInput, context: ToolContext) -> ToolOutput:
        args = input.arguments
        action = args.get("action")
        if not isinstance(action, str):
            return ToolOutput(ok=False, error="invalid argument: action (expected str)")
        if action not in _ACTIONS:
            return ToolOutput(ok=False, error=f"unsupported action: {action}")
        if action == "status":
            result = {"mode": "stub", "branch": "main", "status": "clean"}
        elif action == "branch":
            result = {"mode": "stub", "branch": "main"}
        else:  # log
            result = {"mode": "stub", "commits": list(MOCK_REPO_STATE["commits"])}
        return ToolOutput(ok=True, result=result, usage=self._stub_usage())
