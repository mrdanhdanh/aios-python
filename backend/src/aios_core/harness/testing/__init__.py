"""Test & Simulation package (TASK-031, H3)."""

from .contracts import (
    ExpectedResult, Fault, FaultType, Scenario, SimulationOutcome,
    SimulationStatus, TestLevel,
)
from .errors import ScenarioError, SimulationError, TestError
from .faults import FaultInjector, ResourceExhaustedError
from .scenarios import load, load_many
from .simulation import FakeRuntime, FakeTool, SimulationRunner
from .testing import TestHarness

__all__ = [
    "ExpectedResult", "Fault", "FaultType", "Scenario", "SimulationOutcome",
    "SimulationStatus", "TestLevel",
    "ScenarioError", "SimulationError", "TestError",
    "FaultInjector", "ResourceExhaustedError",
    "load", "load_many",
    "FakeRuntime", "FakeTool", "SimulationRunner", "TestHarness",
]
