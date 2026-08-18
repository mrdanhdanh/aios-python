"""DSH Bridge module (M16, TASK-104..108): independent verification oracle."""

from .contracts import DSHConfig, DSHStatus, InvariantResult, OracleReport
from .engine import DSHBridgeEngine
from .errors import DSHBridgeError
from .harness import DSHBridgeHarness

__all__ = [
    "DSHConfig", "DSHStatus", "InvariantResult", "OracleReport",
    "DSHBridgeEngine", "DSHBridgeError", "DSHBridgeHarness",
]
