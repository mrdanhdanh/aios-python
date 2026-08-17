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

    skill = sub.add_parser("skill", help="Skill commands (M10-F4 + M11-P4a R5)")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)
    skill_sub.add_parser("list", help="List skills")
    skill_distill = skill_sub.add_parser("distill", help="Distill skill from repo URL (M11-P4a, R5)")
    skill_distill.add_argument("url", help="Skill repo URL (github)")
    skill_distill.add_argument("--out", default="distilled", help="Output directory")

    deploy = sub.add_parser("deploy", help="Deploy commands (M11-P4b, R7)")
    deploy.add_argument("--static", metavar="DIR", help="Static dir to deploy")
    deploy.add_argument("--apply", action="store_true", help="Apply (write marker) — default dry-run")

    capability = sub.add_parser("capability", help="Capability commands (M10-F4)")
    capability_sub = capability.add_subparsers(dest="capability_command", required=True)
    capability_sub.add_parser("list", help="List capabilities")

    reference = sub.add_parser("reference", help="Reference-Asset commands (M11-P3d, R12)")
    reference_sub = reference.add_subparsers(dest="reference_command", required=True)
    ref_describe = reference_sub.add_parser("describe", help="Describe a reference image (mock vision)")
    ref_describe.add_argument("image", help="Path to reference image")

    sub.add_parser("cost", help="Cost dashboard (M10-F4, TASK-075)")

    sub.add_parser("performance", help="Performance metrics (M10-F4, TASK-075)")

    migrate = sub.add_parser("migrate", help="Migration 1.0 (M10-F5, TASK-074) + 1.0→1.1 (M12 C2)")
    migrate.add_argument("kind", help="config|workflow|plugin|contract (1.0→1.1)")
    migrate.add_argument("from_version", help="Version gốc (semver)")
    migrate.add_argument("to_version", help="Version đích (semver)")
    migrate.add_argument("--dry-run", action="store_true", help="Không thay đổi gì")
    migrate.add_argument("--apply", action="store_true", help="Thực hiện migration")
    migrate.add_argument("--input", default=None,
                         help="File input JSON (nhánh 1.0→1.1; default: stub)")
    migrate.add_argument("--journal", default="aios/data/migrations.db",
                         help="Migration journal DB path (test isolation)")

    sub.add_parser("conformance", help="AIOS conformance — 11 areas + 7 gates (M10-F5 + M11 INV-035 + M12 compatibility)")

    sub.add_parser("verify-state", help="INV-035 verification state model + fail-closed gate (M11-P0)")

    replay = sub.add_parser("render-replay", help="Pixel-stable replay (M11-P1, TASK-079)")
    replay.add_argument("--seed", type=int, default=42, help="PRNG seed (default 42)")
    replay.add_argument("--frames", type=int, default=60, help="Số frame replay (default 60)")
    replay.add_argument("--width", type=int, default=64)
    replay.add_argument("--height", type=int, default=64)
    replay.add_argument("--freeze", choices=["none", "fixed", "paused"], default="none")
    replay.add_argument("--show-hashes", action="store_true", help="In hash từng frame")

    probe = sub.add_parser("visual-probe", help="Visual regression probe (M11-P2, TASK-080)")
    probe.add_argument("--dump-ref", metavar="FILE", help="Ghi mock evidence ref vào JSON file")
    probe.add_argument("--dump-current", metavar="FILE", help="Ghi mock evidence current vào JSON file")
    probe.add_argument("--ref", metavar="FILE", help="Đọc evidence ref từ JSON")
    probe.add_argument("--current", metavar="FILE", help="Đọc evidence current từ JSON")
    probe.add_argument("--threshold", type=int, default=30, help="Pixel threshold (default 30)")
    probe.add_argument("--missing-ref", action="store_true", help="Mô phỏng thiếu ref (MISSING_EVIDENCE)")

    asset = sub.add_parser("asset", help="Asset capability commands (M11-P3, TASK-081)")
    asset_sub = asset.add_subparsers(dest="asset_command", required=True)
    asset_sub.add_parser("list", help="List asset capabilities")
    discover = asset_sub.add_parser("discover", help="Discover capabilities theo kind")
    discover.add_argument("kind", choices=["sprite", "tileset", "map", "audio",
                                            "animation", "ui_asset"])
    match = asset_sub.add_parser("match", help="Match request → capabilities (R11)")
    match.add_argument("request", help="Vd: \"generate sprite\"")
    produce = asset_sub.add_parser("produce", help="Produce asset qua pipeline (R9)")
    produce.add_argument("capability_id")
    produce.add_argument("--kind", required=True, choices=["sprite", "tileset", "map",
                                                           "audio", "animation", "ui_asset"])
    produce.add_argument("--name", default="asset")
    produce.add_argument("--seed", type=int, default=0)
    produce.add_argument("--params-json", default="{}", help="JSON params")

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

    compat = sub.add_parser("compat", help="Compatibility Matrix (M12-P0 C1, TASK-084)")
    compat_sub = compat.add_subparsers(dest="compat_command", required=True)
    compat_sub.add_parser("list", help="List compatibility matrix entries")
    compat_check = compat_sub.add_parser("check", help="Check a component against the matrix")
    compat_check.add_argument("kind", choices=["plugin", "contract", "workflow",
                                               "skill", "sdk"])
    compat_check.add_argument("id", help="Component id (không prefix loại)")
    compat_check.add_argument("version", help="Component version (semver)")
    compat_check.add_argument("--aios-version", default=None,
                              help="AIOS version to check against (default 1.1.0)")
    compat_sub.add_parser("verify", help="Backward compatibility suite cũ→mới trên 1.1 (M12-P2 C3, TASK-086)")

    harness = sub.add_parser("harness", help="Harness commands (M13-P0, TASK-089)")
    harness_sub = harness.add_subparsers(dest="harness_command", required=True)
    h_behavioral = harness_sub.add_parser(
        "behavioral",
        help="Behavioral conformance — N lần + repeat + fault + evidence + gate (M13-P0)",
    )
    h_behavioral.add_argument("--profile", choices=["quick", "standard", "stress", "soak"],
                              default="quick", help="Iterations profile (default quick)")
    h_behavioral.add_argument("--scenario-file", required=True,
                              help="Path to scenario YAML/JSON")
    h_behavioral.add_argument("--iterations", type=int, default=None,
                              help="Override profile iterations (thắng soak)")
    h_behavioral.add_argument("--duration", type=float, default=0.0,
                              help="Soak duration (seconds)")
    h_behavioral.add_argument("--faults", default=None,
                              help="JSON list[Fault] — áp mọi iteration")
    h_behavioral.add_argument("--fault-iterations", default=None,
                              help="JSON list[int] — chỉ iteration có fault (1-based)")
    h_behavioral.add_argument("--repeat-samples", type=int, default=3,
                              help="Số iteration đầu chạy double-run (default 3)")
    h_behavioral.add_argument("--baseline", default=None,
                              help="JSON Baseline file (chỉ expose — gate-as-blocker thuộc M14)")
    h_behavioral.add_argument("--save-baseline", default=None,
                              help="Ghi Baseline JSON từ lần chạy này")
    h_behavioral.add_argument("--no-strict", action="store_true",
                              help="Không raise khi FAIL/ERROR (exit vẫn 1)")
    h_coverage = harness_sub.add_parser(
        "coverage",
        help="Harness Coverage model 9 chiều + negative-path + readiness (M13-P1)",
    )
    h_coverage.add_argument("--min-overall", type=float, default=0.8,
                            help="Overall ngưỡng readiness (0,1])")
    h_coverage.add_argument("--min-replay", type=float, default=0.75,
                            help="Replay ngưỡng — v1 mặc định NOT_READY (cần TASK-091)")
    h_coverage.add_argument("--production-tests", action="store_true",
                            help="V1 luôn NOT_READY khi bật (chưa có nguồn evidence — M13.1/M16)")
    h_coverage.add_argument("--no-strict", action="store_true",
                            help="Không raise khi NOT_READY (exit vẫn 1)")
    h_meta = harness_sub.add_parser(
        "meta",
        help="Meta-Harness — verify the verifier (adversarial fail-closed, M13-P2)",
    )
    h_meta.add_argument("--no-strict", action="store_true",
                        help="Không raise khi Meta FAIL (exit vẫn 1)")
    h_release = harness_sub.add_parser(
        "release",
        help="Release gate — System Readiness + Harness Trust (M13-P3)",
    )
    h_release.add_argument("--no-strict", action="store_true",
                           help="Không raise khi BLOCKED (exit vẫn 1)")

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
    if args.command == "skill" and args.skill_command == "distill":
        return _skill_distill(args.url, args.out)
    if args.command == "deploy" and args.static:
        return _deploy_static(args.static, args.apply)
    if args.command == "capability" and args.capability_command == "list":
        return _capability_list()
    if args.command == "reference" and args.reference_command == "describe":
        return _reference_describe(args.image)
    if args.command == "cost":
        return _cost()
    if args.command == "performance":
        return _performance()
    if args.command == "migrate":
        return _migrate(args.kind, args.from_version, args.to_version,
                        args.dry_run, args.apply, args.input, args.journal)
    if args.command == "conformance":
        return _conformance()
    if args.command == "verify-state":
        return _verify_state()
    if args.command == "render-replay":
        return _render_replay(args.seed, args.frames, args.width, args.height,
                              args.freeze, args.show_hashes)
    if args.command == "visual-probe":
        return _visual_probe(args.dump_ref, args.dump_current, args.ref,
                             args.current, args.threshold, args.missing_ref)
    if args.command == "asset" and args.asset_command == "list":
        return _asset_list()
    if args.command == "asset" and args.asset_command == "discover":
        return _asset_discover(args.kind)
    if args.command == "asset" and args.asset_command == "match":
        return _asset_match(args.request)
    if args.command == "asset" and args.asset_command == "produce":
        return _asset_produce(args.capability_id, args.kind, args.name,
                              args.seed, args.params_json)
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
    if args.command == "compat" and args.compat_command == "list":
        return _compat_list()
    if args.command == "compat" and args.compat_command == "check":
        return _compat_check(args.kind, args.id, args.version, args.aios_version)
    if args.command == "compat" and args.compat_command == "verify":
        return _compat_verify()
    if args.command == "harness" and args.harness_command == "behavioral":
        return _harness_behavioral(args)
    if args.command == "harness" and args.harness_command == "coverage":
        return _harness_coverage(args)
    if args.command == "harness" and args.harness_command == "meta":
        return _harness_meta(args)
    if args.command == "harness" and args.harness_command == "release":
        return _harness_release(args)
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


