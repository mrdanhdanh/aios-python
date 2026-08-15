"""Autonomous Evaluation (TASK-060 — M9-P3).

M6 Harness Evaluation thành **decision mechanism** (PLAN §M9-25):
``Evaluation { correctness · quality · cost · risk · progress · confidence }
→ Decision { continue / retry / replan / stop / ask_human }``. Progress
Estimator (§M9-26): completion · confidence · risk · budget remaining — 3
iterations không tăng progress → STUCK → replan. Deterministic — không LLM
mặc định (thresholds injectable).
"""

from __future__ import annotations

import threading
from typing import Any

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import (
    AutonomousVerdict,
    EvaluationConfig,
    EvaluationDimensions,
    ProgressEstimate,
)

_RULE_ORDER = ("stop", "ask_human", "retry", "replan", "continue")  # C1-01 v1


class ProgressEstimator:
    """Theo dõi chuỗi progress — stuck khi N giá trị cuối bằng nhau (C1-03)."""

    def __init__(self, stuck_iterations: int = 3) -> None:
        self._stuck_n = stuck_iterations
        self._lock = threading.RLock()
        self._history: dict[str, list[float]] = {}

    def observe(self, goal_id: str, progress: float) -> None:
        with self._lock:
            self._history.setdefault(goal_id, []).append(progress)

    def is_stuck(self, goal_id: str) -> bool:
        with self._lock:
            hist = self._history.get(goal_id, [])
            if len(hist) < self._stuck_n:
                return False
            tail = hist[-self._stuck_n:]
            return all(v == tail[0] for v in tail)

    def reset(self, goal_id: str) -> None:
        with self._lock:
            self._history.pop(goal_id, None)


class AutonomousEvaluator:
    """Evaluation → decision (rule thứ tự cố định — C1-01 v1/C2-01 v2)."""

    def __init__(
        self,
        config: EvaluationConfig | None = None,
        event_service: EventService | None = None,
        estimator: ProgressEstimator | None = None,
    ) -> None:
        self._config = config or EvaluationConfig()
        self._events = event_service
        self._estimator = estimator or ProgressEstimator(
            stuck_iterations=self._config.stuck_iterations
        )

    # -- evaluation ------------------------------------------------------------

    def evaluate(
        self,
        goal_id: str,
        dimensions: EvaluationDimensions,
    ) -> tuple[AutonomousVerdict, ProgressEstimate]:
        """Rules theo thứ tự: STOP → ASK_HUMAN → RETRY → REPLAN → CONTINUE."""
        self._estimator.observe(goal_id, dimensions.progress)
        stuck = self._estimator.is_stuck(goal_id)
        estimate = ProgressEstimate(
            completion=dimensions.progress,
            confidence=min(dimensions.correctness, dimensions.quality, dimensions.confidence),
            risk=dimensions.risk,
            budget_remaining=max(0.0, 1.0 - dimensions.cost),
            progress_stuck=stuck,
            trajectory_warning=self._trajectory_warning(dimensions.trajectory_evidence),
        )

        cfg = self._config
        if dimensions.cost >= cfg.cost_max:
            verdict = AutonomousVerdict.STOP
        elif dimensions.risk >= cfg.risk_max:
            verdict = AutonomousVerdict.ASK_HUMAN
        elif dimensions.correctness < cfg.correctness_min:
            verdict = AutonomousVerdict.RETRY
        elif stuck:
            verdict = AutonomousVerdict.REPLAN
        else:
            verdict = AutonomousVerdict.CONTINUE

        self._emit(goal_id, verdict, estimate)
        return verdict, estimate

    # -- internals -------------------------------------------------------------

    @staticmethod
    def _trajectory_warning(evidence: dict[str, Any]) -> bool:
        """>0 tool_failures/recovery_count → warning (C1-02 v1)."""
        failures = int(evidence.get("tool_failures", 0) or 0)
        recoveries = int(evidence.get("recovery_count", 0) or 0)
        return failures > 0 or recoveries > 0

    def _emit(self, goal_id: str, verdict: AutonomousVerdict, estimate: ProgressEstimate) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_DECISION,
            {
                "goal_id": goal_id,
                "verdict": verdict.value,
                "progress": estimate.completion,
                "stuck": estimate.progress_stuck,
            },
            source="autonomous.evaluation",
        )
