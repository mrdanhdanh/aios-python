"""SkillDistiller — R5 (M11-P4a, TASK-083).

Distill skill package từ repo ngoài (URL) → structure → capability extraction
→ synthesis (SKILL.md + manifest.json) → contract validation → report.
Deterministic, offline-first: FetchFn injectable (default GitHubFetchStub —
hash URL → seed → tree mẫu; không network). Fail-closed (INV-035): fetch
fail / tree rỗng / out_dir có file cũ → SkillDistillError (không file một phần).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

from ..semver import parse_version

#: Keywords capability extraction — mirror CREATIVE_TRIGGERS (R6).
CAPABILITY_KEYWORDS: tuple[str, ...] = (
    "sprite", "pixel", "game", "canvas", "audio", "animation", "map", "tileset",
)

#: SkillSource hợp lệ (mirror skills/base.py — không import để giữ allow-list M8).
_SKILL_SOURCES = ("zip", "git", "pip")

_LICENSE_OK = ("mit", "apache-2.0", "apache 2.0", "apache2")
_LICENSE_WARN = ("", "unknown", "proprietary")

_SKILL_MD_TEMPLATE = """# {name}

Distilled by AIOS SkillDistiller (M11-P4a, R5) from {url}.

## Capabilities
{capabilities}

## Source
- URL: {url}
- Distilled: deterministic (no LLM)
"""


class SkillDistillError(RuntimeError):
    """Fail-closed lỗi distill (INV-035) — không tạo file một phần."""


class SkillDistillReport(BaseModel):
    """Kết quả distill (C2-01)."""

    model_config = ConfigDict(extra="forbid")

    distilled_files: list[str] = []
    capabilities: list[str] = []
    warnings: list[str] = []
    manifest_path: str = ""
    license_status: str = "ok"  # ok | warn


#: Fetch tree — dict[path_str, content_str] (deterministic stub mặc định).
FetchTree = dict[str, str]
FetchFn = Callable[[str], FetchTree]


class GitHubFetchStub:
    """Stub deterministic — hash URL → seed → tree mẫu (C1-01).

    Cùng URL → cùng tree; khác URL → khác skill.
    """

    def __call__(self, url: str) -> FetchTree:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)
        name = f"skill.{digest[:8]}"
        capability = CAPABILITY_KEYWORDS[seed % len(CAPABILITY_KEYWORDS)]
        skill_md = (
            f"# {name}\n\n"
            f"Distilled stub for {url}\n\n"
            f"Specializes in {capability} assets.\n"
        )
        return {
            "SKILL.md": skill_md,
            "src/__init__.py": f'""" {name} — stub source. """\n',
            "src/generate.py": f'"""Generate {capability} assets (stub). """\n',
            "tests/test_generate.py": "def test_generate():\n    assert True\n",
        }


class SkillDistiller:
    """Pipeline 7 bước deterministic (R5)."""

    def __init__(self, fetcher: FetchFn | None = None) -> None:
        self._fetcher = fetcher or GitHubFetchStub()

    # -- pipeline -------------------------------------------------------------

    def distill(
        self,
        url: str,
        out_dir: str | Path,
        fetcher: FetchFn | None = None,
    ) -> SkillDistillReport:
        f = fetcher or self._fetcher
        # Bước 1: fetch (fail → fail-closed)
        try:
            tree = f(url)
        except Exception as exc:  # noqa: BLE001
            raise SkillDistillError(f"fetch failed: {exc}") from exc
        if not tree:
            raise SkillDistillError("tree empty — nothing to distill")
        out = Path(out_dir)
        # Fail-closed: không ghi đè (no-overwrite — C2-01)
        if (out / "SKILL.md").exists() or (out / "manifest.json").exists():
            raise SkillDistillError(f"out_dir already has distilled files: {out}")
        # Bước 2: license
        license_status, warnings = self._license_check(tree)
        # Bước 3: structure scan
        self._structure_check(tree)
        # Bước 4: capability extraction
        capabilities = self._extract_capabilities(tree)
        # Bước 5: synthesis
        name = self._skill_name(url)
        skill_md, manifest = self._synthesize(url, name, capabilities)
        # Bước 6: contract validation (mirror SkillManifest — semver + field checks)
        self._validate_manifest(manifest)  # raise → fail-closed
        # Bước 7: write + report
        out.mkdir(parents=True, exist_ok=True)
        (out / "SKILL.md").write_text(skill_md, encoding="utf-8")
        (out / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return SkillDistillReport(
            distilled_files=["SKILL.md", "manifest.json"],
            capabilities=capabilities,
            warnings=warnings,
            manifest_path=str(out / "manifest.json"),
            license_status=license_status,
        )

    # -- steps ----------------------------------------------------------------

    def _license_check(self, tree: FetchTree) -> tuple[str, list[str]]:
        license_file = tree.get("LICENSE") or tree.get("LICENSE.md") or ""
        lowered = license_file.lower()
        if any(mark in lowered for mark in _LICENSE_OK):
            return "ok", []
        return "warn", ["no LICENSE found — verify before distribution"]

    def _structure_check(self, tree: FetchTree) -> None:
        if "SKILL.md" not in tree:
            raise SkillDistillError("SKILL.md missing in tree")

    def _extract_capabilities(self, tree: FetchTree) -> list[str]:
        haystack = " ".join(tree.values()).lower()
        found = [kw for kw in CAPABILITY_KEYWORDS if kw in haystack]
        return sorted(dict.fromkeys(found))

    def _skill_name(self, url: str) -> str:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        return f"skill.{digest}"

    def _synthesize(
        self, url: str, name: str, capabilities: list[str],
    ) -> tuple[str, dict[str, Any]]:
        cap_lines = "\n".join(f"- {c}" for c in capabilities) or "- (none)"
        skill_md = _SKILL_MD_TEMPLATE.format(
            name=name, url=url, capabilities=cap_lines,
        )
        manifest: dict[str, Any] = {
            "id": name,
            "name": f"Distilled {name}",
            "version": "1.0.0",
            "source": "zip",
            "description": f"Distilled from {url} (M11-P4a R5)",
            "dependencies": [],
            "capabilities": [f"asset:{c}" for c in capabilities],
            "permissions": ["filesystem"],
        }
        return skill_md, manifest

    # -- contract validation (mirror SkillManifest rules, không import skills) -

    def _validate_manifest(self, manifest: dict[str, Any]) -> None:
        """Validate manifest theo contract SkillManifest (semver + fields).

        Không import aios_core.skills (allow-list M8 ecosystem chỉ cho
        semver/metadata) — mirror rules để fail-closed.
        """
        if not str(manifest.get("id", "")).strip():
            raise SkillDistillError("manifest: id must not be empty")
        if not str(manifest.get("name", "")).strip():
            raise SkillDistillError("manifest: name must not be empty")
        try:
            parse_version(str(manifest.get("version", "")))
        except ValueError:
            raise SkillDistillError(
                f"manifest: invalid semver version: {manifest.get('version')!r}"
            ) from None
        source = manifest.get("source", "")
        if source not in _SKILL_SOURCES:
            raise SkillDistillError(f"manifest: unknown source: {source!r}")
        for dep in manifest.get("dependencies", []):
            if not str(dep).strip():
                raise SkillDistillError("manifest: dependency must not be empty")
        for cap in manifest.get("capabilities", []):
            if not str(cap).strip():
                raise SkillDistillError("manifest: capability must not be empty")