def _skill_distill(url: str, out: str) -> int:
    """Distill skill từ repo URL — R5 (M11-P4a, TASK-083)."""
    from ..ecosystem.distiller import SkillDistillError, SkillDistiller

    try:
        report = SkillDistiller().distill(url, out)
    except SkillDistillError as exc:
        print(f"ERROR: {exc} (fail-closed — INV-035)")
        return 1
    print(f"Distilled OK — license: {report.license_status}")
    print(f"  files: {', '.join(report.distilled_files)}")
    print(f"  manifest: {report.manifest_path}")
    print(f"  capabilities: {', '.join(report.capabilities) or '-'}")
    if report.warnings:
        for w in report.warnings:
            print(f"  WARN: {w}")
    return 0


def _deploy_static(dir_path: str, apply: bool) -> int:
    """Deploy static dir — R7 (M11-P4b, TASK-083). Dry-run default."""
    from ..ecosystem.deploy import StaticDeploy

    report = StaticDeploy().deploy(dir_path, dry_run=not apply)
    print(f"Deploy [{report.status}] — {report.dir}")
    print(f"  files: {report.files} · bytes: {report.total_bytes}")
    print(f"  sha256: {report.total_sha256}")
    if report.marker:
        print(f"  marker: {report.marker}")
    if report.hint:
        print(f"  hint: {report.hint}")
    return 0 if report.status == "ok" else 1


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


