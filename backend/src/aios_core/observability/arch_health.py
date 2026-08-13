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
]

_CONTRACT_RULES: list[tuple[str, str, tuple[str, ...]]] = [
    ("contract", "contracts", ("aios_core.kernel.services", "aios_core.kernel.events")),
]

# orchestrator/planner.py is exempt (uses models — INV-005 rule B)
_ORCHESTRATOR_EXEMPT = "orchestrator.planner"


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

        # -- layer rules ------------------------------------------------------
        for kind, sub, forbidden in _LAYER_RULES:
            target = package_dir / sub
            if not target.is_dir():
                continue
            for py in sorted(target.rglob("*.py")):
                rel = py.relative_to(package_dir).with_suffix("").as_posix().replace("/", ".")
                if rel.endswith(_ORCHESTRATOR_EXEMPT):
                    continue
                ext, mods = collect_imports(package_dir, rel)
                for f in forbidden:
                    for mod in mods | ext:
                        if mod == f or mod.startswith(f + ".") or f.startswith(mod + "."):
                            violations.append(
                                ArchViolation(kind, rel, f"imports forbidden module: {mod}")
                            )

        # -- contract rules ---------------------------------------------------
        for kind, sub, forbidden in _CONTRACT_RULES:
            target = package_dir / sub
            if not target.is_dir():
                continue
            for py in sorted(target.rglob("*.py")):
                rel = py.relative_to(package_dir).with_suffix("").as_posix().replace("/", ".")
                ext, mods = collect_imports(package_dir, rel)
                for f in forbidden:
                    for mod in mods | ext:
                        if mod == f or mod.startswith(f + ".") or f.startswith(mod + "."):
                            violations.append(
                                ArchViolation(kind, rel, f"imports forbidden module: {mod}")
                            )

        # -- policy rule (INV-007): execution.py must call self._policy.evaluate
        policy_file = package_dir / "aios_core" / "kernel" / "services" / "execution.py"
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
