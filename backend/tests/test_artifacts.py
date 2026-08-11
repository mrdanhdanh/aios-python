"""Artifact service tests: store/load/delete/list + path guard."""

import pytest

from aios_core.contracts import ArtifactContract, ArtifactType
from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import ArtifactCorruptedError, ArtifactService

SHA256_64 = "a" * 64


def _contract(storage_path="reports/r.md", **over):
    data = dict(
        id="art-1",
        name="r",
        version="1.0.0",
        author="AIOS",
        license="MIT",
        contract_version="1.0.0",
        schema_version="1.0.0",
        type=ArtifactType.MARKDOWN,
        storage_path=storage_path,
    )
    data.update(over)
    return ArtifactContract(**data)


@pytest.fixture
def svc(tmp_path):
    return ArtifactService(tmp_path / "artifacts", EventBus())


def test_store_writes_file_and_sidecar_and_emits(tmp_path):
    bus = EventBus()
    received = []
    bus.subscribe(EventType.ARTIFACT_CREATED, lambda ev: received.append(ev))
    svc = ArtifactService(tmp_path / "artifacts", bus)
    contract = _contract()
    result = svc.store(contract, b"hello")
    assert (tmp_path / "artifacts" / "reports" / "r.md").is_file()
    assert (tmp_path / "artifacts" / "reports" / "r.md.aios.json").is_file()
    assert len(received) == 1
    assert received[0].payload["artifact"]["id"] == "art-1"
    assert result.checksum is not None
    assert len(result.checksum) == 64


def test_store_base_dir_auto_created(tmp_path):
    svc = ArtifactService(tmp_path / "nested" / "artifacts", EventBus())
    svc.store(_contract(), b"x")
    assert (tmp_path / "nested" / "artifacts" / "reports" / "r.md").is_file()


def test_store_recomputes_checksum_and_refreshes_updated(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    contract = _contract()
    contract.checksum = SHA256_64  # stale checksum
    result = svc.store(contract, b"new-content")
    assert result.checksum != SHA256_64
    assert result.updated >= result.created


def test_load_roundtrip(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    svc.store(_contract(), b"payload")
    assert svc.load(_contract()) == b"payload"


def test_load_checksum_mismatch_raises(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    svc.store(_contract(), b"payload")
    with pytest.raises(ArtifactCorruptedError):
        svc.load(_contract(checksum=SHA256_64))  # wrong checksum


def test_load_missing_file_raises(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    with pytest.raises(FileNotFoundError):
        svc.load(_contract())


def test_delete_removes_file_and_sidecar(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    svc.store(_contract(), b"x")
    svc.delete(_contract())
    assert not (tmp_path / "artifacts" / "reports" / "r.md").exists()
    assert not (tmp_path / "artifacts" / "reports" / "r.md.aios.json").exists()
    svc.delete(_contract())  # idempotent


def test_list_filters_by_type(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    svc.store(_contract(storage_path="a.md"), b"1")
    svc.store(_contract(storage_path="b.json", id="art-2", name="b", type=ArtifactType.JSON), b"{}")
    all_artifacts = svc.list()
    assert len(all_artifacts) == 2
    json_only = svc.list(artifact_type=ArtifactType.JSON)
    assert len(json_only) == 1
    assert json_only[0].type == ArtifactType.JSON


def test_list_skips_corrupt_sidecar(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    svc.store(_contract(storage_path="ok.md"), b"1")
    corrupt = tmp_path / "artifacts" / "bad.md.aios.json"
    corrupt.write_text("{not-json", encoding="utf-8")
    result = svc.list()
    assert len(result) == 1  # corrupt sidecar skipped, no crash


def test_list_base_dir_missing_returns_empty(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    assert svc.list() == []


def test_path_guard_traversal(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    with pytest.raises(ValueError, match="escapes"):
        svc.store(_contract(storage_path="../outside.md"), b"x")
    with pytest.raises(ValueError, match="escapes"):
        svc.load(_contract(storage_path="../outside.md"))


def test_path_guard_sibling_prefix(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    sibling = tmp_path / "artifacts2"
    sibling.mkdir()
    evil = str(sibling / "evil.md")
    with pytest.raises(ValueError, match="escapes"):
        svc.store(_contract(storage_path=evil), b"x")


def test_path_guard_absolute_outside(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    outside = str(tmp_path / "elsewhere" / "f.md")
    with pytest.raises(ValueError, match="escapes"):
        svc.store(_contract(storage_path=outside), b"x")


def test_relative_path_inside_base_ok(tmp_path):
    svc = ArtifactService(tmp_path / "artifacts", EventBus())
    svc.store(_contract(storage_path="sub/dir/f.md"), b"x")
    assert (tmp_path / "artifacts" / "sub" / "dir" / "f.md").is_file()
