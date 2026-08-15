"""TASK-047 — Developer Kit (M8-E5) tests."""

import yaml

import pytest

from aios_core.ecosystem import DevKit, DevKitError


def _scaffold(tmp_path, kind="plugin", name="github"):
    created = DevKit().create_scaffold(kind, name, tmp_path)
    root = tmp_path / name
    return root, created


def test_plugin_scaffold_structure(tmp_path):
    root, created = _scaffold(tmp_path)
    assert len(created) == 6
    assert (root / "aios.plugin.yaml").exists()
    assert (root / "src/github/plugin.py").exists()
    assert (root / "src/__init__.py").exists()
    assert (root / "tests/test_scaffold.py").exists()
    assert (root / "README.md").exists()
    assert (root / "pyproject.toml").exists()


def test_manifest_yaml_roundtrip(tmp_path):
    root, _ = _scaffold(tmp_path)
    manifest = yaml.safe_load((root / "aios.plugin.yaml").read_text(encoding="utf-8"))
    assert manifest["id"] == "github.plugin"
    assert manifest["version"] == "0.1.0"
    assert manifest["aios"]["min"] == "1.0.0"
    assert manifest["aios"]["max"] == "2.x"
    assert manifest["plugin_type"] == "integration"
    assert manifest["provides"][0]["id"] == "github.plugin"


def test_stub_compiles(tmp_path):
    root, _ = _scaffold(tmp_path, kind="agent", name="reviewer")
    source = (root / "src/reviewer/plugin.py").read_text(encoding="utf-8")
    compile(source, "plugin.py", "exec")
    assert "from aios import Agent" in source


def test_deterministic(tmp_path):
    root_a, created_a = _scaffold(tmp_path / "a")
    root_b, created_b = _scaffold(tmp_path / "b")
    files_a = sorted(p.relative_to(root_a).as_posix() for p in root_a.rglob("*") if p.is_file())
    files_b = sorted(p.relative_to(root_b).as_posix() for p in root_b.rglob("*") if p.is_file())
    assert files_a == files_b
    for rel in files_a:
        assert (root_a / rel).read_bytes() == (root_b / rel).read_bytes()


def test_no_overwrite(tmp_path):
    root, _ = _scaffold(tmp_path)
    (root / "README.md").write_text("keep", encoding="utf-8")
    with pytest.raises(DevKitError, match="overwrite"):
        DevKit().create_scaffold("plugin", "github", tmp_path)
    assert (root / "README.md").read_text(encoding="utf-8") == "keep"


def test_invalid_kind_and_name(tmp_path):
    with pytest.raises(DevKitError, match="unknown kind"):
        DevKit().create_scaffold("bogus", "x", tmp_path)
    with pytest.raises(DevKitError, match="invalid name"):
        DevKit().create_scaffold("plugin", "My Plugin", tmp_path)


def test_all_kinds(tmp_path):
    for kind in ("plugin", "agent", "capability", "tool", "workflow"):
        root, _ = _scaffold(tmp_path / kind, kind=kind, name="sample")
        assert (root / "aios.plugin.yaml").exists()
