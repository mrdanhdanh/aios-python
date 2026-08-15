"""System status — M10-F4 (TASK-071)."""

from __future__ import annotations

from typing import Any


def system_status(kernel: Any | None = None) -> dict:
    """Version + services + emergency flag."""
    from .. import __version__

    if kernel is None:
        from ..kernel import RuntimeKernel

        kernel = RuntimeKernel.create()
    out: dict = {"version": __version__}
    try:
        from ..kernel.kill_switch import KillSwitch

        switch = kernel.container.resolve(KillSwitch)
        snap = switch.state.snapshot()
        out["emergency"] = snap["emergency"]
        out["reversible"] = snap["reversible"]
    except Exception:  # noqa: BLE001
        out["emergency"] = False
    try:
        from ..models import ModelRegistry

        registry = kernel.container.resolve(ModelRegistry)
        out["services"] = {"models": len(registry.list())}
    except Exception:  # noqa: BLE001
        out["services"] = {}
    return out
