import pytest

from aios import Agent, AgentRequest, AgentResponse, Capability, Client, ContractError, Tool, ToolInput, ToolOutput, Workflow


def test_public_agent_and_tool_contracts():
    class A(Agent):
        id = "agent"

    class T(Tool):
        id = "tool"
        capabilities = ("read",)

    assert A().id == "agent"
    assert T().capabilities == ("read",)
    Capability("read")


def test_tool_requires_capability():
    class T(Tool):
        id = "tool"

    with pytest.raises(ContractError):
        T()


def test_workflow_rejects_cycles():
    with pytest.raises(ContractError):
        Workflow(id="w", nodes=["a", "b"], edges=[("a", "b"), ("b", "a")])


def test_dto_round_trip_and_unknown_response_rejected():
    response = AgentResponse("ok")
    assert AgentResponse.from_dict(response.to_dict()).output == "ok"
    with pytest.raises(ValueError):
        AgentResponse.from_dict({"output": "ok", "unknown": True})


def test_client_uses_injected_transport():
    class Transport:
        def run_agent(self, agent_id, payload):
            return {"output": payload["input"]}

        def run_workflow(self, workflow_id, payload):
            return {"workflow": workflow_id}

        def call_tool(self, tool_id, payload):
            return {"value": payload["value"]}

        def get_capabilities(self):
            return [{"id": "read"}]

    client = Client(Transport())
    assert client.run_agent("a", AgentRequest("hello")).output == "hello"
    assert client.run_workflow("w")["workflow"] == "w"
    assert client.call_tool("t", ToolInput("x")).value == "x"
    assert client.get_capabilities() == [{"id": "read"}]
