"""Autonomous Recovery (TASK-055 — M9-P2).

Từ retry/fallback/report (M4) thành pipeline đầy đủ (PLAN §M9-15):
``Detect → Classify → Diagnose → Generate strategies → Score → Policy check →
Execute → Verify``. KHÔNG retry vô hạn: retry budget · failure fingerprint ·
circuit breaker (per-fingerprint) · cooldown · escalation (§M9-16).
"""

from __future__ import annotations

import hashlib
import threading
from typing import Callable

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import (
    FailureEvent,
    RecoveryOutcome,
    RecoveryStrategy,
    STRATEGY_SCORES,
)
from .errors import RecoveryError

_STRATEGY_ORDER = sorted(
    STRATEGY_SCORES, key=lambda s: -STRATEGY_SCORES[s]
)  # RETRY → FALLBACK → ALTERNATIVE → ESCALATE


def fingerprint_of(error_type: str, message: str) -> str:
    """sha256(error_type|message)[:16] — deterministic (C1-05 v1)."""
    return hashlib.sha256(f"{error_type}|{message}".encode()).hexdigest()[:16]


class CircuitBreaker:
    """Breaker per-fingerprint (C1-01 v1): open khi count ≥ threshold; cooldown."""

    def __init__(
        self,
        fail_threshold: int = 3,
        cooldown_s: float = 60.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._threshold = fail_threshold
        self._cooldown_s = cooldown_s
        self._clock = clock or _default_clock
        self._lock = threading.RLock()
        self._fail_count: dict[str, int] = {}
        self._cooldown_until: dict[str, float] = {}

    def is_open(self, fingerprint: str) -> bool:
        with self._lock:
            until = self._cooldown_until.get(fingerprint, 0.0)
            if until and self._clock() < until:
                return True
            if until:  # hết cooldown → CLOSED (C2-03 v2)
                self._cooldown_until.pop(fingerprint, None)
                self._fail_count.pop(fingerprint, None)
            return False

    def record_failure(self, fingerprint: str) -> bool:
        """Tăng count; trả True nếu vừa OPEN."""
        with self._lock:
            count = self._fail_count.get(fingerprint, 0) + 1
            if count >= self._threshold:
                self._cooldown_until[fingerprint] = self._clock() + self._cooldown_s
                self._fail_count[fingerprint] = count
                return True
            self._fail_count[fingerprint] = count
            return False

    def record_success(self, fingerprint: str) -> None:
        """Thành công → reset count (CLOSED, C2-02 v2)."""
        with self._lock:
            self._fail_count.pop(fingerprint, None)
            self._cooldown_until.pop(fingerprint, None)

    def state(self, fingerprint: str) -> dict[str, int | float]:
        with self._lock:
            return {
                "fail_count": self._fail_count.get(fingerprint, 0),
                "cooldown_until": self._cooldown_until.get(fingerprint, 0.0),
            }


class AutonomousRecovery:
    """Recovery pipeline deterministic — strategies scored + policy check.

    ``execute_strategy`` và ``verifier`` injectable (offline-first): mặc định
    execute = noop (record), verify = True (chỉ dùng test — production wiring
    truyền thật, C1-03 v1).
    """

    def __init__(
        self,
        event_service: EventService | None = None,
        breaker: CircuitBreaker | None = None,
        max_attempts: int = 5,
        policy_check: Callable[[RecoveryStrategy], bool] | None = None,
        execute_strategy: Callable[[RecoveryStrategy, FailureEvent], None] | None = None,
        verifier: Callable[[], bool] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._events = event_service
        self._breaker = breaker or CircuitBreaker(clock=clock)
        self._max_attempts = max_attempts
        self._policy = policy_check or (lambda _s: True)
        self._execute = execute_strategy or (lambda _s, _f: None)
        self._verify = verifier or (lambda: True)
        self._lock = threading.RLock()
        self._tried: dict[str, set[str]] = {}  # fingerprint -> strategies đã thử

    # -- main ------------------------------------------------------------------

    def recover(self, failure: FailureEvent) -> RecoveryOutcome:
        """Detect → strategies → score → policy → execute → verify → escalate."""
        fp = fingerprint_of(failure.error_type, failure.message)
        with self._lock:
            if self._breaker.is_open(fp):
                return RecoveryOutcome(
                    escalated=True,
                    reason="circuit open (cooldown)",
                )
            attempts = 0
            tried = self._tried.setdefault(fp, set())
            for strategy in _STRATEGY_ORDER:
                if strategy is RecoveryStrategy.ESCALATE:
                    # Escalate là outcome cuối — không "execute" nó.
                    break
                if strategy in tried:
                    continue  # C1-05 v1: không lặp strategy vô ích
                if not self._policy(strategy):
                    continue  # policy deny → bỏ (score 0)
                if attempts >= self._max_attempts:
                    break  # retry budget (không tính strategy chưa thử)
                attempts += 1
                tried.add(strategy)
                self._emit(failure, strategy, "attempt")
                try:
                    self._execute(strategy, failure)
                except Exception as exc:  # execute fail → strategy kế tiếp
                    self._breaker.record_failure(fp)
                    self._emit(failure, strategy, f"execute failed: {exc}")
                    continue
                if self._verify():
                    self._breaker.record_success(fp)
                    self._emit(failure, strategy, "recovered")
                    return RecoveryOutcome(
                        recovered=True,
                        strategy=strategy,
                        attempts=attempts,
                    )
                # verify fail → count failure + strategy kế tiếp
                opened = self._breaker.record_failure(fp)
                self._emit(failure, strategy, "verify failed")
                if opened:
                    return RecoveryOutcome(
                        escalated=True,
                        strategy=strategy,
                        attempts=attempts,
                        reason="circuit open after repeated failures",
                    )
            self._emit(failure, None, "escalated")
            return RecoveryOutcome(
                escalated=True,
                attempts=attempts,
                reason="no feasible strategy",
            )

    def reset(self, fingerprint: str) -> None:
        """Reset tried-set (gọi khi context thay đổi — C2-01 v2 tinh thần)."""
        with self._lock:
            self._tried.pop(fingerprint, None)
            self._breaker.record_success(fingerprint)

    # -- internals -------------------------------------------------------------

    def _emit(self, failure: FailureEvent, strategy: RecoveryStrategy | None, note: str) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_RECOVERY,
            {
                "execution_id": failure.execution_id,
                "error_type": failure.error_type,
                "strategy": strategy.value if strategy else "escalate",
                "note": note,
            },
            source="autonomous.recovery",
        )


def _default_clock() -> float:
    import time

    return time.time()
