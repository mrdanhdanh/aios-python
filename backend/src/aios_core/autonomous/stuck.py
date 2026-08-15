"""Advanced Stuck Detection (TASK-061 — M9-P2).

7 signals (PLAN §M9-27): repeated tool calls · repeated errors · no state
change · no progress · oscillation (A→B→A→B) · budget burn · contradictory
plans. Detect deterministic — chỉ dựa trên sequence, không phụ thuộc thời
gian thật (R2-2 v2).
"""

from __future__ import annotations

import threading
from collections import deque
from typing import Any

from .contracts import StuckReport, StuckSignal

# Thresholds mặc định (C2-02 v2, injectable).
_DEFAULTS = {
    "tool_repeat": 3,
    "error_repeat": 3,
    "no_state_change": 5,
    "no_progress": 5,
    "budget_events": 3,
    "replan_count": 3,
}

_MAX_GOALS = 1000  # R2-1 v2: cap tránh leak


class StuckDetector:
    """Window per goal_id — record() append, detect() đọc, reset() xóa."""

    def __init__(self, window_size: int = 20, thresholds: dict[str, int] | None = None) -> None:
        self._window_size = window_size
        self._thresholds = {**_DEFAULTS, **(thresholds or {})}
        self._lock = threading.RLock()
        self._windows: dict[str, deque] = {}

    # -- public API ------------------------------------------------------------

    def record(self, event_type: str, goal_id: str, detail: dict[str, Any] | None = None) -> None:
        """event_type ∈ {TOOL_CALL, ERROR, STATE_CHANGE, PROGRESS, REPLAN, BUDGET}."""
        with self._lock:
            window = self._windows.setdefault(goal_id, deque(maxlen=self._window_size))
            window.append(
                {"type": event_type, "detail": dict(detail or {})}
            )
            if len(self._windows) > _MAX_GOALS:
                # evict goal cũ nhất (insertion order — dict)
                oldest = next(iter(self._windows))
                if oldest != goal_id:
                    self._windows.pop(oldest, None)

    def reset(self, goal_id: str) -> None:
        """Xóa window — gọi khi replan/recovery thành công (C2-01 v2)."""
        with self._lock:
            self._windows.pop(goal_id, None)

    def detect(self, goal_id: str) -> StuckReport:
        """STUCK nếu ≥ 1 signal; counts deterministic."""
        with self._lock:
            window = self._windows.get(goal_id)
            if window is None:
                return StuckReport(window_size=self._window_size)
            events = list(window)
        signals: list[str] = []
        counts: dict[str, int] = {}

        tool_counts: dict[str, int] = {}
        error_counts: dict[str, int] = {}
        states: list[str] = []
        progress_seen = False
        budget_count = 0
        replan_count = 0

        for ev in events:
            t = ev["type"]
            d = ev["detail"]
            if t == "TOOL_CALL":
                tool = str(d.get("tool_id", ""))
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            elif t == "ERROR":
                fp = str(d.get("fingerprint", ""))
                error_counts[fp] = error_counts.get(fp, 0) + 1
            elif t == "STATE_CHANGE":
                states.append(str(d.get("state", "")))
            elif t == "PROGRESS":
                progress_seen = True
            elif t == "BUDGET":
                budget_count += 1
            elif t == "REPLAN":
                replan_count += 1

        # 1. Repeated tool calls
        for tool, n in tool_counts.items():
            counts[StuckSignal.REPEATED_TOOL_CALLS.value] = counts.get(
                StuckSignal.REPEATED_TOOL_CALLS.value, 0) + n
        if any(n >= self._thresholds["tool_repeat"] for n in tool_counts.values()):
            signals.append(StuckSignal.REPEATED_TOOL_CALLS.value)

        # 2. Repeated errors
        for fp, n in error_counts.items():
            counts[StuckSignal.REPEATED_ERRORS.value] = counts.get(
                StuckSignal.REPEATED_ERRORS.value, 0) + n
        if any(n >= self._thresholds["error_repeat"] for n in error_counts.values()):
            signals.append(StuckSignal.REPEATED_ERRORS.value)

        # 3. No state change: ≥ N STATE_CHANGE nhưng chỉ 1 state duy nhất
        if len(states) >= self._thresholds["no_state_change"] and len(set(states)) == 1:
            signals.append(StuckSignal.NO_STATE_CHANGE.value)
        counts[StuckSignal.NO_STATE_CHANGE.value] = len(states)

        # 4. No progress: ≥ N bước (tool/error/state) nhưng chưa từng PROGRESS
        activity = sum(tool_counts.values()) + sum(error_counts.values()) + len(states)
        if activity >= self._thresholds["no_progress"] and not progress_seen:
            signals.append(StuckSignal.NO_PROGRESS.value)

        # 5. Oscillation: tồn tại i: states[i]==states[i+2] and states[i+1]==states[i+3]
        if any(
            states[i] == states[i + 2] and states[i + 1] == states[i + 3]
            for i in range(len(states) - 3)
        ):
            signals.append(StuckSignal.OSCILLATION.value)

        # 6. Budget burn: ≥ 3 BUDGET + 0 PROGRESS
        counts[StuckSignal.BUDGET_BURN.value] = budget_count
        if budget_count >= self._thresholds["budget_events"] and not progress_seen:
            signals.append(StuckSignal.BUDGET_BURN.value)

        # 7. Contradictory plans: ≥ 3 REPLAN (v1 — C1-04 v1)
        counts[StuckSignal.CONTRADICTORY_PLANS.value] = replan_count
        if replan_count >= self._thresholds["replan_count"]:
            signals.append(StuckSignal.CONTRADICTORY_PLANS.value)

        verdict = "stuck" if signals else "normal"
        return StuckReport(
            signals=signals,
            counts=counts,
            verdict=verdict,
            window_size=self._window_size,
        )
