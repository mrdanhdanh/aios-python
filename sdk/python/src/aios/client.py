"""Transport-only client facade; runtime policy remains outside the SDK."""
from __future__ import annotations

from typing import Any, Protocol

from .contracts import AgentRequest, AgentResponse, ToolInput, ToolOutput
from .errors import SDKError


class Transport(Protocol):
    def run_agent(self, agent_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def run_workflow(self, workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def call_tool(self, tool_id: str, payload: dict[str, Any]) -> dict[str, Any]: ...
    def get_capabilities(self) -> list[dict[str, Any]]: ...


class Client:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    def run_agent(self, agent_id: str, request: AgentRequest) -> AgentResponse:
        return AgentResponse.from_dict(self._transport.run_agent(agent_id, request.to_dict()))

    def run_workflow(self, workflow_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        result = self._transport.run_workflow(workflow_id, dict(payload or {}))
        if not isinstance(result, dict):
            raise SDKError("workflow response must be an object")
        return dict(result)

    def call_tool(self, tool_id: str, input: ToolInput) -> ToolOutput:
        return ToolOutput.from_dict(self._transport.call_tool(tool_id, input.to_dict()))

    def get_capabilities(self) -> list[dict[str, Any]]:
        result = self._transport.get_capabilities()
        if not isinstance(result, list) or not all(isinstance(item, dict) for item in result):
            raise SDKError("capabilities response must be a list of objects")
        return [dict(item) for item in result]