def _reference_describe(image: str) -> int:
    """Describe reference image — R12 (M11-P3d, TASK-082), mock vision."""
    from ..rendering import AssetError, ReferenceAssetUnderstanding

    try:
        desc = ReferenceAssetUnderstanding().ingest(image)
    except AssetError as exc:
        print(f"ERROR: {exc} (fail-closed — INV-035)")
        return 1
    print("Reference description (mock vision):")
    print(f"  scene:   {desc.scene}")
    print(f"  style:   {desc.style}")
    print(f"  objects: {', '.join(desc.objects) or '-'}")
    print(f"  palette: {', '.join(desc.palette) or '-'}")
    if desc.raw_text:
        print(f"  raw:     {desc.raw_text}")
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


def _migrate(kind: str, from_version: str, to_version: str,
             dry_run: bool, apply: bool, input_file: str | None,
             journal_path: str = "aios/data/migrations.db") -> int:
    """Migration 1.0 (M10-F5, TASK-074) + nhánh AIOS 1.0→1.1 (M12 C2, TASK-085)."""
    from ..upgrade.migration import (
        MigrationEngine,
        MigrationFormats,
        MigrationJournal,
        MigrationPlan,
        MigrationStep,
    )

    # -- M12 C2: nhánh 1.0.0 → 1.1.0 (matrix-gated, plan chuẩn) --------------
    if from_version == "1.0.0" and to_version == "1.1.0":
        from ..upgrade.backup import BackupStore
        from ..upgrade.compatibility import AIOS_VERSION
        from ..upgrade.migration_110 import (
            Aios110Migrator,
            Aios110Result,
            get_plan,
            SUPPORTED_KINDS,
        )

        if kind not in SUPPORTED_KINDS:
            print(f"FAILED: kind {kind!r} không hỗ trợ migration 1.0→1.1 "
                  f"({','.join(SUPPORTED_KINDS)})")
            return 1
        # stub khớp matrix (C1-03) — hoặc đọc --input (C2-02)
        if input_file:
            try:
                with open(input_file, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except Exception as exc:  # noqa: BLE001
                print(f"FAILED: đọc --input {input_file!r} lỗi: {exc}")
                return 1
        elif kind == "config":
            payload = {}
        elif kind == "plugin":
            payload = {"id": "demo", "version": "1.0.0", "aios": {"min": "1.0.0"}}
        elif kind == "workflow":
            payload = {"name": "demo_flow", "version": "1.0.0",
                       "nodes": [{"id": "n1", "type": "task", "name": "n1"}]}
        else:  # contract
            payload = {"id": "agent", "version": "1.0.0"}

        migrator = Aios110Migrator(
            engine=MigrationEngine(journal=MigrationJournal(journal_path)),
            backup_store=BackupStore(journal_path.replace("migrations.db", "backups.db")),
        )
        try:
            if dry_run:
                result = migrator.dry_run(kind, payload)
                print(json.dumps({
                    "dry_run": True,
                    "kind": kind,
                    "steps": result.payload.get("_dry_run_steps", []),
                    "matrix": result.matrix,
                }, indent=2))
                return 0
            if apply:
                result = migrator.apply(kind, payload)
                print(json.dumps({
                    "applied": True,
                    "migration_id": get_plan(kind, migrator.component_id(kind, payload)).migration_id,
                    "backup_id": result.backup_id,
                    "journal": result.journal_status,
                    "matrix": result.matrix,
                    "payload": result.payload,
                }, indent=2, default=str))
                return 0
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED: {exc}")
            return 1
        print("Chọn --dry-run hoặc --apply")
        return 2

    # -- nhánh cũ (v0→v1) — giữ nguyên hành vi ---------------------------------
    # input payload stub (demo): config/workflow/plugin v0
    if kind == "config":
        payload = {"autonomous": {"budget": {"max_duration_s": 7200.0}}}
        fmt = MigrationFormats.config_v0_to_v1
    elif kind == "workflow":
        payload = {"id": "w", "nodes": [{"id": "n1", "type": "task", "name": "n1"}]}
        fmt = MigrationFormats.workflow_v0_to_v1
    elif kind == "plugin":
        payload = {"id": "p", "name": "p", "version": "0.9.0",
                   "aios": {"min": "1.0.0"}}
        fmt = MigrationFormats.plugin_v0_to_v1
    else:
        print(f"FAILED: kind {kind!r} không hỗ trợ (config|workflow|plugin)")
        return 1

    plan = MigrationPlan(
        migration_id=f"{kind}:{from_version}->{to_version}",
        kind=kind, from_version=from_version, to_version=to_version,
        steps=[MigrationStep(kind=kind, id=f"{kind}.v1", fn=fmt)],
    )
    engine = MigrationEngine(journal=MigrationJournal(journal_path))
    try:
        if dry_run:
            result = engine.dry_run(plan, payload)
            print(json.dumps({"dry_run": True, "steps": result["_dry_run_steps"],
                              "payload": result}, indent=2))
            return 0
        if apply:
            result = engine.apply(plan, payload)
            print(json.dumps({"applied": True, "migration_id": plan.migration_id,
                              "payload": result}, indent=2))
            return 0
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}")
        return 1
    print("Chọn --dry-run hoặc --apply")
    return 2


