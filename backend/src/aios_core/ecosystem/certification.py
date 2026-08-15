"""Certification (TASK-049, M8-E7).

Plugin states: COMMUNITY → VERIFIED → CERTIFIED → ENTERPRISE_CERTIFIED.
Harness is the gate: any failed check keeps the plugin at COMMUNITY with a
report. Six default check groups (PLAN §M8-E7): contract, behavior, security,
permission, compatibility, performance — each produces evidence (INV-018
spirit). The engine only orchestrates; checks are injectable.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from ..semver import parse_version
from .errors import CertificationError

CheckFn = Callable[[dict], tuple[bool, str]]  # (manifest) -> (passed, evidence)


class CertLevel(str, Enum):
    COMMUNITY = "community"
    VERIFIED = "verified"
    CERTIFIED = "certified"
    ENTERPRISE_CERTIFIED = "enterprise_certified"


class CertCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    passed: bool
    evidence: str


class CertReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    level: CertLevel = CertLevel.COMMUNITY
    checks: list[CertCheck] = Field(default_factory=list)
    passed: int = 0
    failed: int = 0
    threshold: float = 1.0


# -- default checks ------------------------------------------------------------

def _check_contract(manifest: dict) -> tuple[bool, str]:
    missing = [field for field in ("id", "version", "name") if not manifest.get(field)]
    if missing:
        return False, f"missing manifest fields: {missing}"
    try:
        parse_version(str(manifest["version"]))
    except ValueError:
        return False, f"invalid semver: {manifest['version']!r}"
    return True, f"contract fields ok (id={manifest['id']}, version={manifest['version']})"


def _check_behavior(manifest: dict) -> tuple[bool, str]:
    # Behavior is verified by the Harness runner — v1 records intent only.
    return True, "behavior harness not configured for this plugin"


def _check_security(manifest: dict) -> tuple[bool, str]:
    permissions = manifest.get("permissions") or []
    if any(perm == "*" for perm in permissions):
        return False, "wildcard permission '*' is not allowed"
    return True, f"permissions scoped: {sorted(permissions)}"


def _check_permission(manifest: dict) -> tuple[bool, str]:
    permissions = manifest.get("permissions") or []
    if not permissions:
        return False, "no permissions declared — required for certification"
    return True, f"permissions declared: {sorted(permissions)}"


def _check_compatibility(manifest: dict) -> tuple[bool, str]:
    aios = manifest.get("aios") or {}
    lo, hi = aios.get("min", "0.0.0"), aios.get("max", "*")
    if not isinstance(lo, str) or not isinstance(hi, str):
        return False, "aios range must be strings"
    return True, f"aios range declared: {lo}..{hi}"


def _check_performance(manifest: dict) -> tuple[bool, str]:
    return True, "performance benchmark not configured for this plugin"


def default_checks() -> list[tuple[str, CheckFn]]:
    """Six check groups in PLAN order — deterministic."""
    return [
        ("contract", _check_contract),
        ("behavior", _check_behavior),
        ("security", _check_security),
        ("permission", _check_permission),
        ("compatibility", _check_compatibility),
        ("performance", _check_performance),
    ]


class CertificationEngine:
    """Pure orchestrator — checks injectable, output deterministic."""

    def __init__(
        self,
        checks: list[tuple[str, CheckFn]] | None = None,
        threshold: float = 1.0,
    ) -> None:
        if threshold < 0.0 or threshold > 1.0:
            raise CertificationError("threshold must be within [0, 1]")
        self._checks = list(checks) if checks is not None else list(default_checks())
        if not self._checks:
            raise CertificationError("at least one check is required")
        self._threshold = threshold

    def certify(self, manifest: dict) -> CertReport:
        """Run all checks; any fail → COMMUNITY; security fail hard-blocks
        CERTIFIED+. Never mutates the input manifest."""
        report = CertReport(threshold=self._threshold)
        for name, fn in sorted(self._checks, key=lambda item: item[0]):
            try:
                passed, evidence = fn(manifest)
            except Exception as exc:  # noqa: BLE001 — a broken check must not crash
                passed, evidence = False, f"check raised: {exc}"
            report.checks.append(CertCheck(name=name, passed=passed, evidence=evidence))
            if passed:
                report.passed += 1
            else:
                report.failed += 1
        total = len(report.checks)
        ratio = (report.passed / total) if total else 0.0
        security_failed = any(
            check.name == "security" and not check.passed for check in report.checks
        )
        if ratio >= self._threshold and report.failed == 0:
            report.level = CertLevel.VERIFIED
        if report.level == CertLevel.VERIFIED and not security_failed:
            report.level = CertLevel.CERTIFIED
        publisher = manifest.get("publisher")
        signature = manifest.get("signature")
        if (
            report.level == CertLevel.CERTIFIED
            and isinstance(publisher, dict)
            and publisher.get("id")
            and signature
        ):
            report.level = CertLevel.ENTERPRISE_CERTIFIED
        return report


__all__ = [
    "CertLevel",
    "CertReport",
    "CertificationEngine",
    "default_checks",
]
