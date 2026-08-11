"""Metadata tests: semver validation, fields, make_component_metadata."""

import pytest
from pydantic import ValidationError

from aios_core.metadata import AiOSMetadata, make_component_metadata


def test_valid_semver_versions():
    for version in ("1.0.0", "1.0.0-beta.1", "1.0.0-beta.1+build.5", "0.1.0", "10.20.30-alpha+build"):
        AiOSMetadata(
            id="x", name="x", version=version, author="a", license="MIT"
        )


def test_invalid_semver_versions():
    for version in ("1.0", "1", "1.0.0.0", "v1.0.0", "1.0.0-", "1.0.0+"):
        with pytest.raises(ValidationError):
            AiOSMetadata(
                id="x", name="x", version=version, author="a", license="MIT"
            )


def test_updated_ge_created():
    with pytest.raises(ValidationError):
        AiOSMetadata(
            id="x",
            name="x",
            version="1.0.0",
            author="a",
            license="MIT",
            created="2026-01-01T00:00:00Z",
            updated="2025-01-01T00:00:00Z",
        )


def test_timestamps_aware_utc():
    m = AiOSMetadata(id="x", name="x", version="1.0.0", author="a", license="MIT")
    assert m.created.tzinfo is not None
    assert m.updated.tzinfo is not None


def test_defaults():
    m = AiOSMetadata(id="x", name="x", version="1.0.0", author="a", license="MIT")
    assert m.dependencies == []
    assert m.permissions == []
    assert m.tags == []
    assert m.health is None
    assert m.checksum is None


def test_make_component_metadata_defaults():
    m = make_component_metadata(id="tool-x", name="tool-x", version="0.1.0")
    assert m.author == "AIOS"
    assert m.license == "MIT"
    assert m.checksum is None
    assert m.health is None
    assert m.dependencies == []


def test_make_component_metadata_created_override():
    import datetime

    created = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    m = make_component_metadata(id="t", name="t", version="0.1.0", created=created)
    assert m.created == created
    assert m.updated == created


def test_make_component_metadata_invalid_version():
    with pytest.raises(ValidationError):
        make_component_metadata(id="t", name="t", version="nope")
