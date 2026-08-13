"""Wire registries for the API app (C1-03/C2-07/C2-08/C2-09)."""

from __future__ import annotations

from ..agents import AssistantRegistry, CoderAssistant, DoctorAssistant, GeneralAssistant, SystemDoctor
from ..capabilities import CapabilityRegistry
from ..catalog import SystemCatalog
from ..config import Settings
from ..kernel.runtime_kernel import RuntimeKernel
from ..models import ModelRegistry
from ..orchestrator.agent_selector import AgentSelector
from ..orchestrator.normalizer import Normalizer
from ..orchestrator.orchestrator import Orchestrator
from ..orchestrator.planner import Planner
from ..orchestrator.rule_engine import default_rules
from ..orchestrator.workflow_matcher import WorkflowMatcher
from ..prompts import PromptRegistry
from ..sandbox import SandboxPool
from ..skills import SkillManager
from ..tools import build_tool_registry
from ..workflow.library import WorkflowLibrary

CAP_DESCRIPTIONS = {
    "execute_code": "run python code",
    "manage_container": "docker containers",
    "call_api": "http calls",
    "mcp_call": "mcp servers",
    "run_shell": "shell commands",
    "git_ops": "git operations",
}


def build_registries(settings: Settings, kernel: RuntimeKernel, regs: dict) -> dict:
    """Fill missing registry keys. `regs` may contain injected fakes (tests)."""

    def _ensure(key: str, factory):
        if key not in regs or regs[key] is None:
            regs[key] = factory()
        return regs[key]

    # Core kernel services.
    from ..kernel.services import ArtifactService, EventService

    regs.setdefault("event_service", kernel.container.resolve(EventService))
    regs.setdefault("artifact_service", kernel.container.resolve(ArtifactService))

    # Orchestrator (C1-03): default offline-first pipeline with MockModel.
    def _build_orchestrator():
        library = WorkflowLibrary()
        registry = ModelRegistry()
        from ..models import MockModel

        registry.register("mock", MockModel(responses=["ok"], loop=True))
        model = registry.default()
        return Orchestrator(
            rule_engine=default_rules(),
            workflow_matcher=WorkflowMatcher(library),
            planner=Planner(),
            normalizer=Normalizer(library=library),
            agent_selector=AgentSelector(),
            model=model,
            library=library,
        )

    _ensure("orchestrator", _build_orchestrator)

    # Assistants + selector wiring (AC11 uses CoderAssistant via intent).
    def _build_assistants():
        reg = AssistantRegistry(selector=AgentSelector().select)
        reg.register(GeneralAssistant())
        reg.register(CoderAssistant())
        reg.register(DoctorAssistant())
        reg.register(SystemDoctor())
        return reg

    _ensure("assistants", _build_assistants)

    # Tools + capability binding (C2-07 catalog populate uses them).
    def _build_tools():
        tool_reg = build_tool_registry()
        cap_reg = CapabilityRegistry()
        for cap, desc in CAP_DESCRIPTIONS.items():
            cap_reg.register_capability(cap, desc)
        tool_reg.bind_capabilities(lambda cap, tid: cap_reg.bind_tool(cap, tid))
        return tool_reg

    tools_reg = _ensure("tools", _build_tools)
    regs.setdefault("capabilities", None)  # populated below
    if "capabilities" not in regs or regs["capabilities"] is None:
        cap_reg = CapabilityRegistry()
        for cap, desc in CAP_DESCRIPTIONS.items():
            cap_reg.register_capability(cap, desc)
        tools_reg.bind_capabilities(lambda cap, tid: cap_reg.bind_tool(cap, tid))
        regs["capabilities"] = cap_reg

    # Skills (C2-01: db_path from Settings.skills).
    def _build_skills():
        return SkillManager(db_path=settings.skills.db_path)

    _ensure("skills", _build_skills)

    # Goals (db_path from Settings.goals).
    def _build_goals():
        from ..orchestrator.goals import GoalManager

        return GoalManager(event_service=regs["event_service"], db_path=settings.goals.db_path)

    _ensure("goals", _build_goals)

    # Sandbox (C2-09).
    _ensure("sandbox", lambda: SandboxPool())

    # Prompts + models.
    _ensure("prompts", PromptRegistry)

    def _build_models():
        reg = ModelRegistry()
        from ..models import MockModel

        reg.register("mock", MockModel(responses=["ok"], loop=True))
        return reg

    _ensure("models", _build_models)

    # Catalog (C2-07: populate entries so production is not empty).
    def _build_catalog():
        catalog = SystemCatalog()
        for tool in tools_reg.list():
            catalog.index_entry(
                kind="tool", id=tool.id,
                metadata={"name": tool.name, "tool_type": tool.tool_type,
                          "capabilities": list(tool.capabilities)},
            )
        for skill in regs["skills"].list():
            catalog.index_entry(
                kind="skill", id=skill.id,
                metadata={"name": skill.name, "version": skill.version,
                          "state": skill.state.value},
            )
        for assistant in regs["assistants"].list():
            catalog.index_entry(
                kind="assistant", id=assistant.name,
                metadata={"intent": assistant.intent},
            )
        for model_name in regs["models"].list():
            catalog.index_entry(kind="model", id=model_name, metadata={})
        return catalog

    _ensure("catalog", _build_catalog)

    # Health registry.
    from ..healthcheck import HealthRegistry

    _ensure("health", HealthRegistry)

    # Conversation memory (C2-08).
    from ..memory import ConversationMemory

    def _build_conversations():
        return ConversationMemory(settings.memory.conversation_db_path)

    _ensure("conversations", _build_conversations)

    # Observability (TASK-021) — metrics/prompt-history/doctor/arch-health/evaluations.
    def _build_observability():
        from ..observability.arch_health import ArchitectureHealth
        from ..observability.doctor import HealthDoctor
        from ..observability.evaluation import EvaluationStore
        from ..observability.metrics import MetricsService
        from ..observability.prompt_history import PromptHistory

        db_path = settings.observability.db_path
        metrics = MetricsService(kernel.bus, f"{db_path}.metrics" if not db_path.endswith(".metrics") else db_path)
        from pathlib import Path

        base = Path(db_path)
        return {
            "metrics": metrics,
            "prompt_history": PromptHistory(base.with_name(base.name + ".prompts")),
            "doctor": HealthDoctor(
                health_registry=regs["health"],
                diagnostics=[
                    lambda: {"skills": len(regs["skills"].list())},
                    lambda: {"catalog_entries": regs["catalog"].count()},
                    lambda: {"prompts": len(regs["prompts"].list())},
                ],
                metrics_summary=metrics.summary,
            ),
            "arch_health": ArchitectureHealth(),
            "evaluations": EvaluationStore(kernel.bus, base.with_name(base.name + ".evals")),
        }

    _ensure("observability", _build_observability)

    # Orchestrator v2 (TASK-022) — advisor/supervisor/collector/goal reporter.
    # MUST build AFTER observability (R3-2): collector subscribes after
    # EvaluationStore so rows exist when evaluators run.
    def _build_orchestrator_v2():
        from ..orchestrator.advisor import ImprovementAdvisor
        from ..orchestrator.evaluation_collector import EvaluationCollector
        from ..orchestrator.goals.reporting import GoalReporter
        from ..orchestrator.goals.task_queue import QueueItemStatus, TaskQueue
        from ..orchestrator.supervisor import ExecutionSupervisor

        obs = regs["observability"]
        task_queue = TaskQueue(event_service=regs["event_service"], db_path=settings.goals.db_path)
        collector = EvaluationCollector(obs["evaluations"], evaluator=None)
        # Trigger: subscribe 3 terminal events → collect_workflow (P2-1 v2).
        from ..kernel.events import EventType

        def _on_terminal(event):
            if event.type in (
                EventType.WORKFLOW_COMPLETED,
                EventType.WORKFLOW_FAILED,
                EventType.WORKFLOW_CANCELLED,
            ):
                collector.collect_workflow(
                    str(event.payload.get("plan_id") or ""),
                    str(event.payload.get("execution_id") or ""),
                    {},
                )

        kernel.bus.subscribe(None, _on_terminal)
        return {
            "advisor": ImprovementAdvisor(obs["evaluations"], obs["metrics"], obs["prompt_history"]),
            "supervisor": ExecutionSupervisor(
                kernel.bus,
                task_queue_count=lambda: len(task_queue.list_items(QueueItemStatus.QUEUED)),
            ),
            "collector": collector,
            "goal_reporter": GoalReporter(regs["goals"]),
        }

    _ensure("orchestrator_v2", _build_orchestrator_v2)

    return regs
