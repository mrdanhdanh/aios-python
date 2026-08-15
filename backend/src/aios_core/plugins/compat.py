"""AIOS compatibility range check (TASK-044, M8-E2).

Supports the PLAN §M8-E2 example: ``aiOS: { min: 1.8.0, max: 2.x }``.
Constraints are parsed fail-fast; ``*`` matches any version, ``2.x`` matches
every 2.* version, plain semver matches exactly that version or newer for
``min`` semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..semver import VersionInfo, parse_version
from .errors import PluginCompatibilityError


@dataclass(frozen=True)
class Constraint:
    raw: str
    major: int | None = None
    minor: int | None = None
    patch: int | None = None

    def matches(self, version: VersionInfo) -> bool:
        if self.raw == "*":
            return True
        if self.major is not None and version.major != self.major:
            return False
        if self.minor is not None and version.minor != self.minor:
            return False
        if self.patch is not None and version.patch != self.patch:
            return False
        return True


def parse_constraint(raw: str) -> Constraint:
    """Parse '2.x' | '2.1.3' | '*' | '1.8.0'. Raises PluginCompatibilityError."""
    raw = (raw or "*").strip()
    if raw == "*":
        return Constraint(raw=raw)
    if raw.endswith(".x"):
        core = raw[:-2]
        parts = core.split(".")
        if len(parts) not in (1, 2) or not all(p.isdigit() for p in parts):
            raise PluginCompatibilityError(f"invalid aios constraint: {raw!r}")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) == 2 else None
        return Constraint(raw=raw, major=major, minor=minor)
    try:
        parsed = parse_version(raw)
    except ValueError:
        raise PluginCompatibilityError(f"invalid aios constraint: {raw!r}") from None
    return Constraint(raw=raw, major=parsed.major, minor=parsed.minor, patch=parsed.patch)


def _within_min(parsed: VersionInfo, lo: Constraint) -> bool:
    if lo.raw == "*":
        return True
    if lo.major is not None:
        if parsed.major < lo.major:
            return False
        if parsed.major > lo.major:
            return True
        if lo.minor is not None:
            if parsed.minor < lo.minor:
                return False
            if parsed.minor > lo.minor:
                return True
            if lo.patch is not None and parsed.patch < lo.patch:
                return False
    return True


def _within_max(parsed: VersionInfo, hi: Constraint) -> bool:
    if hi.raw == "*":
        return True
    if hi.major is not None:
        if parsed.major > hi.major:
            return False
        if parsed.major < hi.major:
            return True
        # same major
        if hi.minor is None:  # "2.x" → any 2.*
            return True
        if parsed.minor > hi.minor:
            return False
        if parsed.minor < hi.minor:
            return True
        if hi.patch is None:  # "2.1.x"
            return True
        return parsed.patch <= hi.patch
    return True


def check_compatibility(min_constraint: str, max_constraint: str, aios_version: str) -> bool:
    """True when aios_version falls inside [min, max]."""
    parsed = parse_version(aios_version)
    lo = parse_constraint(min_constraint)
    hi = parse_constraint(max_constraint)
    return _within_min(parsed, lo) and _within_max(parsed, hi)
