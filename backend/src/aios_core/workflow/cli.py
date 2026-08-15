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
    """
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
    if args.command == "serve":
        return _serve(args.host, args.port)
    if args.command == "catalog" and args.catalog_command == "list":
        return _catalog_list()
    if args.command == "workflow" and args.workflow_command == "validate":
        return _workflow_validate(args.workflow_file)
    if args.command == "contract" and args.contract_command == "validate":
        return _contract_validate(args.contract_file)
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
