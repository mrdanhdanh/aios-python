"""Planner: LLM fallback (only when the deterministic pipeline fails)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..models.base import ChatMessage, ModelContract
from ..models.errors import ModelError
from ..workflow.library import WorkflowLibrary

_INTENT_RE = re.compile(r"intent:\s*(\w+)")
_WORKFLOW_RE = re.compile(r"workflow:\s*([\w\-]+)")


@dataclass
class PlanResult:
    intent: str
    workflow_names: list[str] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.5
    llm_used: bool = False
    error: bool = False


class Planner:
    """LLM-based fallback planner. Counts real model.chat calls."""

    def __init__(self) -> None:
        self._calls = 0

    @property
    def calls(self) -> int:
        return self._calls

    def reset_calls(self) -> None:
        self._calls = 0

    def plan(
        self, request: str, model: ModelContract, library: WorkflowLibrary
    ) -> PlanResult:
        if not model.is_available():
            return PlanResult(intent="chat", error=True, reasoning="model unavailable")
        names = ", ".join(library.list()) or "none"
        system_prompt = (
            "You are the AIOS orchestrator planner. Analyze the user request and reply:\n"
            f"intent: <one of chat|coding|medical|system|skill|upgrade|diagnose>\n"
            f"workflow: <name from available workflows: {names} | none>\n"
        )
        try:
            self._calls += 1
            response = model.chat(
                [
                    ChatMessage(role="system", content=system_prompt),
                    ChatMessage(role="user", content=request),
                ]
            )
        except ModelError as exc:
            return PlanResult(
                intent="chat", error=True, reasoning=f"model error: {exc}", llm_used=True
            )

        intent_match = _INTENT_RE.search(response.content)
        if not intent_match:
            return PlanResult(intent="chat", error=True, reasoning="unparseable response", llm_used=True)
        intent = intent_match.group(1)
        workflow_match = _WORKFLOW_RE.search(response.content)
        workflow_names = [workflow_match.group(1)] if workflow_match and workflow_match.group(1) != "none" else []
        return PlanResult(
            intent=intent,
            workflow_names=workflow_names,
            reasoning=response.content,
            confidence=0.6,
            llm_used=True,
        )


class PlannerStub:
    """Deterministic stub for offline tests (never calls a model)."""

    def __init__(self, intent_map: dict[str, str] | None = None) -> None:
        self._intent_map = intent_map or {}
        self._calls = 0

    @property
    def calls(self) -> int:
        return self._calls

    def reset_calls(self) -> None:
        self._calls = 0

    def plan(
        self, request: str, model: ModelContract, library: WorkflowLibrary
    ) -> PlanResult:
        intent = self._intent_map.get(request.strip(), "chat")  # exact text match
        return PlanResult(intent=intent, llm_used=False)