def _conformance() -> int:
    """AIOS conformance — 10 areas + 20 GS + 6 release gates (M10 + M11)."""
    from ..harness.certification import ConformanceRunner, format_conformance

    report = ConformanceRunner().run()
    print(format_conformance(report))
    return 0 if report.ready else 1


def _verify_state() -> int:
    """INV-035 — verification state model + fail-closed gate (M11-P0, TASK-078)."""
    from ..verification import VerificationGate, default_mechanisms
    from ..verification.gate import format_gate_report
    from ..verification.normalize import describe_transition_table

    print(describe_transition_table())
    print("")
    report = VerificationGate(default_mechanisms()).check_all()
    print(format_gate_report(report))
    return 0 if report.fail_closed else 1


def _render_replay(
    seed: int, frames: int, width: int, height: int,
    freeze: str, show_hashes: bool,
) -> int:
    """M11-P1 (TASK-079): DeterministicHarness với mock render_fn.

    Mock render: pixel = (frame_index*7 + t*13 + seed) % 256 → deterministic.
    """
    from ..rendering import DeterministicHarness, RenderTimeline
    from ..rendering.contracts import RenderFn

    def mock_render(frame) -> bytes:  # noqa: ANN001
        buf = bytearray(width * height * 3)
        for i in range(len(buf)):
            buf[i] = (frame.frame_index * 7 + int(frame.t * 13) + frame.seed) % 256
        return bytes(buf)

    timeline = RenderTimeline()
    timeline.record("keydown", 100, {"key": "start"})
    timeline.record("pointer", 500, {"x": 10, "y": 20})

    harness = DeterministicHarness(mock_render, width=width, height=height,
                                   freeze_policy=freeze)
    result = harness.run(timeline, seed=seed, num_frames=frames)

    print(f"RenderReplay — {width}×{height}, seed={seed}, "
          f"{frames} frames, freeze={freeze}")
    print("=" * 50)
    print(f"stable: {result.stable}")
    if result.diff_frames:
        print(f"diff_frames ({len(result.diff_frames)}): {result.diff_frames[:20]}")
    if show_hashes and result.frames_a:
        for f in result.frames_a[:5]:
            print(f"  frame {f.frame_index}: t={f.t:.3f} "
                  f"hash={f.pixel_hash[:12]}…")
    print(f"outcome: {result.outcome.state.value} "
          f"({result.outcome.evidence})")
    return 0 if result.stable else 1


