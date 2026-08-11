"""AIOS core package: config, logging, metadata, healthcheck."""

__version__ = "0.1.0"

from .config import Settings, load_settings
from .healthcheck import (
    HealthCheck,
    HealthRegistry,
    HealthReport,
    HealthStatus,
)
from .logging import get_logger, set_correlation_id, setup_logging
from .metadata import AiOSMetadata, make_component_metadata

__all__ = [
    "__version__",
    "Settings",
    "load_settings",
    "HealthCheck",
    "HealthRegistry",
    "HealthReport",
    "HealthStatus",
    "get_logger",
    "set_correlation_id",
    "setup_logging",
    "AiOSMetadata",
    "make_component_metadata",
]
