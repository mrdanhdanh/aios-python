"""Import smoke tests: package imports, version, exports."""

import re

import aios_core


def test_version_is_semver():
    assert re.match(r"^\d+\.\d+\.\d+", aios_core.__version__)


def test_exports_present():
    for name in (
        "get_logger",
        "setup_logging",
        "AiOSMetadata",
        "make_component_metadata",
        "HealthStatus",
        "HealthReport",
        "HealthCheck",
        "HealthRegistry",
        "Settings",
        "load_settings",
        "__version__",
    ):
        assert hasattr(aios_core, name), f"missing export: {name}"
