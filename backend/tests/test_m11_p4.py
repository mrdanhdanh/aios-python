"""Tests M11-P4a/b — R5 SkillDistiller + R7 Static Deploy (TASK-083)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aios_core.ecosystem.deploy import StaticDeploy
from aios_core.ecosystem.distiller import (
    GitHubFetchStub,
    SkillDistillError,
    SkillDistiller,
)
from aios_core.skills.base import SkillManifest


# -- AC1/AC4/AC5: R5 SkillDistiller -------------------------------------------

def test_r5_distill_report(tmp_path: Path):
    report = SkillDistiller().distill("https://github.com/aios/demo-sprite", tmp_path)
    assert report.distilled_files == ["SKILL.md", "manifest.json"]
    assert report.license_status == "warn"  # stub không có LICENSE
    assert (tmp_path / "SKILL.md").exists()
    assert (tmp_path / "manifest.json").exists()


def test_r5_manifest_valid(tmp_path: Path):
    report = SkillDistiller().distill("https://github.com/aios/demo-sprite", tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    # Contract validation pass
    parsed = SkillManifest.validate_manifest(**manifest)
    assert parsed.id == manifest["id"]
    assert parsed.version == "1.0.0"
    assert parsed.source.value == "zip"
    assert report.manifest_path == str(tmp_path / "manifest.json")


def test_r5_capability_extraction_deterministic(tmp_path: Path):
    url = "https://github.com/aios/demo-sprite"
    d1 = SkillDistiller().distill(url, tmp_path / "a")
    d2 = SkillDistiller().distill(url, tmp_path / "b")
    assert d1.capabilities == d2.capabilities


def test_r5_different_url_different_skill(tmp_path: Path):
    url_a = "https://github.com/aios/sprite-gen"
    url_b = "https://github.com/aios/audio-gen"
    ra = SkillDistiller().distill(url_a, tmp_path / "a")
    rb = SkillDistiller().distill(url_b, tmp_path / "b")
    ma = json.loads((tmp_path / "a" / "manifest.json").read_text(encoding="utf-8"))
    mb = json.loads((tmp_path / "b" / "manifest.json").read_text(encoding="utf-8"))
    assert ma["id"] != mb["id"] or ra.capabilities != rb.capabilities


# -- AC2: license -------------------------------------------------------------

def test_r5_license_ok_when_mit(tmp_path: Path):
    tree = {
        "SKILL.md": "# skill\n",
        "LICENSE": "MIT License\n",
    }

    class _Fetcher:
        def __call__(self, url):  # noqa: ANN001, ANN201
            return tree

    report = SkillDistiller().distill("https://github.com/aios/mit-skill", tmp_path, _Fetcher())
    assert report.license_status == "ok"
    assert report.warnings == []


def test_r5_license_warn_when_missing(tmp_path: Path):
    tree = {"SKILL.md": "# skill\n"}

    class _Fetcher:
        def __call__(self, url):  # noqa: ANN001, ANN201
            return tree

    report = SkillDistiller().distill("https://github.com/aios/no-license", tmp_path, _Fetcher())
    assert report.license_status == "warn"
    assert any("LICENSE" in w for w in report.warnings)


# -- AC3: fail-closed ---------------------------------------------------------

def test_r5_fetch_fail_fail_closed(tmp_path: Path):
    class _Broken:
        def __call__(self, url):  # noqa: ANN001
            raise RuntimeError("network down")

    with pytest.raises(SkillDistillError):
        SkillDistiller().distill("https://github.com/aios/x", tmp_path, _Broken())
    # Không tạo file một phần
    assert not (tmp_path / "SKILL.md").exists()


def test_r5_empty_tree_fail_closed(tmp_path: Path):
    class _Empty:
        def __call__(self, url):  # noqa: ANN001, ANN201
            return {}

    with pytest.raises(SkillDistillError):
        SkillDistiller().distill("https://github.com/aios/x", tmp_path, _Empty())


def test_r5_no_overwrite(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("old", encoding="utf-8")
    with pytest.raises(SkillDistillError):
        SkillDistiller().distill("https://github.com/aios/x", tmp_path)
    assert (tmp_path / "SKILL.md").read_text(encoding="utf-8") == "old"


def test_r5_stub_deterministic():
    url = "https://github.com/aios/skill-a"
    tree1 = GitHubFetchStub()(url)
    tree2 = GitHubFetchStub()(url)
    assert tree1 == tree2
    assert "SKILL.md" in tree1
    assert "src/__init__.py" in tree1


# -- AC7/AC8/AC9: R7 Static Deploy --------------------------------------------

def _site(tmp_path: Path) -> Path:
    root = tmp_path / "site"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text("<h1>hi</h1>", encoding="utf-8")
    (root / "assets" / "a.js").write_text("console.log(1)", encoding="utf-8")
    return root


def test_r7_verify_ok(tmp_path: Path):
    root = _site(tmp_path)
    report = StaticDeploy().verify(root)
    assert report.status == "ok"
    assert report.files == 2
    assert report.total_bytes > 0
    assert len(report.total_sha256) == 64


def test_r7_verify_missing_dir_blocked(tmp_path: Path):
    report = StaticDeploy().verify(tmp_path / "nope")
    assert report.status == "blocked"


def test_r7_verify_empty_dir_blocked(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()
    report = StaticDeploy().verify(empty)
    assert report.status == "blocked"


def test_r7_manifest_deterministic(tmp_path: Path):
    root = _site(tmp_path)
    m1 = StaticDeploy().manifest(root)
    m2 = StaticDeploy().manifest(root)
    assert m1.total_sha256 == m2.total_sha256
    assert m1.files == m2.files


def test_r7_deploy_dry_run_no_files(tmp_path: Path):
    root = _site(tmp_path)
    report = StaticDeploy().deploy(root, dry_run=True)
    assert report.status == "ok"
    assert "dry-run" in report.hint
    assert not (root / ".aios" / "deploy.json").exists()


def test_r7_deploy_apply_writes_marker(tmp_path: Path):
    root = _site(tmp_path)
    report = StaticDeploy().deploy(root, dry_run=False)
    assert report.status == "ok"
    assert report.marker
    marker = json.loads(Path(report.marker).read_text(encoding="utf-8"))
    assert marker["files"] == 2
    assert marker["total_sha256"] == report.total_sha256


def test_r7_deploy_apply_merge_no_overwrite(tmp_path: Path):
    root = _site(tmp_path)
    StaticDeploy().deploy(root, dry_run=False)
    marker_path = root / ".aios" / "deploy.json"
    marker_path.write_text(
        json.dumps({"custom_key": "keep-me", "files": 99}), encoding="utf-8"
    )
    StaticDeploy().deploy(root, dry_run=False)
    merged = json.loads(marker_path.read_text(encoding="utf-8"))
    assert merged["custom_key"] == "keep-me"  # key cũ giữ nguyên
    assert merged["files"] == 2  # key mới ghi đè


def test_r7_deploy_blocked_when_invalid(tmp_path: Path):
    report = StaticDeploy().deploy(tmp_path / "nope", dry_run=False)
    assert report.status == "blocked"
    assert report.marker == ""  # không apply khi verify fail
