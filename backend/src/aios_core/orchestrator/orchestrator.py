"""AIOS Orchestrator v1: Decision Pipeline (Normalizer → Rule → Matcher → Planner)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Literal

from .agent_selector import AgentSelector
from .normalizer import NormalizedRequest, Normalizer
from .planner import PlanResult, Planner
from .rule_engine import RuleEngine
from .workflow_matcher import WorkflowMatcher

ResolvedBy = Literal["normalizer", "rule", "workflow", "planner", "fallback"]


@dataclass
class OrchestratorResponse:
    intent: str
    agent: str | None
    workflow_name: str | None
    source: str
    resolved_by: ResolvedBy
    raw: str
    plan: PlanResult | None = None
    request_stats: dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    """Public entry: text/dict request → decision (agent + workflow).

    Offline-first: deterministic stages run before the LLM planner.
    """

    def __init__(
        self,
        rule_engine: RuleEngine,
        workflow_matcher: WorkflowMatcher,
        planner: Planner,
        normalizer: Normalizer,
        agent_selector: AgentSelector,
        model=None,
        library=None,
    ) -> None:
        self._rules = rule_engine
        self._matcher = workflow_matcher
        self._planner = planner
        self._normalizer = normalizer
        self._selector = agent_selector
        self._model = model
        self._library = library
        self._lock = threading.RLock()
        self._total_requests = 0
        self._last_planner_calls = 0

    # -- stats ----------------------------------------------------------------

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "llm_calls": self._planner.calls,
            }

    def reset(self) -> None:
        with self._lock:
            self._total_requests = 0
            self._planner.reset_calls()

    # -- pipeline -------------------------------------------------------------

    def handle(self, request: str | dict | NormalizedRequest) -> OrchestratorResponse:
        with self._lock:
            self._total_requests += 1

        # Normalize.
        if isinstance(request, NormalizedRequest):
            req = request
            skip_normalizer = True
        elif isinstance(request, dict):
            req = self._normalizer.normalize(
                request.get("text", ""), source=request.get("source", "cli")
            )
            skip_normalizer = False
        else:
            req = self._normalizer.normalize(request, source="cli")
            skip_normalizer = False
        del skip_normalizer

        # Normalizer special intents (#, !skill) → stop pipeline.
        if req.intent is not None:
            return OrchestratorResponse(
                intent=req.intent,
                agent=self._selector.select(req.intent),
                workflow_name=None,
                source=req.source,
                resolved_by="normalizer",
                raw=req.raw,
                request_stats={"confidence": req.confidence},
            )

        # Rule engine.
        rule_match = self._rules.match(req.raw)
        if rule_match is not None:
            agent = rule_match.agent or self._selector.select(rule_match.intent)
            # Matcher still runs (workflow_name as secondary info); no planner.
            wf_match = self._matcher.match(req.raw)
            return OrchestratorResponse(
                intent=rule_match.intent,
                agent=agent,
                workflow_name=wf_match.workflow_name if wf_match else None,
                source=req.source,
                resolved_by="rule",
                raw=req.raw,
                request_stats={"confidence": rule_match.priority / 10.0},
            )

        # Workflow matcher (rule-free path).
        wf_match = self._matcher.match(req.raw)
        if wf_match is not None:
            return OrchestratorResponse(
                intent="workflow",
                agent=self._selector.select("workflow"),
                workflow_name=wf_match.workflow_name,
                source=req.source,
                resolved_by="workflow",
                raw=req.raw,
                request_stats={"confidence": wf_match.confidence},
            )

        # Planner (LLM fallback).
        if isinstance(self._planner, Planner):
            plan = self._planner.plan(req.raw, self._model, self._library)
            resolved_by: ResolvedBy = "planner" if plan.llm_used else "fallback"
            return OrchestratorResponse(
                intent=plan.intent,
                agent=self._selector.select(plan.intent),
                workflow_name=plan.workflow_names[0] if plan.workflow_names else None,
                source=req.source,
                resolved_by=resolved_by,
                raw=req.raw,
                plan=plan,
                request_stats={"llm_used": plan.llm_used, "error": plan.error},
            )

        # PlannerStub path.
        plan = self._planner.plan(req.raw, None, None)  # type: ignore[arg-type]
        return OrchestratorResponse(
            intent=plan.intent,
            agent=self._selector.select(plan.intent),
            workflow_name=None,
            source=req.source,
            resolved_by="fallback",
            raw=req.raw,
            plan=plan,
            request_stats={"llm_used": False},
        )
