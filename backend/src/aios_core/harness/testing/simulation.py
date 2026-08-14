"""Simulation (TASK-031, H3): Fake Runtime/Tool + runner — KHÔNG side effect.

Không import sqlite3/httpx/socket/requests/os (INV-020b). Deterministic,
offline: request → intent → agent → policy → fake plan/graph → outcome.
"""

from __future__ import annotations

from typing import Any, Callable

from .contracts import (
    Fault,
    ExpectedResult,
    Scenario,
    SimulationOutcome,
    SimulationStatus,
)
from .errors import SimulationError
from .faults import FaultInjector, ResourceExhaustedError

_DEFAULT_INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "coding": ("review", "fix", "implement", "refactor", "write code"),
    "testing": ("test", "unit test"),
    "writing": ("write", "summarize", "document"),
    "planning": ("plan", "design"),
}


class FakeRuntime:
    """Deterministic detectors — injectable, defaults keyword-based (C3-02)."""

    def __init__(
        self,
        *,
        intent: Callable[[str], str] | None = None,
        resolve_agent: Callable[[str], str] | None = None,
        check_policy: Callable[[str, str], str] | None = None,
        capabilities: Callable[[str], list[str]] | None = None,
    ) -> None:
        self._intent = intent or self._default_intent
        self._agent = resolve_agent or self._default_agent
        self._policy = check_policy or (lambda request, intent: "allow")  # R2-1
        self._capabilities = capabilities or self._default_capabilities

    def intent(self, request: str) -> str:
        return self._intent(request)

    def resolve_agent(self, intent: str) -> str:
        return self._agent(intent)

    def check_policy(self, request: str, intent: str) -> str:
        return self._policy(request, intent)

    def capabilities(self, agent: str) -> list[str]:
        return self._capabilities(agent)

    # -- defaults ------------------------------------------------------------

    @staticmethod
    def _default_intent(request: str) -> str:
        lowered = request.lower()
        for intent, keywords in _DEFAULT_INTENT_KEYWORDS.items():
            if any(k in lowered for k in keywords):
                return intent
        return "general"

    @staticmethod
    def _default_agent(intent: str) -> str:
        return {"coding": "coder", "testing": "coder",  # R2-2
                "writing": "writer", "planning": "generalist"}.get(intent, "generalist")

    @staticmethod
    def _default_capabilities(agent: str) -> list[str]:
        return {"coder": ["filesystem", "python"], "writer": ["filesystem"],
                "generalist": ["filesystem"]}.get(agent, ["filesystem"])


class FakeTool:
    """Deterministic tool — ghi last_call, behavior cố định."""

    def __init__(self, name: str, behavior: dict[str, Any] | None = None) -> None:
        self.name = name
        self.behavior = behavior if behavior is not None else {"ok": True}
        self.last_call: dict[str, Any] | None = None

    def run(self, input_: dict[str, Any]) -> dict[str, Any]:
        self.last_call = {"name": self.name, "input": input_,
                          "output": dict(self.behavior)}
        return dict(self.behavior)


