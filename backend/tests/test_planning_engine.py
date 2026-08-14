"""TASK-026 — Planning Engine tests (M5-P9): goal analysis, decomposition,
dependency, capability, risk, plan build, INV-014 validation, engine ladder."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from pydantic import ValidationError

from aios_core.capabilities import CapabilityRegistry
from aios_core.kernel.dag import validate_dag
from aios_core.kernel.execution_plan import (
    ExecutionPlan,
    ExecutionPlanStatus,
    PlanNode,
    PlanNodeType,
)
from aios_core.kernel.services import PermissionScope
from aios_core.orchestrator.errors import PlanningError
from aios_core.orchestrator.planning import (
    GoalAnalysis,
    GoalAnalyzer,
    GoalComplexity,
    PlanSource,
    PlanningEngine,
    PlanningResult,
    PlanValidationReport,
    RiskReport,
    TaskSpec,
    TemplateSkeleton,
    ValidationRule,
    register_template,
)
from aios_core.orchestrator.planning.capability_resolver import CapabilityResolver
from aios_core.orchestrator.planning.dependency_analyzer import DependencyAnalyzer
from aios_core.orchestrator.planning.execution_planner import ExecutionPlanner
from aios_core.orchestrator.planning.risk_analyzer import RiskAnalyzer
from aios_core.orchestrator.planning.validation import PlanValidator, ValidationContext
from aios_core.workflow.definition import WorkflowDefinition
from aios_core.workflow.library import WorkflowLibrary

REVIEW_TEMPLATE_DEPS = [[], ["T1"], ["T1"], ["T2", "T3"], ["T4"], ["T5"]]


@dataclass
class FakeRequest:
    text: str
    policy: str | None = None
    source: str = "test"


def make_capabilities(*names: str) -> CapabilityRegistry:
    registry = CapabilityRegistry()
    for name in names:
        registry.register_capability(name)
    return registry


def make_library() -> WorkflowLibrary:
    return WorkflowLibrary()


def make_engine(
    capabilities: CapabilityRegistry | None = None,
    library: WorkflowLibrary | None = None,
    planner=None,
    router=None,
    registry=None,
    settings=None,
    policy=None,
    model=None,
) -> PlanningEngine:
    from aios_core.config import PlanningSettings

    return PlanningEngine(
        library=library or make_library(),
        capabilities=capabilities or make_capabilities(
            "code_analysis", "test_writing", "test_run", "reporting",
            "code_generation"),
        policy=policy,
        planner=planner,
        model=model,
        router=router,
        registry=registry,
        settings=settings or PlanningSettings(),
    )


def review_tasks() -> list[TaskSpec]:
    from aios_core.orchestrator.planning.templates import get_template

    return get_template("review").to_task_specs()


# ---------------------------------------------------------------------------
# YC-1 — Contracts
# ---------------------------------------------------------------------------

class TestContracts:
    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            TaskSpec(id="T1", name="x", type=PlanNodeType.TASK, bogus=1)
        with pytest.raises(ValidationError):
            GoalAnalysis(intent="chat", complexity=GoalComplexity.SIMPLE,
                         source=PlanSource.RULE, bogus=1)

    def test_risk_highest(self):
        assert RiskReport(items=[]).highest is None
        from aios_core.orchestrator.planning import RiskItem

        report = RiskReport(items=[RiskItem(level="low", kind="a", message=""),
                                   RiskItem(level="high", kind="b", message="")])
        assert report.highest == "high"

    def test_validation_rule_8(self):
        assert {rule.value for rule in ValidationRule} == {
            "contract", "capability", "permission", "policy",
            "dependency", "resource", "cycle", "timeout",
        }

    def test_report_valid(self):
        from aios_core.orchestrator.planning import PlanValidationIssue

        report = PlanValidationReport(issues=[PlanValidationIssue(
            rule=ValidationRule.CYCLE, message="x", fatal=True)])
        assert report.valid is False
        assert PlanValidationReport().valid is True

    def test_planning_error_keeps_report(self):
        report = PlanValidationReport()
        error = PlanningError("boom", report=report)
        assert error.report is report


# ---------------------------------------------------------------------------
# YC-2 — Goal Analyzer
# ---------------------------------------------------------------------------

class TestGoalAnalyzer:
    def test_review_complex(self):
        goal = GoalAnalyzer().analyze(FakeRequest("Review module authentication và viết test"),
                                      make_library())
        assert goal.intent == "review"
        assert "authentication" in goal.target
        assert goal.complexity is GoalComplexity.COMPLEX

    def test_simple(self):
        goal = GoalAnalyzer().analyze(FakeRequest("check status"), make_library())
        assert goal.complexity is GoalComplexity.SIMPLE
        assert goal.intent == "system"  # keyword "status" -> system

    def test_open(self):
        goal = GoalAnalyzer().analyze(
            FakeRequest("Phân tích toàn bộ dự án rồi đề xuất kiến trúc mới"),
            make_library())
        assert goal.complexity is GoalComplexity.OPEN

    def test_workflow_match(self):
        library = make_library()
        library.register(WorkflowDefinition(
            name="crud-generator", version="1.0.0", description="create crud api",
            nodes=[{"id": "N1", "type": "task", "name": "gen",
                    "capabilities": [], "depends_on": []}]))
        goal = GoalAnalyzer().analyze(FakeRequest("Create CRUD API"), library)
        assert goal.matched_workflow == "crud-generator"
        assert goal.source is PlanSource.WORKFLOW

    def test_deterministic(self):
        analyzer = GoalAnalyzer()
        first = analyzer.analyze(FakeRequest("Review module auth"), make_library())
        second = analyzer.analyze(FakeRequest("Review module auth"), make_library())
        assert first.model_dump() == second.model_dump()


# ---------------------------------------------------------------------------
# YC-3 — Decomposer
# ---------------------------------------------------------------------------

class TestDecomposer:
    def test_review_template_exact(self):
        from aios_core.orchestrator.planning.task_decomposer import TaskDecomposer

        goal = GoalAnalysis(intent="review", complexity=GoalComplexity.COMPLEX,
                            source=PlanSource.RULE)
        tasks = TaskDecomposer().decompose(goal, FakeRequest("review"))
        assert [t.id for t in tasks] == [f"T{i}" for i in range(1, 7)]
        assert [t.depends_on for t in tasks] == REVIEW_TEMPLATE_DEPS
        assert [t.type for t in tasks] == [
            PlanNodeType.LLM, PlanNodeType.TASK, PlanNodeType.TASK,
            PlanNodeType.TASK, PlanNodeType.TOOL, PlanNodeType.TASK,
        ]

    def test_simple_single_node(self):
        from aios_core.orchestrator.planning.task_decomposer import TaskDecomposer

        goal = GoalAnalysis(intent="chat", complexity=GoalComplexity.SIMPLE,
                            source=PlanSource.RULE)
        tasks = TaskDecomposer().decompose(goal, FakeRequest("hi"))
        assert len(tasks) == 1 and tasks[0].id == "T1"

    def test_test_intent_rule_skeleton(self):
        from aios_core.orchestrator.planning.task_decomposer import TaskDecomposer

        goal = GoalAnalysis(intent="test", complexity=GoalComplexity.COMPLEX,
                            source=PlanSource.RULE)
        tasks = TaskDecomposer().decompose(goal, FakeRequest("test"))
        assert len(tasks) == 3  # R3-3: "test" has no template -> rule skeleton

    def test_open_empty(self):
        from aios_core.orchestrator.planning.task_decomposer import TaskDecomposer

        goal = GoalAnalysis(intent="chat", complexity=GoalComplexity.OPEN,
                            source=PlanSource.RULE)
        assert TaskDecomposer().decompose(goal, FakeRequest("open")) == []

    def test_register_template(self):
        from aios_core.orchestrator.planning.task_decomposer import TaskDecomposer
        from aios_core.orchestrator.planning.templates import StepSpec

        register_template("custom", TemplateSkeleton(intent="custom", steps=[
            StepSpec(id="T1", name="one", type=PlanNodeType.TASK)]))
        goal = GoalAnalysis(intent="custom", complexity=GoalComplexity.COMPLEX,
                            source=PlanSource.RULE)
        tasks = TaskDecomposer().decompose(goal, FakeRequest("custom"))
        assert len(tasks) == 1


# ---------------------------------------------------------------------------
# YC-4 — Dependency analyzer
# ---------------------------------------------------------------------------

class TestDependency:
    def test_topo_order(self):
        tasks = review_tasks()
        ordered, flagged = DependencyAnalyzer().analyze(tasks)
        assert not flagged
        order = [t.id for t in ordered]
        assert order.index("T1") < order.index("T2")
        assert order.index("T2") < order.index("T4")
        assert order[-1] == "T6"

    def test_self_dep_flagged(self):
        tasks = [TaskSpec(id="T1", name="a", type=PlanNodeType.TASK, depends_on=["T1"])]
        _, flagged = DependencyAnalyzer().analyze(tasks)
        assert flagged == {"T1"}

    def test_unknown_dep_flagged(self):
        tasks = [TaskSpec(id="T1", name="a", type=PlanNodeType.TASK, depends_on=["T9"])]
        _, flagged = DependencyAnalyzer().analyze(tasks)
        assert flagged == {"T1"}


# ---------------------------------------------------------------------------
# YC-5 — Capability resolver
# ---------------------------------------------------------------------------

class TestCapability:
    def test_clean_resolve(self):
        tasks = review_tasks()
        resolved, risks = CapabilityResolver().resolve(
            tasks, make_capabilities("code_analysis", "test_writing", "test_run", "reporting"))
        # No HIGH risks (no unknown capability); medium no-tools is expected
        # because the registry has no tools bound (TASK-014 wiring).
        assert risks.highest != "high"
        assert not any(item.kind == "unknown_capability" for item in risks.items)
        assert all(t.agent == "coder" for t in resolved)

    def test_unknown_capability_risk(self):
        tasks = [TaskSpec(id="T1", name="a", type=PlanNodeType.TASK,
                          capabilities=["unknown_cap"])]
        _, risks = CapabilityResolver().resolve(tasks, make_capabilities())
        assert risks.highest == "high"
        assert any(item.kind == "unknown_capability" for item in risks.items)

    def test_no_tools_risk(self):
        tasks = [TaskSpec(id="T1", name="a", type=PlanNodeType.TASK,
                          capabilities=["no_tools_cap"])]
        registry = make_capabilities("no_tools_cap")
        _, risks = CapabilityResolver().resolve(tasks, registry)
        assert any(item.kind == "capability_no_tools" for item in risks.items)


# ---------------------------------------------------------------------------
# YC-6 — Risk analyzer
# ---------------------------------------------------------------------------

class TestRisk:
    def test_review_items_empty(self):
        from aios_core.config import PlanningSettings

        goal = GoalAnalysis(intent="review", complexity=GoalComplexity.COMPLEX,
                            source=PlanSource.TEMPLATE)
        tasks = review_tasks()
        # fill agents like the resolver would
        resolved, _ = CapabilityResolver().resolve(tasks, make_capabilities(
            "code_analysis", "test_writing", "test_run", "reporting"))
        report = RiskAnalyzer().analyze(goal, resolved, PlanningSettings())
        assert report.items == []  # C3-01 exact

    def test_open_high(self):
        from aios_core.config import PlanningSettings

        goal = GoalAnalysis(intent="chat", complexity=GoalComplexity.OPEN,
                            source=PlanSource.RULE)
        report = RiskAnalyzer().analyze(goal, [], PlanningSettings())
        assert report.highest == "high"
        assert any(item.kind == "open_goal" for item in report.items)

    def test_many_nodes(self):
        from aios_core.config import PlanningSettings

        goal = GoalAnalysis(intent="coding", complexity=GoalComplexity.COMPLEX,
                            source=PlanSource.RULE)
        tasks = [TaskSpec(id=f"T{i}", name="n", type=PlanNodeType.TASK, agent="a")
                 for i in range(20)]
        report = RiskAnalyzer().analyze(goal, tasks, PlanningSettings(max_nodes=32))
        assert any(item.kind == "many_nodes" for item in report.items)


# ---------------------------------------------------------------------------
# YC-7 — Execution planner
# ---------------------------------------------------------------------------

class TestPlanner:
    def test_template_path(self):
        from aios_core.config import PlanningSettings

        goal = GoalAnalysis(intent="review", complexity=GoalComplexity.COMPLEX,
                            source=PlanSource.TEMPLATE)
        plan = ExecutionPlanner().build(review_tasks(), goal, FakeRequest("review"),
                                        None, PlanningSettings())
        assert len(plan.nodes) == 6
        assert plan.status is ExecutionPlanStatus.DRAFT
        assert plan.estimated_tokens == 2000 + 200 * 5
        assert "filesystem" in plan.required_permissions

    def test_workflow_path(self):
        from aios_core.config import PlanningSettings

        library = make_library()
        library.register(WorkflowDefinition(
            name="wf-1", version="1.0.0", description="d", nodes=[
                {"id": "N1", "type": "llm", "name": "first",
                 "capabilities": [], "depends_on": []},
                {"id": "N2", "type": "task", "name": "second",
                 "capabilities": [], "depends_on": ["N1"]},
            ], permissions=["filesystem"],
            retries=2, timeout_s=120.0))
        goal = GoalAnalysis(intent="chat", complexity=GoalComplexity.SIMPLE,
                            source=PlanSource.WORKFLOW, matched_workflow="wf-1")
        plan = ExecutionPlanner().build([], goal, FakeRequest("run"),
                                        library, PlanningSettings())
        assert len(plan.nodes) == 2
        assert plan.nodes[0].retries == 2  # fall-through C2-06
        assert plan.nodes[0].timeout_s == 120.0

    def test_max_nodes_guard(self):
        from aios_core.config import PlanningSettings

        goal = GoalAnalysis(intent="coding", complexity=GoalComplexity.COMPLEX,
                            source=PlanSource.RULE)
        tasks = [TaskSpec(id=f"T{i}", name="n", type=PlanNodeType.TASK)
                 for i in range(40)]
        with pytest.raises(PlanningError, match="too many nodes"):
            ExecutionPlanner().build(tasks, goal, FakeRequest("x"), None,
                                     PlanningSettings(max_nodes=32))


# ---------------------------------------------------------------------------
# YC-8 — Plan validator (INV-014)
# ---------------------------------------------------------------------------

def valid_plan() -> ExecutionPlan:
    return ExecutionPlan(
        id="plan:template:review",
        request_ref="review",
        nodes=[PlanNode(id="T1", type=PlanNodeType.LLM, name="a", agent="coder",
                        capabilities=["code_analysis"], depends_on=[])],
        estimated_cost=0.0, estimated_tokens=2000,
        required_permissions=["filesystem"],
        status=ExecutionPlanStatus.DRAFT, created_at="",
    )


def make_ctx(settings=None, capabilities=None, policy=None, resources=None) -> ValidationContext:
    from aios_core.config import PlanningSettings

    return ValidationContext(
        capabilities=capabilities or make_capabilities("code_analysis"),
        policy=policy, resources=resources,
        settings=settings or PlanningSettings())


class TestValidator:
    def test_valid_plan(self):
        report = PlanValidator().validate(valid_plan(), make_ctx())
        assert report.valid

    def test_contract_fatal(self):
        bad = ExecutionPlan.model_construct(
            id="x", request_ref="", nodes=[{"bogus": 1}], estimated_cost=0,
            estimated_tokens=0, required_permissions=[], required_resources={},
            status=ExecutionPlanStatus.DRAFT, created_at="")
        report = PlanValidator().validate(bad, make_ctx())
        assert any(issue.rule is ValidationRule.CONTRACT and issue.fatal
                   for issue in report.issues)

    def test_capability_fatal(self):
        plan = valid_plan()
        plan = plan.model_copy(update={"nodes": [
            n.model_copy(update={"capabilities": ["nope"]}) for n in plan.nodes]})
        report = PlanValidator().validate(plan, make_ctx())
        assert any(issue.rule is ValidationRule.CAPABILITY and issue.fatal
                   for issue in report.issues)

    def test_permission_fatal(self):
        plan = valid_plan().model_copy(update={"required_permissions": ["bogus_scope"]})
        report = PlanValidator().validate(plan, make_ctx())
        assert any(issue.rule is ValidationRule.PERMISSION and issue.fatal
                   for issue in report.issues)

    def test_policy_deny_fatal(self):
        from aios_core.kernel.events import EventBus
        from aios_core.kernel.services import Policy, PolicyService

        policy = Policy(deny_scopes=["filesystem"])
        service = PolicyService(EventBus(), policy)
        report = PlanValidator().validate(valid_plan(), make_ctx(policy=service))
        fatal = [i for i in report.issues if i.rule is ValidationRule.POLICY]
        assert fatal and fatal[0].fatal
        assert "denied" in fatal[0].message

    def test_policy_ask_non_fatal(self):
        from aios_core.kernel.events import EventBus
        from aios_core.kernel.services import Policy, PolicyService

        policy = Policy(allow_scopes=[], require_approval=True)
        service = PolicyService(EventBus(), policy)
        plan = valid_plan().model_copy(
            update={"required_permissions": [s.value for s in PermissionScope]})
        report = PlanValidator().validate(plan, make_ctx(policy=service))
        policy_issues = [i for i in report.issues if i.rule is ValidationRule.POLICY]
        assert policy_issues and not policy_issues[0].fatal
        assert "approval" in policy_issues[0].message

    def test_dependency_fatal(self):
        from aios_core.orchestrator.planning.templates import StepSpec, TemplateSkeleton

        register_template("depbad", TemplateSkeleton(intent="depbad", steps=[
            StepSpec(id="T1", name="a", type=PlanNodeType.TASK, depends_on=["T9"]),
        ]))
        engine = make_engine()
        with pytest.raises(PlanningError) as exc_info:
            engine.plan(FakeRequest("depbad task"))  # C1-03: build raises ValidationError -> gate
        assert any(i.rule is ValidationRule.DEPENDENCY and i.fatal
                   for i in exc_info.value.report.issues)

    def test_resource_fatal(self):
        from aios_core.config import ResourcesSettings

        report = PlanValidator().validate(valid_plan(), make_ctx(
            resources=ResourcesSettings(max_tokens=100)))
        assert any(issue.rule is ValidationRule.RESOURCE and issue.fatal
                   for issue in report.issues)

    def test_cycle_fatal(self):
        from aios_core.orchestrator.planning.templates import StepSpec, TemplateSkeleton

        register_template("cyclic", TemplateSkeleton(intent="cyclic", steps=[
            StepSpec(id="T1", name="a", type=PlanNodeType.TASK, depends_on=["T3"]),
            StepSpec(id="T2", name="b", type=PlanNodeType.TASK, depends_on=["T1"]),
            StepSpec(id="T3", name="c", type=PlanNodeType.TASK, depends_on=["T2"]),
        ]))
        engine = make_engine()
        with pytest.raises(PlanningError) as exc_info:
            engine.plan(FakeRequest("cyclic task"))
        assert any(i.rule is ValidationRule.CYCLE and i.fatal
                   for i in exc_info.value.report.issues)

    def test_timeout_fatal(self):
        plan = valid_plan().model_copy(update={"nodes": [
            n.model_copy(update={"timeout_s": 0.5}) for n in valid_plan().nodes]})
        report = PlanValidator().validate(plan, make_ctx())
        assert any(issue.rule is ValidationRule.TIMEOUT and issue.fatal
                   for issue in report.issues)

    def test_engine_cycle_raises(self):
        from aios_core.orchestrator.planning.templates import StepSpec, TemplateSkeleton

        register_template("cyclic", TemplateSkeleton(intent="cyclic", steps=[
            StepSpec(id="T1", name="a", type=PlanNodeType.TASK, depends_on=["T3"]),
            StepSpec(id="T2", name="b", type=PlanNodeType.TASK, depends_on=["T1"]),
            StepSpec(id="T3", name="c", type=PlanNodeType.TASK, depends_on=["T2"]),
        ]))
        engine = make_engine()
        with pytest.raises(PlanningError) as exc_info:
            engine.plan(FakeRequest("cyclic task"))
        assert any(i.rule is ValidationRule.CYCLE and i.fatal
                   for i in exc_info.value.report.issues)


# ---------------------------------------------------------------------------
# YC-9 — Engine offline-first ladder
# ---------------------------------------------------------------------------

class TestEngine:
    def test_rule_offline(self):
        engine = make_engine()
        result = engine.plan(FakeRequest("check status"))
        assert result.source is PlanSource.RULE
        assert result.llm_calls == 0
        assert result.plan.status is ExecutionPlanStatus.READY

    def test_template_offline(self):
        engine = make_engine()
        result = engine.plan(FakeRequest("Review module authentication"))
        assert result.source is PlanSource.TEMPLATE
        assert result.llm_calls == 0
        assert len(result.plan.nodes) == 6

    def test_llm_calls_counter(self):
        engine = make_engine()
        engine.plan(FakeRequest("check status"))
        assert engine.llm_calls == 0
        engine.reset_calls()
        assert engine.llm_calls == 0

    def test_deterministic(self):
        engine = make_engine()
        first = engine.plan(FakeRequest("Review module authentication"))
        second = engine.plan(FakeRequest("Review module authentication"))
        assert first.model_dump() == second.model_dump()

    def test_llm_path_with_stub_planner(self):
        from aios_core.orchestrator.planner import PlanResult

        class StubPlanner:
            def __init__(self):
                self.calls = 0

            def plan(self, text, model, library):
                self.calls += 1
                return PlanResult(intent="coding", workflow_names=[], llm_used=True)

        class FakeModel:
            def is_available(self):
                return True

        engine = make_engine(planner=StubPlanner(), model=FakeModel())
        result = engine.plan(FakeRequest("Hãy phân tích toàn bộ dự án và đề xuất kiến trúc"))
        assert result.source is PlanSource.LLM
        assert result.llm_calls == 1
        assert len(result.plan.nodes) == 3  # coding template

    def test_llm_error_increments_calls(self):
        from aios_core.orchestrator.planner import PlanResult

        class ErrorPlanner:
            def plan(self, text, model, library):
                return PlanResult(intent="chat", error=True,
                                  reasoning="model exploded", llm_used=True)

        engine = make_engine(planner=ErrorPlanner(), model=object())
        with pytest.raises(PlanningError, match="llm planning failed"):
            engine.plan(FakeRequest("Phân tích toàn bộ dự án và đề xuất kiến trúc"))
        assert engine.llm_calls == 1  # C2-08

    def test_planner_none_open_raises(self):
        engine = make_engine(planner=None, model=None)
        with pytest.raises(PlanningError, match="unavailable"):
            engine.plan(FakeRequest("Phân tích toàn bộ dự án và đề xuất kiến trúc mới"))

    def test_llm_medical_normalized(self):
        from aios_core.orchestrator.planner import PlanResult

        class StubPlanner:
            def plan(self, text, model, library):
                return PlanResult(intent="medical", workflow_names=[], llm_used=True)

        engine = make_engine(planner=StubPlanner(), model=object())
        result = engine.plan(FakeRequest("Phân tích triệu chứng bệnh nhân và đề xuất"))
        assert result.source is PlanSource.LLM
        assert result.plan.nodes[0].agent == "doctor"  # medical -> doctor (C2-05 v2)


# ---------------------------------------------------------------------------
# INV-014 behavioral
# ---------------------------------------------------------------------------

def test_inv014_never_returns_unvalidated():
    """Engine never returns an invalid plan (raises PlanningError instead)."""
    engine = make_engine()
    result = engine.plan(FakeRequest("check status"))
    assert result.validation.valid
    assert result.plan.status is ExecutionPlanStatus.READY


def test_inv014_validate_dag_helper():
    nodes = [
        PlanNode(id="A", type=PlanNodeType.TASK, name="a"),
        PlanNode(id="B", type=PlanNodeType.TASK, name="b", depends_on=["A"]),
    ]
    validate_dag(nodes)  # no raise
