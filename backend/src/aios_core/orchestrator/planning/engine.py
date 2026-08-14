"""Planning engine (TASK-026 §YC-9/10): offline-first ladder + LLM fallback.

Ladder (PLAN §13): workflow → template → rule → LLM. Only the LLM path
calls the (old) Planner. ``llm_calls`` counts pipeline reliance on LLM and
increments right after planner.plan() even on error paths (C2-08).
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from ...kernel.execution_plan import ExecutionPlan, ExecutionPlanStatus, PlanNode, PlanNodeType
from .capability_resolver import CapabilityResolver
from .contracts import (
    GoalAnalysis,
    PlanSource,
    PlanningResult,
    PlanValidationReport,
    RiskReport,
    TaskSpec,
    ValidationRule,
    PlanValidationIssue,
)
from .dependency_analyzer import DependencyAnalyzer
from .execution_planner import ExecutionPlanner
from .goal_analyzer import GoalAnalyzer
from .risk_analyzer import RiskAnalyzer
from .task_decomposer import TaskDecomposer
from .validation import PlanValidator, ValidationContext

_AGENT_FOR_INTENT = {
    "review": "coder", "test": "coder", "coding": "coder",
    "chat": "general", "doctor": "doctor", "system": "system_doctor",
}


@dataclass
class _RouteRequest:
    """Duck-typed RouteRequest (INV-005 rule A — no aios_core.models import)."""

    policy: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class PlanningEngine:
    """Orchestrates the 7-module planning pipeline (no God Object)."""

    def __init__(
        self,
        library: Any,
        capabilities: Any,
        policy: Any | None = None,
        resources: Any | None = None,
        planner: Any | None = None,  # Planner (old) — LLM fallback
        model: Any | None = None,  # ModelContract (untyped — INV-005 rule A)
        router: Any | None = None,  # ModelRouter (untyped)
        registry: Any | None = None,  # ModelRegistry (untyped)
        settings: Any | None = None,
    ) -> None:
        self._library = library
        self._capabilities = capabilities
        self._policy = policy
        self._resources = resources
        self._planner = planner
        self._model = model
        self._router = router
        self._registry = registry
        self._settings = settings
        self._analyzer = GoalAnalyzer()
        self._decomposer = TaskDecomposer()
        self._dependency = DependencyAnalyzer()
        self._capability_resolver = CapabilityResolver()
        self._risk = RiskAnalyzer()
        self._builder = ExecutionPlanner()
        self._validator = PlanValidator()  # INV-014 gate (arch-asserted)
        self._llm_calls = 0
        self._last_result: PlanningResult | None = None
        self._lock = threading.RLock()

    # -- public API ----------------------------------------------------------

    @property
    def llm_calls(self) -> int:
        with self._lock:
            return self._llm_calls

    def reset_calls(self) -> None:
        with self._lock:
            self._llm_calls = 0

    @property
    def last_result(self) -> PlanningResult | None:
        with self._lock:
            return self._last_result

    def plan(self, request: Any) -> PlanningResult:
        started = time.monotonic()
        goal = self._analyzer.analyze(request, self._library)

        try:
            if goal.source is PlanSource.WORKFLOW:
                result = self._plan_known_workflow(request, goal)
            else:
                tasks = self._decomposer.decompose(goal, request)
                if not tasks:
                    result = self._plan_with_llm(request, goal)
                else:
                    result = self._plan_deterministic(request, goal, tasks)
        except ValidationError as exc:
            raise self._to_planning_error(exc) from exc

        result = result.model_copy(
            update={"latency_ms": int((time.monotonic() - started) * 1000)}
        )
        with self._lock:
            self._last_result = result
        return result

    # -- deterministic paths --------------------------------------------------

    def _plan_known_workflow(self, request: Any, goal: GoalAnalysis) -> PlanningResult:
        plan = self._builder.build([], goal, request, self._library, self._settings)
        return self._finalize(request, plan, goal, PlanSource.WORKFLOW, 0, RiskReport())

    def _plan_deterministic(
        self, request: Any, goal: GoalAnalysis, tasks: list[TaskSpec]
    ) -> PlanningResult:
        from .templates import get_template

        ordered, invalid_ids = self._dependency.analyze(tasks)
        tasks, capability_risks = self._capability_resolver.resolve(
            ordered, self._capabilities, intent=goal.intent)
        risks = RiskReport(items=capability_risks.items + self._risk.analyze(
            goal, tasks, self._settings).items)
        source = PlanSource.TEMPLATE if get_template(goal.intent) is not None else PlanSource.RULE
        plan = self._builder.build(tasks, goal, request, self._library, self._settings)
        return self._finalize(request, plan, goal, source, 0, risks)

    def _finalize(
        self, request: Any, plan: ExecutionPlan, goal: GoalAnalysis,
        source: PlanSource, llm_calls: int, risks: RiskReport,
    ) -> PlanningResult:
        report = self._validator.validate(plan, ValidationContext(
            capabilities=self._capabilities, policy=self._policy,
            resources=self._resources, settings=self._settings))
        if not report.valid:
            from ..errors import PlanningError

            raise PlanningError("plan validation failed", report=report)
        plan = plan.model_copy(update={"status": ExecutionPlanStatus.READY})
        needs_approval = any(
            issue.rule is ValidationRule.POLICY and not issue.fatal
            for issue in report.issues
        )
        return PlanningResult(
            plan=plan, source=source, llm_calls=llm_calls,
            validation=report, needs_approval=needs_approval,
            goal=goal, risks=risks,
        )

    # -- LLM fallback (PLAN §13 bậc 4) -----------------------------------------

    def _plan_with_llm(self, request: Any, goal: GoalAnalysis) -> PlanningResult:
        if self._planner is None:
            from ..errors import PlanningError

            raise PlanningError("llm planning unavailable")
        model = self._resolve_model(request)
        plan_result = self._planner.plan(request.text, model, self._library)
        self._increment_llm_calls()  # C2-08: after the call, even on error
        if plan_result.error:
            from ..errors import PlanningError

            raise PlanningError(f"llm planning failed: {plan_result.reasoning}")
        return self._plan_from_llm_result(request, goal, plan_result)

    def _resolve_model(self, request: Any) -> Any:
        from ..errors import PlanningError

        if self._router is not None:
            try:
                # Duck-typed RouteRequest (INV-005 rule A — no models import).
                self._router.select(_RouteRequest(policy=request.policy))
            except Exception as exc:  # RouterError / ModelError
                raise PlanningError(f"no model available: {exc}") from exc
            name = getattr(getattr(self._router, "last_decision", None), "model_name", None)
            if name is None or self._registry is None:
                raise PlanningError("no model available")
            return self._registry.get(name)
        if self._model is None:
            raise PlanningError("no model available")
        return self._model

    def _plan_from_llm_result(self, request: Any, goal: GoalAnalysis, plan_result: Any) -> PlanningResult:
        from ..errors import PlanningError
        from .templates import get_template

        intent = _normalize_intent(plan_result.intent)
        workflow_name = plan_result.workflow_names[0] if plan_result.workflow_names else None
        if workflow_name is not None and self._library is not None:
            try:
                definition = self._library.get(workflow_name)
            except KeyError:
                definition = None
            if definition is not None:
                new_goal = goal.model_copy(update={"intent": intent,
                                                    "matched_workflow": workflow_name,
                                                    "source": PlanSource.LLM})
                plan = self._builder.build([], new_goal, request, self._library, self._settings)
                return self._finalize(request, plan, new_goal, PlanSource.LLM, 1, RiskReport())
        template = get_template(intent)
        tasks = template.to_task_specs() if template is not None else _skeleton_for_intent(intent)
        new_goal = goal.model_copy(update={"intent": intent, "source": PlanSource.LLM})
        plan = self._builder.build(tasks, new_goal, request, self._library, self._settings)
        return self._finalize(request, plan, new_goal, PlanSource.LLM, 1, RiskReport())

    def _increment_llm_calls(self) -> None:
        with self._lock:
            self._llm_calls += 1

    # -- helpers ---------------------------------------------------------------

    def _to_planning_error(self, exc: ValidationError):
        from ..errors import PlanningError

        message = str(exc)
        if "cycle detected" in message:
            rule = ValidationRule.CYCLE
        elif "depends on unknown" in message:
            rule = ValidationRule.DEPENDENCY
        else:
            rule = ValidationRule.CONTRACT
        issues = [PlanValidationIssue(
            rule=rule, node_id="", message=message, fatal=True)]
        return PlanningError(message, report=PlanValidationReport(issues=issues))


def _normalize_intent(intent: str) -> str:
    if intent == "medical":
        return "doctor"  # C2-05 v2
    if intent in _AGENT_FOR_INTENT:
        return intent
    return "chat"


def _skeleton_for_intent(intent: str) -> list[TaskSpec]:
    """Deterministic post-LLM skeleton (C2-05 v2): generic 2-node fallback."""
    return [
        TaskSpec(id="T1", name=intent, type=PlanNodeType.LLM,
                 agent=_AGENT_FOR_INTENT.get(intent, "general"), depends_on=[]),
        TaskSpec(id="T2", name="report", type=PlanNodeType.TASK,
                 agent=_AGENT_FOR_INTENT.get(intent, "general"), depends_on=["T1"]),
    ]
