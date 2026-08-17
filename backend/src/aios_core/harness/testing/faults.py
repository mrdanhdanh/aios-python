"""Failure injection (TASK-031, H3): Chaos nhẹ deterministic."""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from .contracts import Fault, FaultType
from .errors import SimulationError


class ResourceExhaustedError(Exception):
    """Resource fault — queue/retry semantics."""


class FaultInjector:
    """Stateful injector: mỗi fault inject ĐÚNG 1 lần cho mỗi target.

    Lần gọi đầu bị fault (raise) → runner catch → retry → lần 2 không còn
    fault → thành công → recovery_events ghi nhận. attempts semantics:
    params.retries = số retry kỳ vọng (thông tin; v1 inject 1 lần).
    Deterministic, đơn luồng (C3-05).
    """

    def __init__(self, faults: list[Fault], *, default_retries: int = 1) -> None:
        self._faults = list(faults)
        self._counts: Counter[str] = Counter()
        self._default_retries = default_retries
        self.injected: list[dict] = []
        self.recovery_events: list[dict] = []

    # -- queries -------------------------------------------------------------

    def next_for(self, target: str) -> Fault | None:
        """Fault chưa inject cho target (count == 0 — C2-04).

        M13-P0 (TASK-089): fault `recoverable=False` trả MỌI lần (không
        check count) → apply raise mọi lần → runner retry fail → ERROR.
        Default recoverable=True giữ hành vi cũ (inject 1 lần/target).
        """
        for fault in self._faults:
            if fault.target == target:
                if fault.recoverable and self._counts[target] > 0:
                    return None
                return fault
        return None

    # -- execution -----------------------------------------------------------

    def apply(self, target: str, call_fn: Callable[[], Any]) -> tuple[Any, bool]:
        """Gọi call_fn với fault semantics; return (result, recovered=True).

        Fault → raise (caller retry/fallback); lần sau → bình thường.
        """
        fault = self.next_for(target)
        if fault is None:
            return call_fn(), True
        self._counts[target] += 1
        self.injected.append({"target": target, "type": fault.type.value,
                              "attempt": self._counts[target]})
        if fault.type == FaultType.TIMEOUT:
            raise TimeoutError(f"simulated timeout on {fault.target}")
        if fault.type == FaultType.FAILURE:
            raise RuntimeError(f"simulated failure on {fault.target}")
        # EXHAUSTED: v1 không sleep thật (deterministic) — raise như queue đầy
        raise ResourceExhaustedError(f"simulated resource exhausted on {fault.target}")

    def recover(self, target: str, kind: str, fault: Fault) -> None:
        """Ghi nhận recovery (runner gọi khi retry/fallback thành công)."""
        self.recovery_events.append({"type": kind, "target": target,
                                     "fault_type": fault.type.value})
