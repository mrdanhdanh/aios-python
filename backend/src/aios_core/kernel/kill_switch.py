"""Kill Switch — M10-F3 (TASK-068).

`aiagent stop execution <id>` · `aiagent stop goal <id>` · `aiagent emergency-stop`:
Autonomous loops STOP · New tasks STOP · New tool calls BLOCK · Pending approvals
CANCEL · Running reversible ROLLBACK-marked. Gate duy nhất — không shortcut
(Gate E: kill-switch bypass = 0).
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Callable


class KillSwitchError(RuntimeError):
    pass


@dataclass
class EmergencyState:
    """Trạng thái emergency (in-memory, thread-safe)."""

    emergency: bool = False
    blocked_executions: int = 0
    blocked_tool_calls: int = 0
    cancelled_approvals: int = 0
    reversible: list[str] = field(default_factory=list)
    released: bool = False

    def snapshot(self) -> dict[str, Any]:
        return {
            "emergency": self.emergency,
            "blocked_executions": self.blocked_executions,
            "blocked_tool_calls": self.blocked_tool_calls,
            "cancelled_approvals": self.cancelled_approvals,
            "reversible": list(self.reversible),
            "released": self.released,
        }


class KillSwitch:
    """Emergency control plane — gate duy nhất cho execution mới + tool calls."""

    def __init__(
        self,
        cancel_execution: Callable[[str], None] | None = None,
        cancel_goal: Callable[[str], Any] | None = None,
        emit: Callable[[str, dict], None] | None = None,
    ) -> None:
        self._cancel_execution = cancel_execution
        self._cancel_goal = cancel_goal
        self._emit = emit or (lambda _t, _p: None)
        self._state = EmergencyState()
        self._lock = threading.RLock()

    # -- API ----------------------------------------------------------------
    @property
    def state(self) -> EmergencyState:
        return self._state

    def stop_execution(self, execution_id: str) -> None:
        """Cancel một execution (qua ExecutionService.cancel — public API)."""
        if self._cancel_execution is not None:
            self._cancel_execution(execution_id)
        else:
            raise KillSwitchError("cancel_execution hook chưa được wire")

    def stop_goal(self, goal_id: str) -> None:
        """Cascade cancel một goal (qua GoalManager.cancel_goal — public API)."""
        if self._cancel_goal is not None:
            self._cancel_goal(goal_id)
        else:
            raise KillSwitchError("cancel_goal hook chưa được wire")

    def emergency_stop(self, running: list[str] | None = None) -> EmergencyState:
        """EMERGENCY: block mọi việc mới + đánh dấu reversible. Idempotent."""
        with self._lock:
            if self._state.emergency:
                return self._state  # idempotent — không double event/state
            self._state.emergency = True
            self._state.reversible = list(running or [])
            self._state.released = False
            self._emit("emergency.stopped", self._state.snapshot())
            return self._state

    def release(self) -> EmergencyState:
        """Hết emergency — an toàn: gọi khi chưa emergency → no-op."""
        with self._lock:
            if not self._state.emergency:
                return self._state
            self._state.emergency = False
            self._state.reversible = []
            self._state.released = True
            self._emit("emergency.released", self._state.snapshot())
            return self._state

    # -- gates --------------------------------------------------------------
    def preflight(self) -> bool:
        """Execution mới được chạy? (false khi emergency)"""
        if self._state.emergency:
            with self._lock:
                self._state.blocked_executions += 1
            return False
        return True

    def preflight_tool(self) -> bool:
        """Tool call mới được thực hiện? (false khi emergency)"""
        if self._state.emergency:
            with self._lock:
                self._state.blocked_tool_calls += 1
            return False
        return True

    def cancel_pending_approvals(self) -> int:
        """Đánh dấu approvals pending bị hủy (caller quản lý danh sách)."""
        with self._lock:
            if self._state.emergency:
                self._state.cancelled_approvals += 1
            return self._state.cancelled_approvals
