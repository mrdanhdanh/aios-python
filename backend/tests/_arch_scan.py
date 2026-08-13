"""AST-based import scanner for architecture invariant tests (TASK-016).

Pure static analysis: parses source with ``ast`` and NEVER imports the runtime
package. Used by ``tests/test_architecture.py`` to enforce INV-001..INV-010.

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

# backend/tests/_arch_scan.py -> parents[1] = backend -> /src = backend/src
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
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


def module_imports(module_rel: str, forbidden: list[str], package_dir: Path | None = None) -> list[str]:
    """Return the list of forbidden imports found in a module ([] = clean)."""
    package_dir = package_dir or SRC_ROOT
    _, aios_mods = collect_imports(package_dir, module_rel)
    hits = []
    for target in forbidden:
        for mod in aios_mods:
            if mod == target or mod.startswith(target + ".") or target.startswith(mod + "."):
                hits.append(f"{module_rel} -> {mod} (forbidden: {target})")
    return hits


def dir_imports(pkg_dir: Path, forbidden: list[str], exclude: list[str] | None = None) -> list[str]:
    """Scan every *.py under pkg_dir (including __init__.py) and collect hits.

    ``pkg_dir``: absolute path to the aios_core subpackage, e.g. SRC_ROOT/"aios_core"/"workflow".
    ``forbidden``: dotted targets (dot-boundary, two-way match).
    Returns list of violation strings ([] = clean).
    """
    exclude = exclude or []
    hits: list[str] = []
    if not pkg_dir.is_dir():
        return hits
    for py in sorted(pkg_dir.rglob("*.py")):
        rel = py.relative_to(SRC_ROOT).with_suffix("").as_posix().replace("/", ".")
        if any(rel.endswith(ex) for ex in exclude):
            continue
        hits.extend(module_imports(rel, forbidden))
    return hits