def _mock_visual_evidence(*, changed_state: bool = False) -> dict:
    """Mock evidence (R10 + R1) — JSON-serializable."""
    state = {
        "version": "1.0",
        "screen": "game",
        "entities": {"player": {"x": 160, "y": 90, "scale": 3}},
        "input": {"left": False, "right": True},
        "t": 0.5,
        "seed": 42,
    }
    if changed_state:
        state["entities"]["player"]["scale"] = 2  # bug: scale mismatch
    return {
        "version": "1.0",
        "screenshot": "data:image/png;base64,"
                      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        "dom_snapshot": {"tag": "canvas", "attrs": {"id": "game"}, "children": []},
        "render_state": state,
        "input_timeline": [
            {"type": "keydown", "timestamp": 100.0, "payload": {"key": "start"}},
        ],
        "browser_meta": {"browser": "chromium", "os": "windows",
                         "viewport": [640, 360], "device_scale_factor": 1.0},
        "seed": 42,
        "pixel_diff": -1.0,
    }


def _visual_probe(
    dump_ref: str, dump_current: str, ref_file: str, current_file: str,
    threshold: int, missing_ref: bool,
) -> int:
    """M11-P2 (TASK-080): VisualRegressionProbe — compare evidence fail-closed."""
    import json

    from ..observability.visual import get_visual_metrics
    from ..rendering import VisualEvidence, VisualRegressionProbe

    if dump_ref:
        with open(dump_ref, "w", encoding="utf-8") as f:
            json.dump(_mock_visual_evidence(), f, ensure_ascii=False, indent=2)
        print(f"ref evidence → {dump_ref}")
        return 0
    if dump_current:
        with open(dump_current, "w", encoding="utf-8") as f:
            json.dump(_mock_visual_evidence(changed_state=True), f,
                      ensure_ascii=False, indent=2)
        print(f"current evidence → {dump_current}")
        return 0

    ref: VisualEvidence | None = None
    current: VisualEvidence | None = None
    if ref_file:
        with open(ref_file, encoding="utf-8") as f:
            ref = VisualEvidence.model_validate(json.load(f))
    if current_file:
        with open(current_file, encoding="utf-8") as f:
            current = VisualEvidence.model_validate(json.load(f))
    if missing_ref:
        ref = None  # mô phỏng thiếu ref → MISSING_EVIDENCE

    probe = VisualRegressionProbe(pixel_threshold=threshold)
    result = probe.compare(ref, current)

    metrics = get_visual_metrics()
    metrics.record_probe(passed=result.passed, pixel_diff=result.pixel_diff)

    print(f"VisualRegressionProbe — threshold={threshold}")
    print("=" * 50)
    print(f"outcome: {result.outcome.state.value} ({result.outcome.verdict.value})")
    print(f"  evidence: {result.outcome.evidence}")
    print(f"  pixel_diff: {result.pixel_diff:.2f}%")
    if result.state_diffs:
        print(f"  state_diffs ({len(result.state_diffs)}): "
              f"{result.state_diffs[:5]}")
    if result.dom_diffs:
        print(f"  dom_diffs ({len(result.dom_diffs)}): {result.dom_diffs[:5]}")
    print(f"  metrics: {metrics.snapshot()}")
    return 0 if result.passed else 1


