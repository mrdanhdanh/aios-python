"""AST-based import scanner for architecture invariant checks (TASK-016 engine,
relocated from tests/ to observability/ in TASK-021 — single source of truth).

Pure static analysis: parses source with ``ast`` and NEVER imports the runtime
package. Used by ``tests/test_architecture.py`` (via the tests/_arch_scan.py
shim) and by ``observability/arch_health.py``.

Semantics (spec TASK-016, critique C1-04/C1-09/C2-01/C2-04/R2):
- EVERY Import node counts (top-level, inside functions, try/except, TYPE_CHECKING).
- Returns two sets: ``external_top_level`` (e.g. {"langgraph", "openai"}) and
  ``aios_core_modules`` with FULL dotted names (e.g. "aios_core.models.base").
- Forbidden matching is dot-boundary and TWO-WAY:
  ``mod == target or mod.startswith(target + ".") or target.startswith(mod + ".")``.
"""

from __future__ import annotations

import ast
from pathlib import Path

# src/aios_core/observability/arch_scan.py -> parents[2] = backend/src
SRC_ROOT = Path(__file__).resolve().parents[2]
assert (SRC_ROOT / "aios_core").is_dir(), f"SRC_ROOT sai: {SRC_ROOT} (phải chứa aios_core/)"

AIOS_CORE = "aios_core"


def _module_level(module_rel: str) -> int:
    """Number of leading dots in a relative import (0 = absolute)."""
    return len(module_rel) - len(module_rel.lstrip("."))


def _resolve_relative(pkg_dotted: str, module_rel: str) -> str:
    """Resolve a relative import to an absolute aios_core dotted path."""
    dots = _module_level(module_rel)
    base = module_rel[dots:]
    parts = pkg_dotted.split(".") if pkg_dotted else [AIOS_CORE]
    # Go up (dots-1) levels from the current package.
    up = parts[: max(1, len(parts) - (dots - 1))]
    if base:
        up = up + [base]
    return ".".join(up)


def collect_imports(package_dir: Path, module_rel: str) -> tuple[set[str], set[str]]:
    """Parse one module file and collect its imports.

    ``package_dir``: directory containing the package (e.g. SRC_ROOT for aios_core).
    ``module_rel``: dotted path of the module relative to package_dir,
    e.g. "aios_core/orchestrator/planner" or "aios_core/workflow/__init__".
    Returns (external_top_level, aios_core_modules) with full dotted names.
    """
    path = (package_dir / module_rel.replace(".", "/")).with_suffix(".py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    pkg_dotted = module_rel.rsplit("/", 1)[0].replace("/", ".")
    external: set[str] = set()
    aios_mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name == "__future__":
                    continue
                if name == AIOS_CORE or name.startswith(AIOS_CORE + "."):
                    aios_mods.add(name)
                else:
                    external.add(name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            level = node.level
            mod = node.module or ""
            if level == 0:
                # absolute: from aios_core.x import y / from langgraph import ...
                if mod == "__future__":
                    continue
                if mod == AIOS_CORE or mod.startswith(AIOS_CORE + "."):
                    aios_mods.add(mod)
                elif mod:
                    external.add(mod.split(".")[0])
            else:
                rel = "." * level + mod
                resolved = _resolve_relative(pkg_dotted, rel)
                aios_mods.add(resolved)
    return external, aios_mods


def module_imports(
    module_rel: str,
    forbidden: list[str],
    package_dir: Path = SRC_ROOT,
) -> list[str]:
    """Return forbidden imports found in a module (two-way dot-boundary match).

    ``module_rel`` e.g. "aios_core/workflow/definition" (relative to package_dir).
    """
    external, aios_mods = collect_imports(package_dir, module_rel)
    hits: list[str] = []
    for target in forbidden:
        for mod in aios_mods | external:
            if mod == target or mod.startswith(target + ".") or target.startswith(mod + "."):
                hits.append(mod)
    return sorted(hits)


def dir_imports(
    package_dir: Path,
    forbidden: list[str],
    exclude: list[str] | None = None,
) -> list[str]:
    """Return forbidden imports found under a directory (non-recursive scanning
    of package files). ``package_dir`` must be under SRC_ROOT."""
    exclude = exclude or []
    hits: list[str] = []
    for py in sorted(package_dir.glob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        if any(rel.startswith(e) for e in exclude):
            continue
        hits.extend(module_imports(rel, forbidden))
    return sorted(set(hits))
