"""Semver parsing and comparison helpers.

Precedence follows the official semver spec (https://semver.org), including
numeric ordering of pre-release identifiers (e.g. ``alpha.10 > alpha.2``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .metadata import SEMVER_RE


@dataclass(frozen=True)
class VersionInfo:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = field(default_factory=tuple)
    build: str | None = None

    def __str__(self) -> str:
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            base += "-" + ".".join(self.prerelease)
        if self.build:
            base += "+" + self.build
        return base


def parse_version(version: str) -> VersionInfo:
    """Parse a semver string into a VersionInfo.

    Raises:
        ValueError: if the string is not valid semver.
    """
    match = SEMVER_RE.match(version)
    if not match:
        raise ValueError(f"Invalid semver: {version!r}")
    major, minor, patch, prerelease, build = match.groups()
    return VersionInfo(
        major=int(major),
        minor=int(minor),
        patch=int(patch),
        prerelease=tuple(prerelease.split(".")) if prerelease else (),
        build=build,
    )


def _prerelease_key(identifiers: tuple[str, ...]) -> tuple[int, tuple[tuple[int, str], ...]]:
    """Key for semver pre-release precedence (numeric identifiers sort lower)."""
    parts: list[tuple[int, str]] = []
    for ident in identifiers:
        if ident.isdigit():
            parts.append((0, str(int(ident)).zfill(10)))  # numeric: sort numerically
        else:
            parts.append((1, ident))  # alphanumeric: sort lexically
    return len(parts), tuple(parts)


def compare(a: str, b: str) -> int:
    """Compare two semver strings. Returns -1, 0, or 1.

    Raises:
        ValueError: if either string is not valid semver.
    """
    va, vb = parse_version(a), parse_version(b)
    if (va.major, va.minor, va.patch) != (vb.major, vb.minor, vb.patch):
        return -1 if (va.major, va.minor, va.patch) < (vb.major, vb.minor, vb.patch) else 1
    # Same core version: pre-release versions sort lower than releases.
    if va.prerelease == vb.prerelease:
        return 0
    if not va.prerelease:
        return 1
    if not vb.prerelease:
        return -1
    return -1 if _prerelease_key(va.prerelease) < _prerelease_key(vb.prerelease) else 1