def _asset_registry():
    """Registry mặc định — singleton + default capabilities từ skills/."""
    from ..rendering import AssetCapabilityRegistry, default_asset_capabilities

    registry = AssetCapabilityRegistry()
    for cap in default_asset_capabilities():
        registry.register(cap)
    return registry


def _asset_list() -> int:
    registry = _asset_registry()
    caps = registry.list()
    if not caps:
        print("<empty> — chưa có capability asset (register thủ công hoặc merge skills/)")
        return 0
    print(f"Asset capabilities ({len(caps)}):")
    for c in caps:
        print(f"  {c.id:<24} kinds={c.kinds} source={c.source or '-'}")
    print(f"counters: {registry.snapshot_counters()}")
    return 0


def _asset_discover(kind: str) -> int:
    registry = _asset_registry()
    caps = registry.discover(kind)
    print(f"Discover kind={kind}: {len(caps)} capability")
    for c in caps:
        print(f"  {c.id}: {c.name} — {c.description}")
    return 0


def _asset_match(request: str) -> int:
    from ..rendering import CreativeMatcher

    matcher = CreativeMatcher(_asset_registry())
    results = matcher.match(request)
    print(f"Match request={request!r}: {len(results)} result")
    for r in results:
        print(f"  {r.score:>3}  {r.capability_id:<24} {r.reason}")
    if not results:
        print("  (no match — không có capability phù hợp)")
    return 0


def _asset_produce(capability_id: str, kind: str, name: str, seed: int,
                   params_json: str) -> int:
    import json

    from ..rendering import AssetSpec

    registry = _asset_registry()
    try:
        params = json.loads(params_json)
    except json.JSONDecodeError:
        params = {}
    spec = AssetSpec(kind=kind, name=name, seed=seed, params=params)
    try:
        out = registry.produce(capability_id, spec)
    except Exception as exc:  # noqa: BLE001 — fail-closed (ERROR)
        print(f"produce FAILED: {exc}")
        return 1
    print(f"produced: {out.artifact_ref}")
    print(f"  sha256={out.sha256[:16]}… size={out.size} "
          f"idempotency={out.idempotency.value}")
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


