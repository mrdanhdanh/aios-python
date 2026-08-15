"""Workflow CLI: `python -m aios_core.workflow.cli <command> ...`."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile


def main(argv: list[str] | None = None) -> int:
    """Entry point for workflow-related commands.

    Subcommands:
      run                 Run a workflow definition (v1: --simulate required)
      doctor              Print runtime health (services wired via DI container)
      catalog list        List indexed catalog entries (built directly)
      workflow validate   Stateless validation of a workflow YAML (engine-agnostic)
      contract validate   Stateless validation of a contract payload
      contract list/check Contract 1.0 matrix (M10-F2)
    """
    # UTF-8 output (✓/⚠/→) — console cp1252 không in được (M10-F2).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="aiagent")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run a workflow definition")
    run.add_argument("workflow_file", help="Path to workflow.yaml")
    run.add_argument(
        "--simulate",
        action="store_true",
        help="Run with fake node runners (required in v1)",
    )

    sub.add_parser("doctor", help="Print runtime health")

    sub.add_parser("metrics", help="Print observability metrics summary (M4-P8)")

    sub.add_parser("arch-health", help="Scan architecture violations (M4-P8)")

    sub.add_parser("advisor", help="Improvement suggestions from logs + evaluations (M4-P8)")

    sub.add_parser("supervisor", help="Execution supervisor snapshot (M4-P8)")

    sub.add_parser("slo", help="Reliability SLO report + release verdict (M10-F2)")

    stop = sub.add_parser("stop", help="Stop execution/goal (M10-F3, TASK-068)")
    stop_sub = stop.add_subparsers(dest="stop_command", required=True)
    stop_exec = stop_sub.add_parser("execution", help="Cancel an execution")
    stop_exec.add_argument("execution_id")
    stop_goal = stop_sub.add_parser("goal", help="Cascade cancel a goal")
    stop_goal.add_argument("goal_id")

    sub.add_parser("emergency-stop", help="EMERGENCY: block mọi việc mới (M10-F3, TASK-068)")

    sub.add_parser("status", help="Kill switch + system status (M10-F3, TASK-068)")

    sub.add_parser("security-check", help="Security baseline 1.0 (M10-F3, TASK-070)")

    sub.add_parser("health", help="Doctor first-class (M10-F4, TASK-071)")

    system = sub.add_parser("system", help="System commands (M10-F4, TASK-071)")
    system_sub = system.add_subparsers(dest="system_command", required=True)
    system_sub.add_parser("status", help="Version + services + emergency flag")

    goal = sub.add_parser("goal", help="Goal commands (M10-F4)")
    goal_sub = goal.add_subparsers(dest="goal_command", required=True)
    goal_sub.add_parser("list", help="List goals")

    execution = sub.add_parser("execution", help="Execution commands (M10-F4)")
    execution_sub = execution.add_subparsers(dest="execution_command", required=True)
    exec_list = execution_sub.add_parser("list", help="List recent executions")
    exec_list.add_argument("--limit", type=int, default=20)

    skill = sub.add_parser("skill", help="Skill commands (M10-F4)")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)
    skill_sub.add_parser("list", help="List skills")

    capability = sub.add_parser("capability", help="Capability commands (M10-F4)")
    capability_sub = capability.add_subparsers(dest="capability_command", required=True)
    capability_sub.add_parser("list", help="List capabilities")

    sub.add_parser("cost", help="Cost dashboard (M10-F4, TASK-075)")

    sub.add_parser("performance", help="Performance metrics (M10-F4, TASK-075)")

    serve = sub.add_parser("serve", help="Start the AIOS API server (M3-P5)")
    serve.add_argument("--host", default="127.0.0.1", help="Bind host")
    serve.add_argument("--port", type=int, default=8000, help="Bind port")

    catalog = sub.add_parser("catalog", help="System catalog commands")
    catalog_sub = catalog.add_subparsers(dest="catalog_command", required=True)
    catalog_sub.add_parser("list", help="List indexed catalog entries")

    workflow = sub.add_parser("workflow", help="Workflow commands")
    workflow_sub = workflow.add_subparsers(dest="workflow_command", required=True)
    w_validate = workflow_sub.add_parser("validate", help="Validate a workflow YAML")
    w_validate.add_argument("workflow_file", help="Path to workflow.yaml")

    contract = sub.add_parser("contract", help="Contract commands")
    contract_sub = contract.add_subparsers(dest="contract_command", required=True)
    c_validate = contract_sub.add_parser("validate", help="Validate a contract payload")
    c_validate.add_argument("contract_file", help="Path to contract JSON")
    contract_sub.add_parser("list", help="List the 10 frozen contracts (M10-F2)")
    contract_sub.add_parser("check", help="Contract Compatibility Matrix (M10-F2)")
    contract_sub.add_parser("check-full", help="Contract matrix + deprecated usage scan (M10-F2)")

    upgrade = sub.add_parser("upgrade", help="Upgrade a component via the upgrade pipeline (M4-P7)")
    upgrade.add_argument("kind", help="Component kind (v1: skill)")
    upgrade.add_argument("component_id", help="Component id")
    upgrade.add_argument("--version", required=True, help="Target version (semver)")
    upgrade.add_argument(
        "--dry-run",
        action="store_true",
        help="Run compatibility + dependency checks only (no changes)",
    )

    ecosystem = sub.add_parser("ecosystem", help="Ecosystem registry commands (M8-E4)")
    ecosystem_sub = ecosystem.add_subparsers(dest="ecosystem_command", required=True)
    eco_search = ecosystem_sub.add_parser("search", help="Search the ecosystem registry")
    eco_search.add_argument("query", nargs="?", default="", help="Keyword (id/name/description/publisher)")
    eco_search.add_argument("--kind", default=None, help="Filter by entry kind (agent/tool/plugin/...)")

    plugin = sub.add_parser("plugin", help="Plugin commands (M8-E5)")
    plugin_sub = plugin.add_subparsers(dest="plugin_command", required=True)
    plugin_create = plugin_sub.add_parser("create", help="Scaffold a new plugin/agent/capability/tool/workflow")
    plugin_create.add_argument("kind", help="plugin|agent|capability|tool|workflow")
    plugin_create.add_argument("name", help="Component name ([a-z][a-z0-9_]*)")
    plugin_create.add_argument("--dir", default=".", help="Output directory (default: current)")

    marketplace = sub.add_parser("marketplace", help="Marketplace commands (M8-E6)")
    marketplace_sub = marketplace.add_subparsers(dest="marketplace_command", required=True)
    mp_publish = marketplace_sub.add_parser("publish", help="Publish a manifest JSON file")
    mp_publish.add_argument("manifest_file", help="Path to manifest JSON")
    mp_publish.add_argument("--publisher", required=True, help="Publisher id")
    mp_publish.add_argument("--key", required=True, help="Signing key (>=64 chars)")

    args = parser.parse_args(argv)

    if args.command == "run":
        if not args.simulate:
            parser.error("--simulate is required in v1 (real execution lands in M2)")
        return _run_simulate(args.workflow_file)
    if args.command == "doctor":
        return _doctor()
    if args.command == "metrics":
        return _metrics()
    if args.command == "arch-health":
        return _arch_health()
    if args.command == "advisor":
        return _advisor()
    if args.command == "supervisor":
        return _supervisor()
    if args.command == "slo":
        return _slo()
    if args.command == "stop" and args.stop_command == "execution":
        return _stop_execution(args.execution_id)
    if args.command == "stop" and args.stop_command == "goal":
        return _stop_goal(args.goal_id)
    if args.command == "emergency-stop":
        return _emergency_stop()
    if args.command == "status":
        return _status()
    if args.command == "security-check":
        return _security_check()
    if args.command == "health":
        return _doctor_first_class()
    if args.command == "system" and args.system_command == "status":
        return _system_status()
    if args.command == "goal" and args.goal_command == "list":
        return _goal_list()
    if args.command == "execution" and args.execution_command == "list":
        return _execution_list(args.limit)
    if args.command == "skill" and args.skill_command == "list":
        return _skill_list()
    if args.command == "capability" and args.capability_command == "list":
        return _capability_list()
    if args.command == "cost":
        return _cost()
    if args.command == "performance":
        return _performance()
    if args.command == "serve":
        return _serve(args.host, args.port)
    if args.command == "catalog" and args.catalog_command == "list":
        return _catalog_list()
    if args.command == "workflow" and args.workflow_command == "validate":
        return _workflow_validate(args.workflow_file)
    if args.command == "contract" and args.contract_command == "validate":
        return _contract_validate(args.contract_file)
    if args.command == "contract" and args.contract_command == "list":
        return _contract_list()
    if args.command == "contract" and args.contract_command in ("check", "check-full"):
        return _contract_check(scan=args.contract_command == "check-full")
    if args.command == "upgrade":
        return _upgrade(args.kind, args.component_id, args.version, args.dry_run)
    if args.command == "ecosystem" and args.ecosystem_command == "search":
        return _ecosystem_search(args.query, args.kind)
    if args.command == "plugin" and args.plugin_command == "create":
        return _plugin_create(args.kind, args.name, args.dir)
    if args.command == "marketplace" and args.marketplace_command == "publish":
        return _marketplace_publish(args.manifest_file, args.publisher, args.key)
    return 1


def _doctor() -> int:
    # Runtime health via the DI container + observability HealthDoctor (M4-P8).
    from ..config import load_settings
    from ..kernel import RuntimeKernel
    from ..kernel.services import EventService
    from ..observability.doctor import HealthDoctor

    kernel = RuntimeKernel.create()
    settings = load_settings()
    event_service = kernel.container.resolve(EventService)
    from ..healthcheck import HealthRegistry
    from ..skills import SkillManager
    from ..catalog import SystemCatalog

    registry = HealthRegistry()
    doctor = HealthDoctor(
        health_registry=registry,
        diagnostics=[
            lambda: {"kernel": "ok", "bus_alive": kernel.bus is not None,
                     "event_service": "registered" if event_service is not None else "missing"},
            lambda: {"skills": len(SkillManager(db_path=str(settings.skills.db_path)).list())},
            lambda: {"catalog_entries": SystemCatalog().count()},
        ],
    )
    report = doctor.report()
    out = {
        "status": report.status.value,
        "kernel": "ok",
        "checks": [
            {"name": c.name, "status": c.status.value, "message": c.message}
            for c in report.checks
        ],
        "diagnostics": report.diagnostics,
    }
    print(json.dumps(out, indent=2))
    return 0


def _metrics() -> int:
    # Observability metrics summary (M4-P8). Empty DB → zeros, no error.
    from ..config import load_settings
    from ..kernel import RuntimeKernel
    from ..observability.metrics import MetricsService

    kernel = RuntimeKernel.create()
    settings = load_settings()
    # [bypass R2-1 TASK-022] suffix convention khớp wiring (db_path + ".metrics")
    service = MetricsService(kernel.bus, settings.observability.db_path + ".metrics")
    print(json.dumps(service.summary(), indent=2))
    service.close()
    return 0


def _arch_health() -> int:
    # Architecture violation scan (M4-P8) — pure AST, no runtime import.
    from ..observability.arch_health import ArchitectureHealth

    report = ArchitectureHealth().scan()
    out = {
        "healthy": report.healthy,
        "violations": [
            {"kind": v.kind, "module": v.module, "message": v.message}
            for v in report.violations
        ],
    }
    print(json.dumps(out, indent=2))
    return 0


def _advisor() -> int:
    # Improvement suggestions (M4-P8) — db suffix convention khớp wiring.
    from ..config import load_settings
    from ..kernel import RuntimeKernel
    from ..observability.evaluation import EvaluationStore
    from ..observability.metrics import MetricsService
    from ..observability.prompt_history import PromptHistory
    from ..orchestrator.advisor import ImprovementAdvisor

    kernel = RuntimeKernel.create()
    settings = load_settings()
    db = settings.observability.db_path
    advisor = ImprovementAdvisor(
        EvaluationStore(kernel.bus, db + ".evals"),
        MetricsService(kernel.bus, db + ".metrics"),
        PromptHistory(db + ".prompts"),
    )
    suggestions = advisor.suggest()
    print(
        json.dumps(
            {
                "count": len(suggestions),
                "suggestions": [
                    {"kind": s.kind, "action": s.action, "target": s.target,
                     "reason": s.reason, "evidence": s.evidence}
                    for s in suggestions
                ],
            },
            indent=2,
        )
    )
    return 0


def _supervisor() -> int:
    # Execution supervisor snapshot (M4-P8).
    from ..kernel import RuntimeKernel
    from ..orchestrator.supervisor import ExecutionSupervisor

    kernel = RuntimeKernel.create()
    supervisor = ExecutionSupervisor(kernel.bus)
    snap = supervisor.snapshot()
    out = {
        "running": list(snap.running),
        "recent_completed": snap.recent_completed,
        "recent_failed": snap.recent_failed,
        "queue_size": snap.queue_size,
        "stuck": list(snap.stuck),
    }
    print(json.dumps(out, indent=2))
    supervisor.close()
    return 0


def _serve(host: str, port: int) -> int:
    # Lazy import (C3-04): avoid pulling fastapi for other subcommands.
    from ..api.serve import run

    run(host=host, port=port)
    return 0


def _slo() -> int:
    """Reliability SLO report + release verdict (M10-F2, TASK-069)."""
    from ..kernel import RuntimeKernel
    from ..observability.slo import SloEngine, format_slo_report

    kernel = RuntimeKernel.create()
    engine = SloEngine()
    metrics = engine.metrics_from_runtime(kernel)
    report = engine.check(metrics)
    print(format_slo_report(report))
    return 0 if report.release_ready else 1


def _kill_switch() -> "object":
    from ..kernel import RuntimeKernel
    from ..kernel.kill_switch import KillSwitch

    kernel = RuntimeKernel.create()
    return kernel.container.resolve(KillSwitch)


def _stop_execution(execution_id: str) -> int:
    """Cancel một execution (M10-F3)."""
    try:
        _kill_switch().stop_execution(execution_id)
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}")
        return 1
    print(f"execution {execution_id} cancelled")
    return 0


def _stop_goal(goal_id: str) -> int:
    """Cascade cancel một goal (M10-F3)."""
    try:
        goal = _kill_switch().stop_goal(goal_id)
        print(f"goal {goal_id} cancelled (status={getattr(goal, 'status', '?')})")
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}")
        return 1
    return 0


def _emergency_stop() -> int:
    """EMERGENCY STOP (M10-F3): block mọi việc mới."""
    state = _kill_switch().emergency_stop()
    print(json.dumps(state.snapshot(), indent=2))
    print("EMERGENCY STOP ACTIVE — release bằng: aiagent status (rồi gọi release qua API)")
    return 0


def _status() -> int:
    """Kill switch status + system status (M10-F3)."""
    switch = _kill_switch()
    snap = switch.state.snapshot()
    out = {
        "emergency": snap["emergency"],
        "blocked_executions": snap["blocked_executions"],
        "blocked_tool_calls": snap["blocked_tool_calls"],
        "cancelled_approvals": snap["cancelled_approvals"],
        "reversible": snap["reversible"],
    }
    print(json.dumps(out, indent=2))
    return 0


def _security_check() -> int:
    """Security baseline 1.0 — 11 items (M10-F3, TASK-070)."""
    from ..security import SecurityChecker, format_security_report

    report = SecurityChecker().run()
    print(format_security_report(report))
    return 0 if not report.blocking else 1


def _doctor_first_class() -> int:
    """Doctor first-class — 18 hạng mục + Health score (M10-F4, TASK-071)."""
    from ..cli.doctor import DoctorFirstClass, format_doctor_report

    report = DoctorFirstClass().run()
    print(format_doctor_report(report))
    return 0


def _system_status() -> int:
    """System status (M10-F4, TASK-071)."""
    from ..cli.system import system_status

    print(json.dumps(system_status(), indent=2))
    return 0


def _goal_list() -> int:
    """List goals (M10-F4, TASK-071)."""
    from ..config import load_settings
    from ..orchestrator.goals import GoalManager

    settings = load_settings()
    manager = GoalManager(
        __import__("aios_core.kernel.services", fromlist=["EventService"]).EventService(
            __import__("aios_core.kernel.events", fromlist=["EventBus"]).EventBus(),
            settings.audit.db_path,
        ),
        settings.goals.db_path,
    )
    goals = manager.list_goals(limit=100)
    if not goals:
        print("<empty>")
        return 0
    for g in goals:
        print(f"{g.id} | {g.title} | {g.status.value} | progress={g.progress:.0%}")
    return 0


def _execution_list(limit: int) -> int:
    """List recent executions (M10-F4, TASK-071) từ MetricsService."""
    from ..config import load_settings
    from ..observability.metrics import MetricsService

    settings = load_settings()
    svc = MetricsService(
        __import__("aios_core.kernel.events", fromlist=["EventBus"]).EventBus(),
        settings.observability.metrics_db_path
        if hasattr(settings.observability, "metrics_db_path") else "aios/data/metrics.db",
    )
    rows = svc.recent(limit=limit)
    if not rows:
        print("<empty>")
        return 0
    for r in rows:
        print(f"{r['execution_id'] or '-'} | {r['name'] or '-'} | "
              f"{r['category']} | {r['duration_ms']:.0f}ms" if r.get("duration_ms") else
              f"{r['execution_id'] or '-'} | {r['name'] or '-'} | {r['category']}")
    return 0


def _skill_list() -> int:
    """List skills (M10-F4, TASK-071)."""
    from ..config import load_settings
    from ..skills import SkillManager

    settings = load_settings()
    manager = SkillManager(db_path=str(settings.skills.db_path))
    skills = manager.list()
    if not skills:
        print("<empty>")
        return 0
    for s in skills:
        print(f"{getattr(s, 'id', s)} | {getattr(s, 'state', '?')}")
    return 0


def _capability_list() -> int:
    """List capabilities (M10-F4, TASK-071)."""
    from ..capabilities import CapabilityRegistry

    registry = CapabilityRegistry()
    caps = registry.list()
    if not caps:
        print("<empty>")
        return 0
    for c in caps:
        print(f"{c.name}")
    return 0


def _cost() -> int:
    """Cost dashboard — 5 chiều (M10-F4, TASK-075)."""
    from ..config import load_settings
    from ..kernel import RuntimeKernel
    from ..observability.metrics import MetricsService
    from ..observability.performance import CostAggregator, CostEstimator

    settings = load_settings()
    kernel = RuntimeKernel.create()
    registry = kernel.container.resolve(__import__(
        "aios_core.models", fromlist=["ModelRegistry"]
    ).ModelRegistry)

    def capabilities(model_id: str):
        try:
            return registry.capability(model_id)
        except Exception:  # noqa: BLE001
            return None

    metrics_svc = MetricsService(kernel.bus, settings.observability.metrics_db_path
                                 if hasattr(settings.observability, "metrics_db_path")
                                 else "aios/data/metrics.db")
    outcome = metrics_svc.counts_by_outcome("workflow")
    aggregator = CostAggregator(
        CostEstimator(capabilities=capabilities),
        workflow_success={"*": (outcome["ok"], outcome["ok"] + outcome["failed"])},
    )
    dash = aggregator.build()
    print(json.dumps({
        "cost_per_workflow": dash.cost_per_workflow,
        "cost_per_agent": dash.cost_per_agent,
        "cost_per_tool": dash.cost_per_tool,
        "cost_per_goal": dash.cost_per_goal,
        "cost_per_success": dash.cost_per_success,
        "total_cost": dash.total_cost,
    }, indent=2))
    return 0


def _performance() -> int:
    """Performance metrics (M10-F4, TASK-075)."""
    from ..config import load_settings
    from ..kernel import RuntimeKernel
    from ..observability.metrics import MetricsService
    from ..observability.performance import PerformanceMetrics

    settings = load_settings()
    kernel = RuntimeKernel.create()
    metrics_svc = MetricsService(kernel.bus, settings.observability.metrics_db_path
                                 if hasattr(settings.observability, "metrics_db_path")
                                 else "aios/data/metrics.db")
    snap = PerformanceMetrics(metrics_svc, settings.artifacts.dir).snapshot()
    print(json.dumps({
        "avg_workflow_latency_ms": snap.avg_workflow_latency_ms,
        "avg_tool_latency_ms": snap.avg_tool_latency_ms,
        "throughput_per_minute": snap.throughput_per_minute,
        "max_concurrency": snap.max_concurrency,
        "storage_bytes": snap.storage_bytes,
        "workflow_count": snap.workflow_count,
        "tool_count": snap.tool_count,
    }, indent=2))
    return 0


def _catalog_list() -> int:
    # Catalog is not registered in RuntimeKernel; build it directly.
    from ..catalog import SystemCatalog

    catalog = SystemCatalog()
    if catalog.count() == 0:
        print("<empty> — no indexed entries")
        return 0
    for entry in catalog.search(""):
        print(f"{entry.kind}/{entry.id}: {json.dumps(entry.metadata, ensure_ascii=False)}")
    return 0


def _workflow_validate(workflow_file: str) -> int:
    # Stateless, engine-agnostic validation (no kernel needed).
    from .compiler import MockCompiler
    from .definition import WorkflowDefinition

    try:
        definition = WorkflowDefinition.from_yaml(workflow_file)
        MockCompiler().compile(definition)  # raises on DAG/structural errors
    except Exception as exc:  # noqa: BLE001
        print(f"INVALID: {exc}")
        return 1
    print(f"VALID: {definition.name} v{definition.version} ({len(definition.nodes)} nodes)")
    return 0


def _contract_validate(contract_file: str) -> int:
    # Stateless contract payload validation (no kernel needed).
    from ..contracts import ContractMetadata

    try:
        ContractMetadata.model_validate_json(_read_text(contract_file))
    except Exception as exc:  # noqa: BLE001
        print(f"INVALID: {exc}")
        return 1
    print("VALID contract payload")
    return 0


def _contract_list() -> int:
    """List 10 frozen contracts (M10-F2)."""
    from ..contracts.catalog import ContractCatalog

    catalog = ContractCatalog()
    print(f"{'id'.ljust(12)}| {'version'.ljust(10)}| lifecycle")
    print("-" * 34)
    for c in sorted(catalog.all(), key=lambda x: x.id):
        print(f"{c.id.ljust(12)}| {c.version.ljust(10)}| {c.lifecycle.value}")
    return 0


def _contract_check(scan: bool = False) -> int:
    """Contract Compatibility Matrix (M10-F2).

    `scan=True` (`contract check-full`): thêm deprecated usage scan trên
    các contract mà runtime đang dùng (mặc định quét catalog đầy đủ).
    """
    from ..contracts.catalog import ContractCatalog
    from ..contracts.check import ContractChecker, format_matrix

    catalog = ContractCatalog()
    checker = ContractChecker(catalog)
    # check-full: quét usage của MỌI contract (phát hiện deprecated usage).
    used = catalog.ids() if scan else None
    report = checker.check_all(used=used)
    print(format_matrix(report, catalog))
    return 0 if not report.blocking else 1


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _upgrade(kind: str, component_id: str, version: str, dry_run: bool) -> int:
    """Upgrade pipeline CLI — v1 wires only the skill kind (TASK-020)."""
    # Lazy imports: avoid pulling upgrade/skills for other subcommands.
    from pathlib import Path

    from ..config import load_settings
    from ..skills import SkillManager
    from ..upgrade import (
        BackupStore,
        Dependency,
        DependencyResolver,
        SkillMigrator,
        UpgradePipeline,
    )

    if kind != "skill":
        print(f"not wired: kind '{kind}' is not supported in v1 (only 'skill')")
        return 1

    settings = load_settings()
    skill_manager = SkillManager(db_path=str(settings.skills.db_path))
    skill = skill_manager.get(component_id)
    if skill is None:
        print(f"component not found: {component_id}")
        return 1

    def parse_deps(manifest: dict) -> tuple:
        deps: list[Dependency] = []
        for dep in manifest.get("dependencies") or []:
            # "id" hoặc "id@>=1.2.3" → pin version (R2-3)
            if "@" not in dep:
                continue
            name, _, constraint = dep.partition("@")
            version = constraint.lstrip("<>=").strip()
            if name and version:
                deps.append(Dependency(name=name, version=version))
        return tuple(deps)

    def lookup(kind_: str, dep_name: str):
        found = skill_manager.get(dep_name)
        if found is None:
            return None
        return type(skill)(
            **{
                **found.model_dump(),
                "dependencies": parse_deps(found.manifest),
            }
        )

    migrator = SkillMigrator(skill_manager)
    pipeline = UpgradePipeline(
        migrator=migrator,
        backup_store=BackupStore(Path(settings.skills.db_path).parent / "upgrade.db"),
        resolver=DependencyResolver(lookup),
    )
    try:
        result = pipeline.run(kind, component_id, version, dry_run=dry_run)
    except ValueError as exc:
        print(f"invalid version: {exc}")
        return 1

    print(f"status: {result.status}")
    if result.reason:
        print(f"reason: {result.reason}")
    if result.plan:
        print("plan: " + " -> ".join(f"{s.component_id}@{s.version}" for s in result.plan))
    if result.backup_id is not None:
        print(f"backup_id: {result.backup_id}")
    if result.status == "failed":
        print(f"failed at step: {result.step}")
        return 1
    if result.status == "skipped":
        return 0
    return 0


def _run_simulate(workflow_file: str) -> int:
    # Lazy imports (keeps `python -m` from double-initializing the package).
    from ..config import AuditSettings, Settings
    from ..kernel import RuntimeKernel
    from ..kernel.services import ExecutionService
    from .compiler import MockCompiler
    from .definition import WorkflowDefinition

    definition = WorkflowDefinition.from_yaml(workflow_file)
    plan = MockCompiler().compile(definition)

    with tempfile.TemporaryDirectory() as tmp:
        # DI container resolves services; audit DB stays isolated in temp dir.
        settings = Settings(audit=AuditSettings(db_path=f"{tmp}/audit.db"))
        kernel = RuntimeKernel.create(settings)
        execution = kernel.container.resolve(ExecutionService)
        runner = {
            node.id: (lambda node, results: f"simulated:{node.id}")
            for node in plan.nodes
        }
        result = execution.execute(plan, runner)

    print(f"workflow: {definition.name} v{definition.version}")
    print(f"status: {result.status.value}")
    if result.reason:
        print(f"reason: {result.reason}")
    for node_id, node_result in result.node_results.items():
        print(f"  node {node_id}: {node_result}")
    return 0 if result.status.value == "completed" else 1


def _ecosystem_search(query: str, kind: str | None) -> int:
    # Ecosystem registry search (M8-E4). DB path convention khớp config.
    from ..config import load_settings
    from ..ecosystem import EcosystemRegistry

    settings = load_settings()
    registry = EcosystemRegistry(settings.ecosystem.db_path)
    hits = registry.search(query, kind=kind)
    out = [
        {"kind": e.kind.value, "id": e.id, "version": e.version,
         "name": e.name, "description": e.description}
        for e in hits
    ]
    print(json.dumps({"count": len(out), "results": out}, indent=2))
    return 0


def _plugin_create(kind: str, name: str, out_dir: str) -> int:
    # Developer Kit scaffold (M8-E5).
    from ..ecosystem import DevKit

    created = DevKit().create_scaffold(kind, name, out_dir)
    print(json.dumps({"created": created}, indent=2))
    return 0


def _marketplace_publish(manifest_file: str, publisher_id: str, key: str) -> int:
    # Marketplace publish (M8-E6) — requires manifest JSON file.
    from ..config import load_settings
    from ..ecosystem import MarketplaceRegistry, Publisher

    with open(manifest_file, encoding="utf-8") as fh:
        manifest = json.load(fh)
    settings = load_settings()
    registry = MarketplaceRegistry(settings.ecosystem.db_path)
    registry.register_publisher(Publisher(id=publisher_id, name=publisher_id), key)
    record = registry.publish(publisher_id, key, manifest)
    print(json.dumps({"publisher": record.publisher_id, "name": record.name,
                      "version": record.version, "signature": record.signature[:16] + "..."}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