class SimulationRunner:
    """Chạy scenario qua pipeline fake — thuần, không state (C3-06)."""

    def __init__(self, runtime: FakeRuntime | None = None) -> None:
        self._runtime = runtime or FakeRuntime()

    def run(self, scenario: Scenario) -> SimulationOutcome:
        request = str(scenario.input.get("request", ""))
        intent = self._runtime.intent(request)
        agent = self._runtime.resolve_agent(intent)
        policy = self._runtime.check_policy(request, intent)
        injector = FaultInjector(scenario.faults)
        tool_calls: list[dict] = []
        executed: list[str] = []
        outputs_ok = True

        try:
            if policy == "deny":
                # P1-02/C2-02: không chạy tool nào
                return self._blocked_outcome(scenario, intent, agent, policy)
            nodes = self._plan(scenario)
            for node in nodes:
                executed.append(node)  # P1-03: trước attempt đầu
                targets = self._targets(node, first=node == nodes[0])
                fault_target = next(
                    (t for t in targets if injector.next_for(t) is not None), None)
                if fault_target is None:
                    result = self._call_tool(node, request, tool_calls)
                else:
                    try:
                        result, _ = injector.apply(
                            fault_target,
                            lambda: self._call_tool(node, request, tool_calls))
                    except (TimeoutError, RuntimeError, ResourceExhaustedError):
                        # retry 1 lần — fault đã inject xong → thành công
                        try:
                            result, _ = injector.apply(
                                fault_target,
                                lambda: self._call_tool(node, request, tool_calls))
                            self._recover(injector, fault_target, scenario)
                        except Exception as exc:  # noqa: BLE001 — không recover
                            raise SimulationError(
                                f"fault not recovered on {node}: {exc}") from exc
                if not result.get("ok", True):
                    outputs_ok = False
        except SimulationError as exc:
            return self._outcome(scenario, SimulationStatus.ERROR, intent, agent,
                                 policy, executed, tool_calls,
                                 injector, outputs_ok, summary=str(exc))
        return self._finalize(scenario, intent, agent, policy, executed,
                              tool_calls, injector, outputs_ok)

    # -- pipeline pieces -----------------------------------------------------

    def _plan(self, scenario: Scenario) -> list[str]:
        """Node `model` luôn đầu (C1-02) + capability nodes (C1-01)."""
        return ["model"] + [f"capability:{c}"
                            for c in scenario.expect.required_capabilities]

    @staticmethod
    def _targets(node: str, *, first: bool) -> list[str]:
        if node == "model":
            # P1-01: resource fault áp tại node đầu (model)
            return ["resource", "model"] if first else ["model"]
        return [f"tool:{node.removeprefix('capability:')}"]

    def _call_tool(self, node: str, request: str,
                   tool_calls: list[dict]) -> dict[str, Any]:
        if node == "model":
            tool = FakeTool("model", {"ok": True, "kind": "model"})
            call_input = {"request": request}
        else:
            capability = node.removeprefix("capability:")
            tool = FakeTool(f"tool:{capability}")
            call_input = {"request": request, "capability": capability}
        call = tool.run(call_input)
        ok = call.get("ok", True)
        tool_calls.append({"node": node, "tool": tool.name,
                           "input": call_input, "ok": ok,
                           "status": "ok" if ok else "failed",
                           "attempt": len(tool_calls) + 1})  # attempt = len+1
        return call

    @staticmethod
    def _recover(injector: FaultInjector, target: str, scenario: Scenario) -> None:
        fault = next((f for f in scenario.faults if f.target == target), None)
        if fault is None:
            return
        kind = {"timeout": "retry", "failure": "fallback",
                "exhausted": "queued"}.get(fault.type.value, "retry")
        injector.recover(target, kind, fault)

    def _blocked_outcome(self, scenario: Scenario, intent: str, agent: str,
                         policy: str) -> SimulationOutcome:
        expect = scenario.expect
        expected_deny = expect.policy == "deny"
        matches = {
            "intent": expect.intent is None or expect.intent == intent,
            "agent": expect.agent is None or expect.agent == agent,
            "policy": True,
        }
        return SimulationOutcome(
            scenario_id=scenario.id,
            status=SimulationStatus.SUCCESS if expected_deny else SimulationStatus.MISMATCH,
            intent=intent, agent=agent, policy=policy,
            expectation_matches=matches,
            verification={"tests_pass": True, "no_policy_bypass": True},
            summary="blocked-as-expected" if expected_deny
                    else "blocked-but-not-expected",
            metrics={"nodes": 0, "tool_calls": 0, "faults_injected": 0,
                     "recovery_events": 0},
        )

    def _finalize(self, scenario: Scenario, intent: str, agent: str, policy: str,
                  executed: list[str], tool_calls: list[dict],
                  injector: FaultInjector, outputs_ok: bool) -> SimulationOutcome:
        expect = scenario.expect
        capabilities = self._runtime.capabilities(agent)
        matches = {
            "intent": expect.intent is None or expect.intent == intent,
            "agent": expect.agent is None or expect.agent == agent,
        }
        if expect.policy is not None:  # C2-01
            matches["policy"] = expect.policy == policy
        if expect.required_capabilities:
            matches["required_capabilities"] = all(
                c in capabilities for c in expect.required_capabilities)
        has_faults = bool(scenario.faults)
        tests_pass = outputs_ok and (
            injector.recovery_events if has_faults else True)
        if isinstance(tests_pass, list):
            tests_pass = bool(tests_pass)
        no_bypass = len(tool_calls) == 0 or policy != "deny"
        verification = {"tests_pass": bool(tests_pass),
                        "no_policy_bypass": bool(no_bypass)}
        all_match = all(matches.values())
        status = SimulationStatus.SUCCESS if all_match else SimulationStatus.MISMATCH
        summary = f"{status.value}: {len(executed)} nodes, {len(tool_calls)} tool calls"
        if scenario.faults:
            summary += f", {len(injector.recovery_events)} recovery"
        return self._outcome(scenario, status, intent, agent, policy, executed,
                             tool_calls, injector, outputs_ok, summary=summary,
                             matches=matches, verification=verification)

    def _outcome(self, scenario: Scenario, status: SimulationStatus,
                 intent: str, agent: str, policy: str, executed: list[str],
                 tool_calls: list[dict], injector: FaultInjector,
                 outputs_ok: bool, *, summary: str,
                 matches: dict[str, bool] | None = None,
                 verification: dict[str, bool] | None = None) -> SimulationOutcome:
        return SimulationOutcome(
            scenario_id=scenario.id,
            status=status,
            intent=intent, agent=agent, policy=policy,
            executed_nodes=executed,
            tool_calls=tool_calls[:100],  # C2-06 cap
            faults_injected=injector.injected,
            recovery_events=injector.recovery_events,
            expectation_matches=matches or {},
            verification=verification or {"tests_pass": outputs_ok,
                                          "no_policy_bypass": True},
            summary=summary,
            metrics={"nodes": len(executed), "tool_calls": len(tool_calls),
                     "faults_injected": len(injector.injected),
                     "recovery_events": len(injector.recovery_events)},
        )
