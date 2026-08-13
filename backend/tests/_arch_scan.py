"""Shim for tests: re-exports the arch scan engine now living in the runtime
package (TASK-021 moved it from tests/ to observability/ — single source of
truth). NOTE: importing this DOES import aios_core at runtime (package init);
the engine itself is pure stdlib and has no side effects.
"""

from aios_core.observability.arch_scan import (  # noqa: F401
    AIOS_CORE,
    SRC_ROOT,
    collect_imports,
    dir_imports,
    module_imports,
)
