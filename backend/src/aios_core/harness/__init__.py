"""AIOS Harness kernel (TASK-029, H1): contracts, lifecycle, registry, runner."""

from .context import HarnessContext
from .contracts import (
    HarnessArtifact,
    HarnessEvent,
    HarnessReport,
    HarnessResult,
    HarnessRun,
    HarnessRunStatus,
    safe_run_id,
    utcnow,
)
from .errors import (
    HarnessError,
    HarnessHookError,
    HarnessLifecycleError,
    HarnessNotFoundError,
    HarnessRegistrationError,
)
from .lifecycle import HarnessLifecycle, TRANSITIONS
from .registry import Harness, HarnessRegistry
from .runner import HarnessRunner

__all__ = [
    "Harness",
    "HarnessArtifact",
    "HarnessContext",
    "HarnessError",
    "HarnessEvent",
    "HarnessHookError",
    "HarnessLifecycle",
    "HarnessLifecycleError",
    "HarnessNotFoundError",
    "HarnessRegistrationError",
    "HarnessRegistry",
    "HarnessReport",
    "HarnessResult",
    "HarnessRun",
    "HarnessRunner",
    "HarnessRunStatus",
    "TRANSITIONS",
    "safe_run_id",
    "utcnow",
]
