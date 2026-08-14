"""Harness lifecycle (TASK-029, H1): pure deterministic state machine."""

from __future__ import annotations

from .contracts import HarnessRunStatus
from .errors import HarnessLifecycleError

TRANSITIONS: dict[HarnessRunStatus, frozenset[HarnessRunStatus]] = {
    HarnessRunStatus.CREATED: frozenset({
        HarnessRunStatus.PREPARING, HarnessRunStatus.FAILED}),
    HarnessRunStatus.PREPARING: frozenset({
        HarnessRunStatus.VALIDATING, HarnessRunStatus.FAILED}),
    HarnessRunStatus.VALIDATING: frozenset({
        HarnessRunStatus.RUNNING, HarnessRunStatus.FAILED}),
    HarnessRunStatus.RUNNING: frozenset({
        HarnessRunStatus.VERIFYING, HarnessRunStatus.FAILED}),
    HarnessRunStatus.VERIFYING: frozenset({
        HarnessRunStatus.COMPLETED, HarnessRunStatus.FAILED}),
    HarnessRunStatus.COMPLETED: frozenset({HarnessRunStatus.FAILED}),
    HarnessRunStatus.FAILED: frozenset({HarnessRunStatus.DIAGNOSED}),
    HarnessRunStatus.DIAGNOSED: frozenset(),
}


class HarnessLifecycle:
    """Pure transitions; terminal = COMPLETED/DIAGNOSED (outcome reached)."""

    @staticmethod
    def can_transition(current: HarnessRunStatus, target: HarnessRunStatus) -> bool:
        return target in TRANSITIONS.get(current, frozenset())

    @staticmethod
    def transition(current: HarnessRunStatus, target: HarnessRunStatus) -> HarnessRunStatus:
        if not HarnessLifecycle.can_transition(current, target):
            raise HarnessLifecycleError(
                f"invalid transition {current.value!r} -> {target.value!r}")
        return target

    @staticmethod
    def is_terminal(status: HarnessRunStatus) -> bool:
        return status in (HarnessRunStatus.COMPLETED, HarnessRunStatus.DIAGNOSED)
