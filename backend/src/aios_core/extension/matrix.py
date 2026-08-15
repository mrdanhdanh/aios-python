"""Compatibility Matrix (TASK-045, M8-E3).

Pure functions — no state, no god object. Fail-closed: a missing runtime
contract or an unsatisfied requirement is an error, never silently allowed.
Supported constraints:
    "*"        any version
    "1.8.0"    exact version
    ">=1.8.0"  at least
    "^2.0"     major pinned (>=2.0.0 <3.0.0)
    "~1.9"     pessimistic (>=1.9 <2.0) — warning (deprecated)
"""

from __future__ import annotations

import re

from ..semver import VersionInfo, compare, parse_version
from .contracts import ApiNamespace, CompatibilityResult
from .errors import CompatibilityViolation, ExtensionError

_CONSTRAINT_RE = re.compile(r"^(\^|>=|~)?(\d+)(?:\.(\d+))?(?:\.(\d+))?$|^\*$")


def parse_constraint(raw: str) -> tuple[str, VersionInfo]:
    """Return (operator, version). Raises ExtensionError on malformed input."""
    raw = (raw or "*").strip()
    if raw == "*":
        return "*", VersionInfo(0, 0, 0)
    match = _CONSTRAINT_RE.match(raw)
    if not match or (match.group(0) != raw):
        raise ExtensionError(f"invalid constraint: {raw!r}")
    op = match.group(1) or "="
    major = int(match.group(2))
    minor = int(match.group(3) or 0)
    patch = int(match.group(4) or 0)
    return op, VersionInfo(major, minor, patch)


def _matches(op: str, have: VersionInfo, want: VersionInfo) -> tuple[bool, str | None]:
    cmp_have_want = compare(str(have), str(want))
    if op == "*":
        return True, None
    if op == "=":
        return cmp_have_want == 0, None
    if op == ">=":
        return cmp_have_want >= 0, None
    if op == "^":
        ok = cmp_have_want >= 0 and have.major == want.major
        return ok, None
    if op == "~":
        ok = cmp_have_want >= 0 and have.major == want.major
        return ok, "constraint '~' is deprecated — use '^' or '>='"
    raise ExtensionError(f"unknown operator: {op!r}")


def check_requires(
    requires: list[dict] | None,
    runtime_versions: dict[str, str],
    allowed_namespaces: list[str] | None = None,
) -> CompatibilityResult:
    """Validate requirements against runtime contract versions.

    ``requires`` is a list of ``{contract, constraint}`` dicts (or
    ``ContractRequirement`` objects). Fail-closed: unknown/missing contract or
    unsatisfied constraint -> error.
    """
    errors: list[str] = []
    warnings: list[str] = []
    for req in requires or []:
        if isinstance(req, dict):
            contract = req.get("contract")
            constraint = req.get("constraint")
        else:
            contract = getattr(req, "contract", None)
            constraint = getattr(req, "constraint", None)
        if not contract or not constraint:
            errors.append(f"malformed requirement: {req!r}")
            continue
        if contract not in runtime_versions:
            errors.append(f"missing runtime contract: {contract}")
            continue
        try:
            op, want = parse_constraint(str(constraint))
        except ExtensionError as exc:
            errors.append(f"{contract}: {exc}")
            continue
        have = parse_version(str(runtime_versions[contract]))
        ok, note = _matches(op, have, want)
        if note:
            warnings.append(f"{contract}: {note}")
        if not ok:
            errors.append(f"{contract}: constraint {constraint!r} not satisfied (runtime {have})")
    return CompatibilityResult(ok=not errors, errors=errors, warnings=warnings)


def assert_namespace_allowed(namespace: ApiNamespace | str, allowed: list[str] | None) -> None:
    """Raise CompatibilityViolation when namespace is outside the allow list."""
    if allowed is None:
        return
    value = namespace.value if isinstance(namespace, ApiNamespace) else namespace
    if value not in allowed:
        raise CompatibilityViolation(f"namespace {value!r} not in allowed: {sorted(allowed)}")


__all__ = ["assert_namespace_allowed", "check_requires", "parse_constraint"]
