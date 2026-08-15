"""Ecosystem Registry v2 (TASK-046, M8-E4).

Pure index/search over SQLite — no certification/marketplace logic here (no
god object). Discovery pipeline (PLAN §M8-E4):
    User request → System Knowledge → Ecosystem Registry → Capability
    Discovery → Plugin.
MCP is an adapter consumed through entries, not the core abstraction.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .contracts import EcosystemEntry, EntryKind, Publisher
from .errors import RegistryError

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS ecosystem_entries (
    kind        TEXT NOT NULL,
    id          TEXT NOT NULL,
    version     TEXT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    entry_json  TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (kind, id)
);
"""

_SEARCH_FIELDS = ("id", "name", "description", "publisher.id", "contract_namespace")


class EcosystemRegistry:
    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._init_db()

    # -- persistence ----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(_SCHEMA_SQL)

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    # -- write ----------------------------------------------------------------

    def index_entry(self, entry: EcosystemEntry | dict) -> EcosystemEntry:
        """Insert or update (upsert on (kind, id)). Accepts dict or model."""
        if isinstance(entry, dict):
            entry = EcosystemEntry.validate_entry(**entry)
        elif not isinstance(entry, EcosystemEntry):
            raise RegistryError(f"unsupported entry type: {type(entry).__name__}")
        payload = json.dumps(entry.model_dump(mode="json"), ensure_ascii=False)
        with closing(self._connect()) as conn, conn:
            conn.execute(
                "INSERT INTO ecosystem_entries (kind, id, version, name, description,"
                " entry_json, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT (kind, id) DO UPDATE SET version=excluded.version,"
                " name=excluded.name, description=excluded.description,"
                " entry_json=excluded.entry_json, updated_at=excluded.updated_at",
                (entry.kind.value, entry.id, entry.version, entry.name,
                 entry.description, payload, self._now_iso()),
            )
        return entry

    def remove_entry(self, kind: EntryKind | str, entry_id: str) -> bool:
        """Remove an entry; returns True when it existed."""
        kind_value = kind.value if isinstance(kind, EntryKind) else kind
        with closing(self._connect()) as conn, conn:
            cur = conn.execute(
                "DELETE FROM ecosystem_entries WHERE kind=? AND id=?",
                (kind_value, entry_id),
            )
            return cur.rowcount > 0

    # -- read -----------------------------------------------------------------

    def _row_to_entry(self, row: tuple) -> EcosystemEntry:
        try:
            return EcosystemEntry.model_validate_json(row[5])
        except Exception:  # noqa: BLE001
            raise RegistryError(f"corrupt ecosystem entry: {row[0]}/{row[1]}") from None

    def get(self, kind: EntryKind | str, entry_id: str) -> EcosystemEntry | None:
        kind_value = kind.value if isinstance(kind, EntryKind) else kind
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT * FROM ecosystem_entries WHERE kind=? AND id=?",
                (kind_value, entry_id),
            ).fetchone()
        return self._row_to_entry(row) if row is not None else None

    def list_entries(self, kind: EntryKind | str | None = None) -> list[EcosystemEntry]:
        with closing(self._connect()) as conn:
            if kind is None:
                rows = conn.execute(
                    "SELECT * FROM ecosystem_entries ORDER BY kind, id"
                ).fetchall()
            else:
                kind_value = kind.value if isinstance(kind, EntryKind) else kind
                rows = conn.execute(
                    "SELECT * FROM ecosystem_entries WHERE kind=? ORDER BY kind, id",
                    (kind_value,),
                ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def search(self, keyword: str = "", kind: EntryKind | str | None = None) -> list[EcosystemEntry]:
        """Case-insensitive search over id/name/description/publisher.id/
        contract_namespace. Empty keyword + no kind -> all entries."""
        keyword = (keyword or "").strip().lower()
        entries = self.list_entries(kind)
        if not keyword:
            entries.sort(key=lambda e: (e.kind.value, e.id))
            return entries
        hits = []
        for entry in entries:
            fields = [
                entry.id.lower(), entry.name.lower(), entry.description.lower(),
                entry.contract_namespace.lower(),
                (entry.publisher.id.lower() if entry.publisher else ""),
            ]
            if any(keyword in field for field in fields):
                hits.append(entry)
        hits.sort(key=lambda e: (e.kind.value, e.id))
        return hits

    def count(self) -> int:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT COUNT(*) FROM ecosystem_entries").fetchone()
        return int(row[0])


__all__ = ["EcosystemRegistry"]
