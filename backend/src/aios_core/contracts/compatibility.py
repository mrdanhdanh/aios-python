"""Compatibility checking between contract versions."""

from __future__ import annotations

from dataclasses import dataclass

from ..semver import VersionInfo, compare, parse_version


@dataclass(frozen=True)
class CompatibilityResult:
    compatible: bool
    breaking: bool
    reason: str


class CompatibilityChecker:
    """Semver compatibility rules for AIOS components.

    ``is_compatible(installed, required)``: ``required`` is the version a
    component declares it needs; ``installed`` is what the runtime has.
    """

    @staticmethod
    def is_compatible(installed: str, required: str) -> bool:
        vi = parse_version(installed)
        vr = parse_version(required)

        # Rule 1: differing pre-release state → incompatible (both directions).
        if bool(vr.prerelease) != bool(vi.prerelease):
            return False

        # Rule 2: required newer than installed → incompatible.
        if compare(required, installed) > 0:
            return False

        # Rule 3: required major < installed major → incompatible (strict policy).
        if vr.major < vi.major:
            return False

        # Rule 4: 0.x — compatible iff same major.minor (patch ignored).
        if vi.major == 0:
            return vr.major == 0 and vr.minor == vi.minor

        # Rule 5: otherwise compatible.
        return True

    @staticmethod
    def check_upgrade(old: str, new: str) -> CompatibilityResult:
        """Check whether upgrading from ``old`` to ``new`` is safe.

        ``compatible`` mirrors ``is_compatible(installed=new, required=old)``
        (parameters reversed — the component was built against ``old``).
        """
        vo = parse_version(old)
        vn = parse_version(new)

        compatible = CompatibilityChecker.is_compatible(installed=new, required=old)
        breaking = (vn.major != vo.major) or (vn.major == 0 and vn.minor != vo.minor)

        if not compatible:
            reason = _reason(old, new, vo, vn)
        else:
            reason = f"Upgrade {old} -> {new} is backward-compatible"
        return CompatibilityResult(compatible=compatible, breaking=breaking, reason=reason)


def _reason(old: str, new: str, vo: VersionInfo, vn: VersionInfo) -> str:
    if not CompatibilityChecker.is_compatible(installed=new, required=old):
        # Mirror the rules for a human-readable reason.
        if bool(vn.prerelease) != bool(vo.prerelease):
            return f"Pre-release state differs: {old} vs {new}"
        if compare(old, new) > 0:
            return f"Required {old} has higher precedence than installed {new}"
        if vo.major < vn.major:
            return f"Required major {vo.major} < installed major {vn.major} (strict policy)"
        if vn.major == 0 and vo.minor != vn.minor:
            return f"0.x minor bump {old} -> {new} is breaking"
        if vn.major == 0 and vo.major != 0:
            return f"0.x incompatibility: {old} vs {new}"
        return f"Upgrade {old} -> {new} is not compatible"
    return f"Upgrade {old} -> {new} is not compatible"