def _compat_list() -> int:
    """Compatibility Matrix registry (M12-P0 C1, TASK-084)."""
    from ..upgrade.compatibility import CompatibilityMatrix

    rows = CompatibilityMatrix().list()
    w_kind = max(len(r["kind"]) for r in rows) if rows else 4
    w_id = max(len(r["id"]) for r in rows) if rows else 2
    print(f"{'kind'.ljust(w_kind)}| {'id'.ljust(w_id)}| version | aios_min | aios_max")
    print("-" * 46)
    for r in rows:
        print(f"{r['kind'].ljust(w_kind)}| {r['id'].ljust(w_id)}| "
              f"{r['version'].ljust(7)} | {r['aios_min'].ljust(7)} | {r['aios_max'] or '*'}")
    print(f"({len(rows)} entries)")
    return 0


def _compat_check(kind: str, component_id: str, version: str,
                  aios_version: str | None = None) -> int:
    """Check component so với Compatibility Matrix — JSON 1 dòng, exit 0/1 (fail-closed)."""
    from ..upgrade.compatibility import AIOS_VERSION, CompatibilityMatrix

    result = CompatibilityMatrix().check(
        kind, component_id, version, aios_version=aios_version or AIOS_VERSION
    )
    print(json.dumps({
        "compatible": result.compatible,
        "errors": result.errors,
        "warnings": result.warnings,
    }))
    return 0 if result.compatible else 1


def _compat_verify() -> int:
    """Backward compatibility suite cũ→mới trên AIOS 1.1 — JSON 1 dòng, exit 0/1."""
    from ..upgrade.backward_compat import BackwardCompatibilitySuite

    report = BackwardCompatibilitySuite().run()
    summary = {
        "passed": sum(1 for r in report.results if r.ok),
        "failed": sum(1 for r in report.results if not r.ok),
    }
    print(json.dumps({
        "ok": report.ok,
        "fail_closed": report.fail_closed,
        "results": [
            {"id": r.id, "kind": r.kind, "ok": r.ok, "detail": r.detail}
            for r in report.results
        ],
        "summary": summary,
    }))
    return 0 if report.ok else 1


def _harness_behavioral(args) -> int:
    """Behavioral conformance (M13-P0, TASK-089) — N lần + repeat + fault +
    evidence + gate. JSON 1 dòng, exit 0 (PASS) / 1 (FAIL/ERROR)."""
    from ..harness.behavioral import (
        BehavioralConformanceEngine, ConformanceConfig, ConformanceStatus,
    )
    from ..harness.benchmark.contracts import Baseline
    from ..harness.testing import load as load_scenario

    try:
        scenario = load_scenario(args.scenario_file)
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: load scenario: {exc}")
        return 1

    faults: list = []
    if args.faults:
        try:
            faults = json.loads(args.faults)
            if not isinstance(faults, list):
                print("FAILED: --faults must be a JSON list")
                return 1
        except json.JSONDecodeError as exc:
            print(f"FAILED: --faults invalid JSON: {exc}")
            return 1
    fault_iterations: list = []
    if args.fault_iterations:
        try:
            fault_iterations = json.loads(args.fault_iterations)
            if not isinstance(fault_iterations, list):
                print("FAILED: --fault-iterations must be a JSON list")
                return 1
        except json.JSONDecodeError as exc:
            print(f"FAILED: --fault-iterations invalid JSON: {exc}")
            return 1

    baseline: Baseline | None = None
    if args.baseline:
        try:
            with open(args.baseline, "r", encoding="utf-8") as fh:
                baseline = Baseline.model_validate(json.load(fh))
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED: load baseline: {exc}")
            return 1

    config = ConformanceConfig(
        profile=args.profile,
        scenario=scenario,
        iterations=args.iterations,
        duration_s=args.duration,
        faults=faults,
        fault_iterations=fault_iterations,
        repeat_samples=args.repeat_samples,
        baseline=baseline,
        strict=not args.no_strict,
    )
    engine = BehavioralConformanceEngine()
    try:
        report = engine.run(config)
    except Exception as exc:  # noqa: BLE001 — fail-fast (P2-3 v2)
        print(f"FAILED: {exc}")
        return 1

    if args.save_baseline:
        try:
            saved = engine.build_baseline(report)
            with open(args.save_baseline, "w", encoding="utf-8") as fh:
                json.dump(saved.model_dump(mode="json"), fh, indent=2)
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED: save baseline: {exc}")
            return 1

    print(json.dumps(report.model_dump(mode="json"), indent=2))
    return 0 if report.status == ConformanceStatus.PASS else 1


