"""Test & Simulation errors (TASK-031, H3)."""


class ScenarioError(Exception):
    """Scenario load/validate failure."""


class SimulationError(Exception):
    """Simulation runner failure (fault không recover)."""


class TestError(Exception):
    """TestHarness verification failure (MISMATCH/ERROR)."""
