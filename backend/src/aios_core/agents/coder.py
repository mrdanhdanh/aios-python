"""Coder assistant — 7 pipeline steps + Self-Fix loop (8 items per PLAN P3).

Fully deterministic, offline, 0 model. Every step is a callable
(state, request) -> dict merged under state[step_name]; default stubs are
provided. Self-Fix re-runs from `generator` with feedback up to max_fix_rounds.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import Assistant, AssistantRequest, AssistantResponse, EventSink

STEP_KEYS = (
    "requirement",
    "planner",
    "generator",
    "static_analysis",
    "formatter",
    "unit_test",
    "integration_test",
)
StepFn = Callable[[dict, AssistantRequest], dict]


class CoderResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    test_reports: dict[str, Any] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)  # static analysis (advisory)
    iterations: int = 0
    passed: bool = False
    history: list[str] = Field(default_factory=list)


# -- default deterministic stubs -------------------------------------------------

def _step_requirement(state: dict, request: AssistantRequest) -> dict:
    return {"requirement": request.text.strip()}


def _step_planner(state: dict, request: AssistantRequest) -> dict:
    return {"plan": [f"implement: {state['requirement']}", "validate"]}


def _step_generator(state: dict, request: AssistantRequest) -> dict:
    requirement = repr(state["requirement"])  # C1-04: escape quotes/backslashes
    docstring = f"\"\"\"Generated stub for: {requirement}\"\"\""
    if state.get("feedback"):
        docstring += f"\n# feedback: {repr(state['feedback'])}"  # C2-09: escape too
    code = f"{docstring}\ndef main():\n    return {requirement}\n"
    return {"code": code}


def _step_static_analysis(state: dict, request: AssistantRequest) -> dict:
    code = state["code"]
    issues: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        issues.append(f"syntax error: {exc}")
        return {"issues": issues}
    if not any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in ast.walk(tree)):
        issues.append("missing def main")
    return {"issues": issues}


def _step_formatter(state: dict, request: AssistantRequest) -> dict:
    code = state["code"].replace("\t", "    ")
    lines = [ln.rstrip() for ln in code.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    formatted = "\n".join(lines).rstrip() + "\n"
    return {"code": formatted}


def _step_unit_test(state: dict, request: AssistantRequest) -> dict:
    code = state["code"]
    try:
        ns: dict = {}
        exec(code, ns)  # noqa: S102 — sandboxed stub pipeline (deterministic)
        main = ns.get("main")
        if main is None:
            return {"passed": False, "detail": "no main function"}
        main()
        return {"passed": True, "detail": "unit test passed"}
    except SyntaxError as exc:
        return {"passed": False, "detail": f"syntax error: {exc}"}
    except Exception as exc:  # noqa: BLE001 — deterministic report
        return {"passed": False, "detail": str(exc)}


def _step_integration_test(state: dict, request: AssistantRequest) -> dict:
    return {"passed": True, "detail": "integration stub"}


DEFAULT_STEPS: dict[str, StepFn] = {
    "requirement": _step_requirement,
    "planner": _step_planner,
    "generator": _step_generator,
    "static_analysis": _step_static_analysis,
    "formatter": _step_formatter,
    "unit_test": _step_unit_test,
    "integration_test": _step_integration_test,
}


class CoderAssistant(Assistant):
    name = "coder"
    intent = "coding"
    description = "Code generator: requirement → plan → generate → static analysis → format → unit/integration test → self-fix"

    def __init__(
        self,
        steps: dict[str, StepFn] | None = None,
        max_fix_rounds: int = 2,
        event_sink: EventSink | None = None,
    ) -> None:
        super().__init__(event_sink=event_sink)
        if max_fix_rounds < 0:
            raise ValueError("max_fix_rounds must be >= 0")
        unknown = set((steps or {}).keys()) - set(STEP_KEYS)
        if unknown:
            raise ValueError(f"unknown step keys: {sorted(unknown)}")
        self._steps = {**DEFAULT_STEPS, **(steps or {})}
        self._max_fix_rounds = max_fix_rounds

    def _process(self, request: AssistantRequest) -> AssistantResponse:
        state: dict = {"request": request.model_dump()}
        history: list[str] = []
        iterations = 0
        passed = False
        last_reports: dict = {}

        for _ in range(1 + self._max_fix_rounds):
            iterations += 1
            keys = STEP_KEYS if iterations == 1 else STEP_KEYS[2:]  # re-run from generator
            for key in keys:
                history.append(key)
                result = self._steps[key](state, request)
                state[key] = result
                state.update(result)  # flat merge for direct keys (code/requirement/...)
            last_reports = {
                "unit": state["unit_test"],
                "integration": state["integration_test"],
            }
            passed = bool(state["unit_test"]["passed"] and state["integration_test"]["passed"])
            if passed:
                break
            state["feedback"] = {"unit": state["unit_test"], "integration": state["integration_test"]}
            if iterations <= self._max_fix_rounds:
                history.append(f"fix_round:{iterations}")

        code = state.get("code", "")
        result = CoderResult(
            code=code,
            test_reports=last_reports,
            issues=list(state.get("static_analysis", {}).get("issues", [])),
            iterations=iterations,
            passed=passed,
            history=history,
        )
        text = f"generated code (iterations={iterations}, passed={passed})\n\n{code}"
        if len(text) > 2000:
            text = text[:2000] + "\n...[truncated]"
        return AssistantResponse(
            text=text,
            intent=self.intent,
            metadata={"result": result.model_dump()},
        )
