"""Meta-Harness package (M13-P2, TASK-091).

Verify the verifier — independent oracle (chống circular) + adversarial
fail-closed. Tái dùng public verification API (KHÔNG sửa verifier production).
"""

from .contracts import (
    MetaCase,
    MetaCaseResult,
    MetaOracle,
    MetaReport,
    MetaStatus,
)
from .engine import MetaHarnessEngine
from .errors import MetaError
from .harness import MetaHarness

__all__ = [
    "MetaCase",
    "MetaCaseResult",
    "MetaOracle",
    "MetaReport",
    "MetaStatus",
    "MetaHarnessEngine",
    "MetaError",
    "MetaHarness",
]
