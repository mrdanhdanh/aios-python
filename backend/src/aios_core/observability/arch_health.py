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
