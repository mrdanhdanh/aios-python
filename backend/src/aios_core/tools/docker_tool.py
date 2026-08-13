"""DockerTool — manage_container capability, mock state, no docker calls."""

from __future__ import annotations

from typing import Any

from .base import Tool, ToolContext, ToolInput, ToolOutput

MOCK_IMAGES: tuple[str, ...] = ("python:3.12-slim", "node:20-alpine", "nginx:latest")
_ACTIONS = {"list_images", "inspect", "status"}


class DockerTool(Tool):
    tool_type = "docker"
    required_scopes = ("docker",)
    capabilities = ("manage_container",)

    def _describe(self) -> str:
        return "Docker container management stub (mock state — no daemon calls)"

    def _run(self, input: ToolInput, context: ToolContext) -> ToolOutput:
        args = input.arguments
        action = args.get("action")
        if not isinstance(action, str):
            return ToolOutput(ok=False, error="invalid argument: action (expected str)")
        if action not in _ACTIONS:
            return ToolOutput(ok=False, error=f"unsupported action: {action}")
        if action == "list_images":
            return ToolOutput(
                ok=True,
                result={"mode": "stub", "images": list(MOCK_IMAGES), "count": len(MOCK_IMAGES)},
                usage=self._stub_usage(),
            )
        if action == "inspect":
            image = args.get("image")
            if image is not None and not isinstance(image, str):
                return ToolOutput(ok=False, error="invalid argument: image (expected str)")
            return ToolOutput(
                ok=True,
                result={"mode": "stub", "image": image or "python:3.12-slim", "state": "mock running"},
                usage=self._stub_usage(),
            )
        return ToolOutput(
            ok=True,
            result={"mode": "stub", "daemon": "mock ok", "containers_running": 0},
            usage=self._stub_usage(),
        )
