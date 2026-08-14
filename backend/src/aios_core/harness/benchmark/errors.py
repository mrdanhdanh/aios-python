"""Benchmark errors (TASK-033, H4)."""


class BenchmarkError(Exception):
    """Benchmark harness failure."""


class GateBlockedError(BenchmarkError):
    """INV-021: regression nghiêm trọng — block release."""
