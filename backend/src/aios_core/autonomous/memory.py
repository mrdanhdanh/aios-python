"""Autonomous Memory (TASK-057 — M9-P2).

Nâng Memory Coordinator (M5): 6 loại memory — Working · Episodic · Semantic ·
Procedural · Failure · Goal (PLAN §M9-19). Learning Loop: Execution →
Evaluation → Failure/Success → Extract Lesson → Validate → Memory → Future
Planning (§M9-20). **INV-034: autonomous memory KHÔNG tự promote thành
Knowledge chưa kiểm chứng** — candidate → deduplicate → validate → confidence
→ promote (double gate: validated=True VÀ confidence ≥ 0.5).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import Lesson, MemoryEntry, MemoryEntryKind
from .errors import MemoryPromotionError

_PROMOTE_MIN_CONFIDENCE = 0.5  # C2-01 v2: double gate

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS autonomous_memory (
    kind TEXT NOT NULL,
    key TEXT NOT NULL,
    content_json TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.0,
    validated INTEGER NOT NULL DEFAULT 0,
    promoted INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (kind, key)
)
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AutonomousMemory:
    """6-kind memory persist SQLite + Learning Loop (INV-034 enforced)."""

    def __init__(self, event_service: EventService | None, db_path: Path | str) -> None:
        self._events = event_service
        self._db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_db()

    # -- public API ------------------------------------------------------------

    def store(
        self,
        kind: MemoryEntryKind,
        key: str,
        content: dict,
        confidence: float = 0.0,
        source: str = "",
    ) -> MemoryEntry:
        """Upsert entry. Key do caller (C2-03 v2)."""
        with self._lock:
            conf = min(1.0, max(0.0, confidence))
            now = _now_iso()
            row = self._get_row(kind, key)
            validated = bool(row["validated"]) if row else False
            promoted = bool(row["promoted"]) if row else False
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    """
                    INSERT INTO autonomous_memory (kind, key, content_json, confidence,
                        validated, promoted, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(kind, key) DO UPDATE SET
                        content_json=excluded.content_json,
                        confidence=excluded.confidence,
                        source=excluded.source,
                        updated_at=excluded.updated_at
                    """,
                    (
                        kind.value, key, json.dumps(content, default=str), conf,
                        int(validated), int(promoted), source, now, now,
                    ),
                )
            return self.retrieve(kind, key)

    def retrieve(self, kind: MemoryEntryKind, key: str | None = None) -> MemoryEntry | None | list[MemoryEntry]:
        """key None → list theo kind (C1-04 v1)."""
        with self._lock:
            with closing(self._connect()) as conn:
                conn.row_factory = sqlite3.Row
                if key is None:
                    rows = conn.execute(
                        "SELECT * FROM autonomous_memory WHERE kind=? ORDER BY updated_at DESC",
                        (kind.value,),
                    ).fetchall()
                    return [self._row_to_entry(r) for r in rows]
                row = conn.execute(
                    "SELECT * FROM autonomous_memory WHERE kind=? AND key=?",
                    (kind.value, key),
                ).fetchone()
            return self._row_to_entry(row) if row else None

    def validate(self, key: str, kind: MemoryEntryKind, confidence: float, source: str) -> MemoryEntry:
        """Đánh dấu validated — source bắt buộc (C1-01 v1)."""
        with self._lock:
            if not source.strip():
                raise MemoryPromotionError("validate cần source (không validate trống)")
            entry = self.retrieve(kind, key)
            if entry is None:
                raise MemoryPromotionError(f"entry không tồn tại: {kind.value}/{key}")
            conf = min(1.0, max(0.0, confidence))
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_memory SET validated=1, confidence=?, source=?, updated_at=? "
                    "WHERE kind=? AND key=?",
                    (conf, source, _now_iso(), kind.value, key),
                )
            return self.retrieve(kind, key)

    def promote(self, kind: MemoryEntryKind, key: str) -> MemoryEntry:
        """INV-034: double gate — validated=True VÀ confidence ≥ 0.5 (C2-01 v2)."""
        with self._lock:
            entry = self.retrieve(kind, key)
            if entry is None:
                raise MemoryPromotionError(f"entry không tồn tại: {kind.value}/{key}")
            if not entry.validated:
                raise MemoryPromotionError(
                    f"INV-034: entry {kind.value}/{key} chưa validated — không promote"
                )
            if entry.confidence < _PROMOTE_MIN_CONFIDENCE:
                raise MemoryPromotionError(
                    f"INV-034: confidence {entry.confidence} < {_PROMOTE_MIN_CONFIDENCE} — không promote"
                )
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_memory SET promoted=1, updated_at=? WHERE kind=? AND key=?",
                    (_now_iso(), kind.value, key),
                )
            promoted = self.retrieve(kind, key)
            if self._events is not None:
                self._events.emit(
                    EventType.AUTONOMY_MEMORY_PROMOTED,
                    {"kind": kind.value, "key": key, "confidence": entry.confidence},
                    source="autonomous.memory",
                )
            return promoted

    # -- learning loop ---------------------------------------------------------

    def learn(self, failure: dict) -> Lesson:
        """Extract lesson từ failure — keys: when/failure/cause/fix/confidence.

        (C1-03 v1): thiếu cause/fix → confidence 0.3 (không promote được);
        đủ 5 keys → confidence input. Key tự sinh ``lesson:{fingerprint}``
        (C2-03 v2).
        """
        with self._lock:
            when = str(failure.get("when", ""))
            what = str(failure.get("failure", ""))
            cause = str(failure.get("cause", ""))
            fix = str(failure.get("fix", ""))
            has_full = all([when, what, cause, fix])
            conf = min(1.0, max(0.0, float(failure.get("confidence", 0.3))))
            if not has_full:
                conf = 0.3
            # fingerprint hash (tái dùng format recovery — sha256[:16])
            import hashlib

            fp = hashlib.sha256(f"lesson|{when}|{what}".encode()).hexdigest()[:16]
            key = f"lesson:{fp}"
            lesson = Lesson(key=key, when=when, failure=what, cause=cause, fix=fix,
                            confidence=conf)
            existing = self.retrieve(MemoryEntryKind.FAILURE, key)
            if existing is not None:
                # C1-02 v1: dedup → confidence = min(1.0, old + 0.1)
                new_conf = min(1.0, existing.confidence + 0.1)
                self.store(MemoryEntryKind.FAILURE, key, lesson.model_dump(),
                           confidence=new_conf, source="learning_loop")
            else:
                self.store(MemoryEntryKind.FAILURE, key, lesson.model_dump(),
                           confidence=conf, source="learning_loop")
            return lesson

    def store_goal_note(self, goal_id: str, note: str) -> MemoryEntry:
        """Goal memory helper (R2-2 v2): kind=GOAL, key=goal_id."""
        return self.store(
            MemoryEntryKind.GOAL, goal_id, {"note": note},
            confidence=0.9, source="autonomous.goal",
        )

    # -- internals -------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute(_DB_SCHEMA)

    def _get_row(self, kind: MemoryEntryKind, key: str) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM autonomous_memory WHERE kind=? AND key=?",
                (kind.value, key),
            ).fetchone()

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            kind=MemoryEntryKind(row["kind"]),
            key=row["key"],
            content=json.loads(row["content_json"]),
            confidence=row["confidence"],
            validated=bool(row["validated"]),
            promoted=bool(row["promoted"]),
            source=row["source"],
            created_at=row["created_at"],
        )
