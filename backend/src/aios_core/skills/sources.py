"""Skill sources — deterministic stubs for zip/git/pip (TASK-015).

No downloads, no git/pip/network: each loader returns a fixed manifest dict
from its own fixtures. Ref semantics (C1-19): empty ref = invalid input ->
ValueError; unknown ref = not found -> SkillError.
"""

from __future__ import annotations

from .base import SkillManifest, SkillSource
from .errors import SkillError

# Fixtures: metadata omitted (C2-07 — determinism across runs).
_ZIP_FIXTURES: dict[str, dict] = {
    "demo-pack": {
        "id": "skill.demo_zip",
        "name": "Demo Zip Skill",
        "version": "1.0.0",
        "source": "zip",
        "description": "demo zip skill",
        "dependencies": [],
        "capabilities": ["demo_cap"],
        "permissions": ["filesystem"],
    },
}
_GIT_FIXTURES: dict[str, dict] = {
    "https://github.com/aios/demo-skill": {
        "id": "skill.demo_git",
        "name": "Demo Git Skill",
        "version": "1.0.0",
        "source": "git",
        "description": "demo git skill",
        "dependencies": ["skill.demo_zip@>=1.0.0"],
        "capabilities": ["demo_git_cap"],
        "permissions": [],
    },
}
_PIP_FIXTURES: dict[str, dict] = {
    "aios-demo-skill": {
        "id": "skill.demo_pip",
        "name": "Demo Pip Skill",
        "version": "1.0.0",
        "source": "pip",
        "description": "demo pip skill",
        "dependencies": [],
        "capabilities": ["demo_pip_cap"],
        "permissions": ["network"],
    },
}

_ALL_FIXTURES: dict[SkillSource, dict[str, dict]] = {
    SkillSource.ZIP: _ZIP_FIXTURES,
    SkillSource.GIT: _GIT_FIXTURES,
    SkillSource.PIP: _PIP_FIXTURES,
}


class _BaseSource:
    source: SkillSource

    def __init__(self, fixtures: dict[str, dict] | None = None) -> None:
        self._fixtures = fixtures if fixtures is not None else _ALL_FIXTURES[self.source]

    def load(self, ref: str) -> dict:
        if not ref or not ref.strip():
            raise ValueError("ref must not be empty")  # C1-19: invalid input
        manifest = self._fixtures.get(ref)
        if manifest is None:
            raise SkillError(f"unknown {self.source.value} ref: {ref!r}")  # C1-19: not found
        return dict(manifest)


class ZipSource(_BaseSource):
    source = SkillSource.ZIP


class GitSource(_BaseSource):
    source = SkillSource.GIT


class PipSource(_BaseSource):
    source = SkillSource.PIP


def build_default_sources() -> dict[SkillSource, object]:
    return {
        SkillSource.ZIP: ZipSource(),
        SkillSource.GIT: GitSource(),
        SkillSource.PIP: PipSource(),
    }


def make_manifest(source: SkillSource, ref: str) -> SkillManifest:
    fixtures = _ALL_FIXTURES[source]
    if ref not in fixtures:
        raise SkillError(f"unknown {source.value} ref: {ref!r}")
    return SkillManifest.validate_manifest(**dict(fixtures[ref]))
