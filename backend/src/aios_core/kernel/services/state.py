"""State service: per-execution state with snapshots."""

from __future__ import annotations

import copy
import logging
import threading
from typing import Any

from ...logging import get_logger

logger = get_logger("aios.kernel.services.state")

NODE_PENDING = "pending"
NODE_RUNNING = "running"
NODE_COMPLETED = "completed"
NODE_FAILED = "failed"


class StateService:
    """In-memory execution state store.

    Schema per execution: ``{plan: dict, nodes: {id: status},
    results: {id: result}, started_at: str}``.
    """

    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def set_state(self, execution_id: str, state: dict[str, Any]) -> None:
        with self._lock:
            self._states[execution_id] = state

    def get_state(self, execution_id: str) -> dict[str, Any] | None:
        with self._lock:
            state = self._states.get(execution_id)
            return copy.deepcopy(state) if state is not None else None

    def update_state(self, execution_id: str, **fields: Any) -> None:
        with self._lock:
            state = self._states.setdefault(execution_id, {})
            state.update(fields)

    def snapshot(self, execution_id: str) -> dict[str, Any]:
        with self._lock:
            state = self._states.get(execution_id, {})
            return self._safe_deepcopy(state)

    def restore(self, execution_id: str, snapshot: dict[str, Any]) -> None:
        with self._lock:
            self._states[execution_id] = self._safe_deepcopy(snapshot)

    def delete(self, execution_id: str) -> None:
        with self._lock:
            self._states.pop(execution_id, None)

    @staticmethod
    def _safe_deepcopy(value: Any) -> Any:
        """Deep copy, falling back to repr for individual non-copyable leaves."""
        if isinstance(value, dict):
            return {k: StateService._safe_deepcopy(v) for k, v in value.items()}
        if isinstance(value, list):
            return [StateService._safe_deepcopy(v) for v in value]
        if isinstance(value, tuple):
            return tuple(StateService._safe_deepcopy(v) for v in value)
        try:
            return copy.deepcopy(value)
        except Exception:  # noqa: BLE001
            logger.warning("State value not deep-copyable; storing repr")
            return repr(value)
