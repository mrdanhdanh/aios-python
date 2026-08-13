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

    args = parser.parse_args(argv)

    if args.command == "run":
        if not args.simulate:
            parser.error("--simulate is required in v1 (real execution lands in M2)")
        return _run_simulate(args.workflow_file)
    if args.command == "doctor":
        return _doctor()
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
    return 1


def _doctor() -> int:
    # Runtime health via the DI container (no direct service construction).
    from ..kernel import RuntimeKernel
    from ..kernel.services import EventService

    kernel = RuntimeKernel.create()
    event_service = kernel.container.resolve(EventService)
    health = {
        "kernel": "ok",
        "bus_alive": kernel.bus is not None,
        "event_service": "registered" if event_service is not None else "missing",
        "audit_db_path": str(getattr(event_service, "_db_path", "") or ""),
    }
    print(json.dumps(health, indent=2))
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


if __name__ == "__main__":
    sys.exit(main())