def _harness_coverage(args) -> int:
    """Harness Coverage + Readiness (M13-P1, TASK-090).

    1 JSON document (coverage + readiness), exit 0 (READY) / 1 (NOT_READY).
    V1 mặc định NOT_READY (replay gate — cần TASK-091) — fail-closed thật.
    """
    from ..harness import HarnessRegistry
    from ..harness.coverage import HarnessCoverage, HarnessReadinessScorer
    from ..kernel import RuntimeKernel

    kernel = RuntimeKernel.create()
    reg = kernel.container.resolve(HarnessRegistry)
    try:
        coverage = HarnessCoverage(reg).build()
        readiness = HarnessReadinessScorer(
            min_overall=args.min_overall, min_replay=args.min_replay,
            production_tests_available=args.production_tests,
        ).score(coverage)
    except Exception as exc:  # noqa: BLE001
        print(f"FAILED: {exc}")
        return 1
    payload = {
        "coverage": coverage.model_dump(mode="json"),
        "readiness": readiness.model_dump(mode="json"),
    }
    print(json.dumps(payload, indent=2))
    return 0 if readiness.status.value == "ready" else 1


def _harness_meta(args) -> int:
    """Meta-Harness (M13-P2, TASK-091): verify the verifier.

    1 JSON document (meta report), exit 0 (PASS) / 1 (FAIL).
    """
    from ..harness import HarnessRegistry, HarnessRunner
    from ..harness.meta import MetaHarness
    from ..kernel import RuntimeKernel
    from ..kernel.services import StateService

    kernel = RuntimeKernel.create()
    reg = kernel.container.resolve(HarnessRegistry)
    # Tạo trực tiếp (HarnessRunner chưa register trong container — giống coverage)
    state = StateService()
    runner = HarnessRunner(state_service=state)
    harness = MetaHarness(state_service=state,
                          registry_ids=sorted(reg.list()))
    ctx = runner.create_context(
        harness, "meta", config={"strict": not args.no_strict})
    report = runner.execute(harness, ctx)
    meta_report = harness.get_report(ctx.run_id) or {}
    print(json.dumps({"meta": meta_report,
                      "status": meta_report.get("status", "fail")}, indent=2))
    return 0 if meta_report.get("status") == "pass" else 1


def _harness_release(args) -> int:
    """Release Gate (M13-P3, TASK-092): System Readiness + Harness Trust.

    1 JSON document (release report), exit 0 (PASS) / 1 (BLOCKED).
    """
    from ..harness import HarnessRegistry, HarnessRunner
    from ..harness.release import ReleaseGateHarness
    from ..kernel import RuntimeKernel
    from ..kernel.services import StateService

    kernel = RuntimeKernel.create()
    reg = kernel.container.resolve(HarnessRegistry)
    # Tạo trực tiếp (HarnessRunner chưa register trong container — giống meta)
    state = StateService()
    runner = HarnessRunner(state_service=state)
    release_h = ReleaseGateHarness(
        reg.get("coverage"), reg.get("meta"), state_service=state)
    ctx = runner.create_context(
        release_h, "release", config={"strict": not args.no_strict})
    report = runner.execute(release_h, ctx)
    release_report = release_h.get_report(ctx.run_id) or {}
    print(json.dumps({"release": release_report,
                      "status": release_report.get("status", "blocked")},
                     indent=2))
    return 0 if release_report.get("status") == "pass" else 1


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
