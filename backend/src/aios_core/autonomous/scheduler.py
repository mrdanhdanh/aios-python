"""Autonomous Scheduler (TASK-062 — M9-P4).

Từ `WHEN execute?` (SchedulerService M1 — queue kỹ thuật) thành **Autonomous
Scheduler** chủ động (PLAN §M9-28): proactive AIOS — System → Observation →
Goal → AIOS acts. Trigger INTERVAL/DAILY + persist last-run (restart không
chạy lại) + run_due deterministic (cùng now → cùng trigger set).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import ScheduleTrigger, TriggerKind, TriggerRun
from .errors import ScheduleError

_MAX_RUN_HISTORY = 1000

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS autonomous_triggers (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    interval_s REAL NOT NULL DEFAULT 0,
    at_hour INTEGER NOT NULL DEFAULT 0,
    target_id TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    last_run_at REAL NOT NULL DEFAULT -1,
    last_run_day INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS autonomous_trigger_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_id TEXT NOT NULL,
    at REAL NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT ''
);
"""


class AutonomousScheduler:
    """Trigger registry + persist + run_due (offline-first, deterministic)."""

    def __init__(
        self,
        event_service: EventService | None,
        db_path: Path | str,
        now: Callable[[], float] | None = None,
    ) -> None:
        self._events = event_service
        self._db_path = Path(db_path)
        self._clock = now or _default_clock
        self._lock = threading.RLock()
        self._fns: dict[str, Callable[[], Any]] = {}  # C1-04 v1: in-memory
        self._init_db()

    # -- registry --------------------------------------------------------------

    def register_trigger(self, trigger: ScheduleTrigger, fn: Callable[[], Any]) -> None:
        """Trùng id → raise (C1-05 v1, fail-fast). Validate theo kind."""
        with self._lock:
            if trigger.kind == TriggerKind.INTERVAL and trigger.interval_s <= 0:
                raise ScheduleError("interval_s phải > 0 (INTERVAL)")
            if trigger.kind == TriggerKind.DAILY and not (0 <= trigger.at_hour <= 23):
                raise ScheduleError("at_hour phải 0-23 (DAILY)")
            row = self._get_trigger(trigger.id)
            if row is not None:
                raise ScheduleError(f"trigger trùng id: {trigger.id}")
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    """
                    INSERT INTO autonomous_triggers (id, kind, interval_s, at_hour,
                        target_id, enabled, last_run_at, last_run_day)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trigger.id, trigger.kind.value, trigger.interval_s,
                        trigger.at_hour, trigger.target_id, int(trigger.enabled),
                        -1, 0,
                    ),
                )
            self._fns[trigger.id] = fn

    def unregister_trigger(self, trigger_id: str) -> None:
        with self._lock:
            self._fns.pop(trigger_id, None)
            with closing(self._connect()) as conn, conn:
                conn.execute("DELETE FROM autonomous_triggers WHERE id=?", (trigger_id,))

    def list_triggers(self) -> list[ScheduleTrigger]:
        with self._lock:
            with closing(self._connect()) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM autonomous_triggers").fetchall()
            out = []
            for row in sorted(rows, key=lambda r: r["id"]):
                out.append(ScheduleTrigger(
                    id=row["id"],
                    kind=TriggerKind(row["kind"]),
                    interval_s=row["interval_s"],
                    at_hour=row["at_hour"],
                    target_id=row["target_id"],
                    enabled=bool(row["enabled"]),
                ))
            return out

    # -- run -------------------------------------------------------------------

    def run_due(self, now: float | None = None) -> list[TriggerRun]:
        """Chạy trigger đã đến hạn — mỗi trigger tối đa 1 lần (C2-02 v2)."""
        with self._lock:
            now = now if now is not None else self._clock()
            runs: list[TriggerRun] = []
            for trigger in self.list_triggers():
                if not trigger.enabled:
                    continue
                row = self._get_trigger(trigger.id)
                if row is None:
                    continue
                due = self._is_due(trigger, row["last_run_at"], row["last_run_day"], now)
                if not due:
                    continue
                fn = self._fns.get(trigger.id)
                if fn is None:
                    run = TriggerRun(trigger_id=trigger.id, at=now,
                                     status="failed", note="fn chưa đăng ký (restart?)")
                    self._record(trigger.id, now, run.status, run.note)
                    runs.append(run)
                    continue
                try:
                    fn()
                    run = TriggerRun(trigger_id=trigger.id, at=now, status="ok")
                except Exception as exc:
                    run = TriggerRun(trigger_id=trigger.id, at=now,
                                     status="failed", note=str(exc))
                self._record(trigger.id, now, run.status, run.note)
                self._emit(trigger, run)
                runs.append(run)
            return runs

    # -- internals -------------------------------------------------------------

    def _is_due(self, trigger: ScheduleTrigger, last_run_at: float, last_run_day: int, now: float) -> bool:
        if trigger.kind == TriggerKind.INTERVAL:
            return last_run_at < 0 or last_run_at + trigger.interval_s <= now
        # DAILY: hour khớp AND chưa chạy hôm nay (C1-02 v1)
        hour = datetime.fromtimestamp(now, tz=timezone.utc).hour
        today = int(now // 86400)
        return hour == trigger.at_hour and last_run_day < today

    def _record(self, trigger_id: str, at: float, status: str, note: str) -> None:
        """Cập nhật last_run NGAY + insert history — atomic (R2-1 v2)."""
        today = int(at // 86400)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "UPDATE autonomous_triggers SET last_run_at=?, last_run_day=? WHERE id=?",
                (at, today, trigger_id),
            )
            conn.execute(
                "INSERT INTO autonomous_trigger_runs (trigger_id, at, status, note)"
                " VALUES (?, ?, ?, ?)",
                (trigger_id, at, status, note),
            )
            conn.execute(
                """
                DELETE FROM autonomous_trigger_runs WHERE id NOT IN (
                    SELECT id FROM autonomous_trigger_runs ORDER BY id DESC LIMIT ?
                )
                """,
                (_MAX_RUN_HISTORY,),
            )

    def _emit(self, trigger: ScheduleTrigger, run: TriggerRun) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_SCHEDULE,
            {
                "trigger_id": trigger.id,
                "kind": trigger.kind.value,
                "status": run.status,
                "at": run.at,
            },
            source="autonomous.scheduler",
        )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(_DB_SCHEMA)

    def _get_trigger(self, trigger_id: str) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM autonomous_triggers WHERE id=?", (trigger_id,)
            ).fetchone()


def _default_clock() -> float:
    import time

    return time.time()
