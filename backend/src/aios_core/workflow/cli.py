"""Workflow CLI: `python -m aios_core.workflow.cli run <yaml> --simulate`."""

from __future__ import annotations

import argparse
import sys
import tempfile


def main(argv: list[str] | None = None) -> int:
    """Run a workflow in simulation mode (fake node runners).

    ``--simulate`` is REQUIRED in v1 (real execution lands in M2).
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
    args = parser.parse_args(argv)

    if args.command == "run":
        if not args.simulate:
            parser.error("--simulate is required in v1 (real execution lands in M2)")
        return _run_simulate(args.workflow_file)
    return 1


def _run_simulate(workflow_file: str) -> int:
    # Lazy imports (keeps `python -m` from double-initializing the package).
    from ..kernel import EventBus
    from ..kernel.services import (
        EventService,
        ExecutionService,
        PolicyService,
        ResourceService,
        StateService,
    )
    from .compiler import MockCompiler
    from .definition import WorkflowDefinition

    definition = WorkflowDefinition.from_yaml(workflow_file)
    plan = MockCompiler().compile(definition)

    with tempfile.TemporaryDirectory() as tmp:
        bus = EventBus()
        execution = ExecutionService(
            EventService(bus, f"{tmp}/audit.db"),
            PolicyService(bus),
            StateService(),
            ResourceService(),
        )
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
