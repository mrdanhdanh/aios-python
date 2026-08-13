"""AIOS Sandbox Pool (TASK-015) — reusable mock sandboxes per language."""

from .errors import SandboxPoolError
from .pool import Sandbox, SandboxPool, SandboxResult, SandboxState

__all__ = [
    "SandboxPoolError",
    "Sandbox",
    "SandboxPool",
    "SandboxResult",
    "SandboxState",
    "build_sandbox_pool",
]


def build_sandbox_pool(max_size: int = 4, idle_timeout_s: float = 300.0) -> SandboxPool:
    return SandboxPool(max_size=max_size, idle_timeout_s=idle_timeout_s)
