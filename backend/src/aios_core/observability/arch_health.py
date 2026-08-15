"""Architecture health (TASK-021) — AST scan reporting layer over arch_scan.

Scans a package directory for layer/contract/policy violations (subset of the
checks enforced by tests/test_architecture.py). Uses collect_imports with an
explicit package_dir — dir_imports stays test-only (hardcodes SRC_ROOT).
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .arch_scan import SRC_ROOT, collect_imports

# (kind, target_dir, forbidden aios/external modules)
_LAYER_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("layer", "agents", ("aios_core.kernel.services", "aios_core.tools")),
    ("layer", "workflow", ("langgraph", "aios_core.models")),
    ("layer", "orchestrator", ("aios_core.models",)),
    ("layer", "capabilities", ("aios_core.models", "aios_core.workflow", "aios_core.tools")),
    # -- M5 — Core Intelligence (INV-011..016) --------------------------------
    # These mirror the allow-lists enforced by tests/test_architecture.py
    # (test_inv_memory_import_allowlist, test_inv_context_import_allowlist,
    # test_inv_planning_import_allowlist, test_inv_graph_import_allowlist,
    # test_inv016_scheduler_import_allowlist). PLAN §M5 requires "observability
    # đầy đủ" for INV-011..016, so the runtime architecture-health scanner must
    # actually scan the M5 packages (not silently skip them, cf. M4 F1).
    # Rules forbid DOWNWARD layer crossings only; every module below is one the
    # package is allowed to import per its allow-list, so no false positives.
    ("layer", "memory", (
        "aios_core.agents", "aios_core.tools", "aios_core.capabilities",
        "aios_core.workflow", "aios_core.orchestrator", "aios_core.models",
        "aios_core.context", "aios_core.knowledge", "aios_core.prompts",
        "aios_core.skills", "aios_core.sandbox", "aios_core.observability",
        "aios_core.upgrade", "aios_core.harness", "aios_core.enterprise",
        "aios_core.ecosystem", "aios_core.plugins", "aios_core.extension",
        "aios_core.contracts", "aios_core.metadata",
        "aios_core.kernel.events", "aios_core.kernel.dag",
        "aios_core.kernel.execution_plan", "aios_core.kernel.graph",
        "aios_core.kernel.scheduler", "aios_core.kernel.policy",
        "aios_core.kernel.resource", "aios_core.kernel.state",
        "aios_core.kernel.runtime_kernel",
    )),
    ("layer", "context", (
        "aios_core.agents", "aios_core.tools", "aios_core.capabilities",
        "aios_core.workflow", "aios_core.orchestrator", "aios_core.models",
        "aios_core.knowledge", "aios_core.prompts", "aios_core.skills",
        "aios_core.sandbox", "aios_core.observability", "aios_core.harness",
        "aios_core.enterprise", "aios_core.ecosystem", "aios_core.plugins",
        "aios_core.extension", "aios_core.contracts",
        "aios_core.kernel.dag", "aios_core.kernel.execution_plan",
        "aios_core.kernel.graph", "aios_core.kernel.scheduler",
        "aios_core.kernel.policy", "aios_core.kernel.resource",
        "aios_core.kernel.runtime_kernel", "aios_core.kernel.events",
    )),
    ("layer", "models/router", (
        "aios_core.agents", "aios_core.tools", "aios_core.capabilities",
        "aios_core.workflow", "aios_core.orchestrator", "aios_core.context",
        "aios_core.knowledge", "aios_core.memory", "aios_core.prompts",
        "aios_core.skills", "aios_core.sandbox", "aios_core.observability",
        "aios_core.harness", "aios_core.enterprise", "aios_core.ecosystem",
        "aios_core.plugins", "aios_core.extension", "aios_core.contracts",
    )),
    ("layer", "orchestrator/planning", (
        "aios_core.knowledge", "aios_core.context", "aios_core.contracts",
        "aios_core.memory", "aios_core.agents", "aios_core.tools",
        "aios_core.capabilities", "aios_core.prompts", "aios_core.skills",
        "aios_core.sandbox", "aios_core.observability", "aios_core.harness",
        "aios_core.enterprise", "aios_core.ecosystem", "aios_core.plugins",
        "aios_core.extension",
    )),
    ("layer", "kernel/graph", (
        "aios_core.orchestrator", "aios_core.models", "aios_core.memory",
        "aios_core.context", "aios_core.knowledge", "aios_core.tools",
        "aios_core.agents", "aios_core.capabilities", "aios_core.workflow",
        "aios_core.prompts", "aios_core.skills", "aios_core.sandbox",
        "aios_core.contracts", "aios_core.observability", "aios_core.harness",
        "aios_core.enterprise", "aios_core.ecosystem", "aios_core.plugins",
        "aios_core.extension",
    )),
    ("layer", "kernel/scheduler", (
        "aios_core.orchestrator", "aios_core.models", "aios_core.memory",
        "aios_core.context", "aios_core.knowledge", "aios_core.tools",
        "aios_core.agents", "aios_core.capabilities", "aios_core.workflow",
        "aios_core.prompts", "aios_core.skills", "aios_core.sandbox",
        "aios_core.contracts", "aios_core.observability", "aios_core.harness",
        "aios_core.enterprise", "aios_core.ecosystem", "aios_core.plugins",
        "aios_core.extension",
    )),
    # -- M6 — AIOS Harness (INV-017..022) ------------------------------------
    # Mirror the allow-list enforced by tests/test_architecture.py
    # (test_inv017_harness_import_allowlist, test_inv017_harness_no_kernel_impl,
    # test_inv018_runner_builds_evidence, test_inv019_*/test_inv020_*/test_inv021_*
    # /test_inv022_*). PLAN §M6 requires "observability đầy đủ" for INV-017..022,
    # so the runtime architecture-health scanner must actually scan the harness/
    # packages (not silently skip them, cf. M5 F1). The rule forbids harness/
    # from coupling to kernel implementation + the control-plane layers it must
    # stay isolated from. Every forbidden module below is one harness is NOT
    # allowed to import per its allow-list (config/logging/kernel.services.state|
    # artifacts/contracts.artifact), so no false positives.
    ("layer", "harness", (
        "aios_core.kernel.services.execution",
        "aios_core.kernel.services.resource",
        "aios_core.kernel.services.scheduler",
        "aios_core.kernel.services.policy",
        "aios_core.kernel.services.permissions",
        "aios_core.kernel.services.context",
        "aios_core.kernel.services.events",
        "aios_core.kernel.graph",
        "aios_core.kernel.runtime_kernel",
        "aios_core.orchestrator",
        "aios_core.orchestrator.planning",
        "aios_core.models",
        "aios_core.memory",
        "aios_core.knowledge",
        "aios_core.capabilities",
        "aios_core.workflow",
        "aios_core.agents",
        "aios_core.tools",
        "aios_core.sandbox",
        "aios_core.ecosystem",
        "aios_core.enterprise",
        "aios_core.upgrade",
        "aios_core.extension",
        "aios_core.plugins",
        "aios_core.prompts",
        "aios_core.skills",
        "aios_core.observability",
    )),
    # -- M10 — Certification Suite (TASK-073) ----------------------------------
    # Certification = hệ thống kiểm chứng TOÀN CỤC (M10): đọc/gọi API public
    # của mọi layer để verify (INV-017 mở rộng: "chỉ gọi API, không sửa").
    # Rule riêng thay vì gộp vào "harness" — nếu không, mọi import verify bị
    # coi là vi phạm. Cấm các module implementation sâu mà certification
    # không bao giờ dùng.
    ("layer", "harness/certification", (
        "aios_core.kernel.graph",
        "aios_core.capabilities",
        "aios_core.workflow",
        "aios_core.sandbox",
        "aios_core.skills",
        "aios_core.prompts",
        "aios_core.context",
    )),
    # -- M7 — Enterprise / Control Plane (INV-022..029) ------------------------
    # PLAN §M7 requires "observability đầy đủ" for the 8 M7 invariants, so the
    # runtime scanner MUST actually scan enterprise/ (not silently skip it, cf.
    # M5 F1 silent-skip). enterprise/ is the Control Plane (INV-029) and must
    # stay self-contained: it may only import its own intra-package modules +
    # pydantic/stdlib. Every downward aios_core import below is forbidden,
    # mirroring the allow-list enforced by tests/test_architecture.py
    # (test_inv022_..test_inv029_*). This keeps the control plane from reaching
    # into execution/runtime internals and prevents a God Object.
    ("layer", "enterprise", (
        "aios_core.kernel", "aios_core.orchestrator", "aios_core.models",
        "aios_core.memory", "aios_core.knowledge", "aios_core.tools",
        "aios_core.agents", "aios_core.capabilities", "aios_core.workflow",
        "aios_core.context", "aios_core.prompts", "aios_core.skills",
        "aios_core.sandbox", "aios_core.observability", "aios_core.harness",
        "aios_core.upgrade", "aios_core.autonomous", "aios_core.api",
        "aios_core.ecosystem", "aios_core.plugins", "aios_core.extension",
        "aios_core.contracts", "aios_core.metadata", "aios_core.catalog",
        "aios_core.goals", "aios_core.policy",
    )),
    # -- M8 — Ecosystem (Plugin Runtime / Extension Contracts / Registry /
    # DevKit / Marketplace / Certification; INV-022..029 reuse + M8 allow-lists)
    # PLAN §M8 requires "observability đầy đủ" for the ecosystem boundary, so
    # the runtime scanner MUST actually scan plugins/ extension/ ecosystem/ (not
    # silently skip them, cf. M5 F1 silent-skip). These mirror the allow-lists
    # enforced by tests/test_architecture.py (test_m8_plugins_import_allowlist,
    # test_m8_extension_import_allowlist, test_m8_ecosystem_import_allowlist).
    # Every forbidden module below is one the package is NOT allowed to import
    # per its allow-list, so no false positives (the real packages pass the
    # test_m8_* allow-list checks, i.e. import only their permitted modules).
    ("layer", "plugins", (
        "aios_core.agents", "aios_core.tools", "aios_core.capabilities",
        "aios_core.workflow", "aios_core.orchestrator", "aios_core.orchestrator.planning",
        "aios_core.models", "aios_core.memory", "aios_core.knowledge",
        "aios_core.context", "aios_core.prompts", "aios_core.sandbox",
        "aios_core.observability", "aios_core.upgrade", "aios_core.harness",
        "aios_core.enterprise", "aios_core.ecosystem", "aios_core.extension",
        "aios_core.contracts", "aios_core.kernel",
    )),
    ("layer", "extension", (
        "aios_core.agents", "aios_core.tools", "aios_core.capabilities",
        "aios_core.workflow", "aios_core.orchestrator", "aios_core.orchestrator.planning",
        "aios_core.models", "aios_core.memory", "aios_core.knowledge",
        "aios_core.context", "aios_core.prompts", "aios_core.skills",
        "aios_core.sandbox", "aios_core.observability", "aios_core.upgrade",
        "aios_core.harness", "aios_core.enterprise", "aios_core.ecosystem",
        "aios_core.plugins", "aios_core.contracts", "aios_core.metadata",
        "aios_core.kernel",
    )),
    ("layer", "ecosystem", (
        "aios_core.agents", "aios_core.tools", "aios_core.capabilities",
        "aios_core.workflow", "aios_core.orchestrator", "aios_core.orchestrator.planning",
        "aios_core.models", "aios_core.memory", "aios_core.knowledge",
        "aios_core.context", "aios_core.prompts", "aios_core.skills",
        "aios_core.sandbox", "aios_core.observability", "aios_core.upgrade",
        "aios_core.harness", "aios_core.enterprise", "aios_core.plugins",
        "aios_core.extension", "aios_core.contracts", "aios_core.kernel",
    )),
    # M9 — Autonomous (INV-030..034, PLAN §M9 "observability đầy đủ").
    # Autonomy Layer đứng TRÊN Orchestrator: autonomous/ KHÔNG chạm Worker
    # Plane (tools/agents — INV-030), KHÔNG tự promote Knowledge (INV-034),
    # và chỉ import kernel.events + kernel.services (aios) — còn lại cấm.
    # KHÔNG cấm aios_core.kernel.events / aios_core.kernel.services (cho phép
    # theo allow-list test_m9_autonomous_import_allowlist) và KHÔNG cấm
    # aios_core.autonomous (intra-package). Các submodule kernel khác bị cấm
    # cụ thể để tránh false-positive trên kernel.events/services (cf. M5 F1
    # silent-skip — runtime scanner phải thực sự quét autonomous/).
    ("layer", "autonomous", (
        "aios_core.agents", "aios_core.tools", "aios_core.capabilities",
        "aios_core.workflow", "aios_core.orchestrator", "aios_core.orchestrator.planning",
        "aios_core.models", "aios_core.memory", "aios_core.knowledge",
        "aios_core.context", "aios_core.prompts", "aios_core.skills",
        "aios_core.sandbox", "aios_core.observability", "aios_core.upgrade",
        "aios_core.harness", "aios_core.enterprise", "aios_core.ecosystem",
        "aios_core.plugins", "aios_core.extension", "aios_core.contracts",
        "aios_core.metadata", "aios_core.catalog", "aios_core.goals",
        "aios_core.policy", "aios_core.api",
        "aios_core.kernel.execution", "aios_core.kernel.execution_plan",
        "aios_core.kernel.resource", "aios_core.kernel.scheduler",
        "aios_core.kernel.policy", "aios_core.kernel.state",
        "aios_core.kernel.runtime_kernel", "aios_core.kernel.dag",
        "aios_core.kernel.graph", "aios_core.kernel.services.execution",
        "aios_core.kernel.services.resource",
    )),
]

_CONTRACT_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("contract", "contracts", ("aios_core.kernel.services", "aios_core.kernel.events")),
]

# orchestrator/planner.py is exempt (uses models — INV-005 rule B)
_ORCHESTRATOR_EXEMPT = "orchestrator/planner"


@dataclass(frozen=True)
class ArchViolation:
    kind: str
    module: str
    message: str


@dataclass(frozen=True)
class ArchReport:
    healthy: bool
    violations: tuple[ArchViolation, ...] = field(default_factory=tuple)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ArchitectureHealth:
    """Scans a package tree for architecture violations (AST, no runtime)."""

    def scan(self, package_dir: Path = SRC_ROOT) -> ArchReport:
        violations: list[ArchViolation] = []

        # The aios_core package may live directly under ``package_dir`` (flat
        # test fixtures) or nested as ``package_dir/aios_core`` (the real tree,
        # where ``SRC_ROOT = backend/src``). Resolve the root that actually
        # contains the scanned sub-packages so layer/contract checks run against
        # the real code instead of silently skipping (the sub-packages are NOT
        # direct children of ``backend/src``).
        aios_root = package_dir / "aios_core" if (package_dir / "aios_core").is_dir() else package_dir

        def _check(rules: list[tuple[str, str, tuple[str, ...]]]) -> None:
            for kind, sub, forbidden in rules:
                target = aios_root / sub
                if not target.is_dir():
                    continue
                for py in sorted(target.rglob("*.py")):
                    # Slash-form module path: collect_imports expects this
                    # ("aios_core/agents/evil"), NOT dot-form — dot-form breaks
                    # its pkg_dotted computation and relative-import resolution.
                    rel = py.relative_to(package_dir).with_suffix("").as_posix()
                    if rel.endswith(_ORCHESTRATOR_EXEMPT):
                        continue
                    # M10: harness/certification có rule riêng — loại khỏi
                    # rule "harness" chung (INV-017 extension, TASK-073).
                    if sub == "harness" and \
                            rel.startswith("aios_core/harness/certification"):
                        continue
                    ext, mods = collect_imports(package_dir, rel)
                    for f in forbidden:
                        for mod in mods | ext:
                            if mod == f or mod.startswith(f + ".") or f.startswith(mod + "."):
                                violations.append(
                                    ArchViolation(kind, rel, f"imports forbidden module: {mod}")
                                )

        # -- layer rules ------------------------------------------------------
        _check(_LAYER_RULES)
        # -- contract rules ---------------------------------------------------
        _check(_CONTRACT_RULES)

        # -- policy rule (INV-007): execution.py must call self._policy.evaluate
        policy_file = aios_root / "kernel" / "services" / "execution.py"
        if policy_file.is_file():
            tree = ast.parse(policy_file.read_text(encoding="utf-8"), filename=str(policy_file))
            found = False
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr == "evaluate":
                    value = node.value
                    if isinstance(value, ast.Attribute) and value.attr == "_policy":
                        found = True
                        break
            if not found:
                violations.append(
                    ArchViolation(
                        "policy",
                        "aios_core/kernel/services/execution",
                        "missing self._policy.evaluate call site (INV-007)",
                    )
                )

        # dedupe (same violation may match multiple rules)
        seen: set[tuple[str, str, str]] = set()
        unique: list[ArchViolation] = []
        for v in violations:
            key = (v.kind, v.module, v.message)
            if key not in seen:
                seen.add(key)
                unique.append(v)
        unique.sort(key=lambda v: (v.kind, v.module))
        return ArchReport(healthy=not unique, violations=tuple(unique))
