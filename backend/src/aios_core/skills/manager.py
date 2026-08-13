"""SkillManager — lifecycle 10 trạng thái, SQLite-persisted (TASK-015).

Optimistic concurrency (R2): every mutation uses UPDATE ... WHERE state=<old>;
rowcount==0 distinguishes not-found vs concurrent change. resolve uses INSERT
+ IntegrityError catch (TOCTOU-safe across instances on the same db_path).
Dependent check (R1) on rollback/remove.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from ..semver import compare, parse_version
from .base import (
    Skill,
    SkillManifest,
    SkillSource,
    SkillState,
    assert_transition,
    is_installed_state,
)
from .errors import SkillError, SkillStateError
from .schema import SKILLS_SCHEMA_SQL

_EVENT_INSTALLED = "skill.installed"
_EVENT_UPDATED = "skill.updated"
_EVENT_REMOVED = "skill.removed"

SourceLoader = Callable[[SkillSource, str], dict]  # (source, ref) -> manifest dict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dependency(dep: str) -> tuple[str, str | None]:
    """'id' -> (id, None); 'id@>=X.Y.Z' -> (id, 'X.Y.Z'). Malformed -> SkillError."""
    if "@" in dep:
        parts = dep.split("@")
        if len(parts) != 2 or not parts[1].startswith(">="):
            raise SkillError(f"invalid dependency constraint: {dep!r}")
        constraint = parts[1][2:]
        try:
            parse_version(constraint)
        except ValueError:
            raise SkillError(f"invalid dependency constraint: {dep!r}") from None
        return parts[0], constraint
    return dep, None


class SkillManager:
    def __init__(
        self,
        db_path: Path | str,
        source_loader: SourceLoader | None = None,
        event_sink: Callable[[str, dict], None] | None = None,
    ) -> None:
        self._db_path = Path(db_path)
        self._source_loader = source_loader or self._default_loader
        self._event_sink = event_sink
        self._init_db()

    # -- persistence ----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(SKILLS_SCHEMA_SQL)

    def _emit(self, event_type: str, payload: dict) -> None:
        if self._event_sink is None:
            return
        try:
            self._event_sink(event_type, payload)
        except Exception:  # noqa: BLE001 — best-effort
            pass

    def _row_to_skill(self, row: tuple) -> Skill:
        try:
            manifest = json.loads(row[5])
            history = json.loads(row[6])
        except (ValueError, TypeError):
            raise SkillError(f"corrupt skill data for {row[0]!r}") from None
        if not isinstance(history, list):
            raise SkillError(f"corrupt history for {row[0]!r}")
        return Skill(
            id=row[0], name=row[1], version=row[2], source=SkillSource(row[3]),
            state=SkillState(row[4]), manifest=manifest, history=history,
            installed_at=row[7], created_at=row[8], updated_at=row[9],
        )

    def _get_row(self, conn: sqlite3.Connection, skill_id: str) -> tuple | None:
        return conn.execute("SELECT * FROM skills WHERE id=?", (skill_id,)).fetchone()

    def _transition(self, skill_id: str, op: str, extra_sets: dict | None = None) -> Skill:
        """Apply op with optimistic concurrency: UPDATE WHERE state=old."""
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, skill_id)
            if row is None:
                raise SkillError(f"skill not found: {skill_id}")
            current = SkillState(row[4])
            target = assert_transition(current, op)
            now = _now_iso()
            sets = {"state": target.value, "updated_at": now}
            if extra_sets:
                sets.update(extra_sets)
            assignments = ", ".join(f"{k}=?" for k in sets)
            params = list(sets.values()) + [skill_id, current.value]
            cur = conn.execute(
                f"UPDATE skills SET {assignments} WHERE id=? AND state=?",
                params,
            )
            if cur.rowcount == 0:
                raise SkillError(f"{op} {skill_id}: state changed concurrently")
        return self.get(skill_id)  # type: ignore[return-value]

    # -- lifecycle ------------------------------------------------------------

    def resolve(self, source: SkillSource, ref: str) -> Skill:
        """T1: load manifest from the source loader (stub) and insert record."""
        manifest_dict = self._source_loader(source, ref)
        manifest = SkillManifest.validate_manifest(**manifest_dict)
        now = _now_iso()
        with closing(self._connect()) as conn, conn:
            try:
                conn.execute(
                    "INSERT INTO skills (id, name, version, source, state, manifest_json,"
                    " history_json, created_at, updated_at) VALUES (?, ?, ?, ?, 'resolved', ?, '[]', ?, ?)",
                    (manifest.id, manifest.name, manifest.version, manifest.source.value,
                     json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False),
                     now, now),
                )
            except sqlite3.IntegrityError:
                raise SkillError(f"skill already exists: {manifest.id}") from None
        return self.get(manifest.id)  # type: ignore[return-value]

    def validate(self, skill_id: str) -> Skill:
        """T2: one-shot (validated->validated cấm — C1-18). Deps + constraint."""
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, skill_id)
            if row is None:
                raise SkillError(f"skill not found: {skill_id}")
            manifest = SkillManifest.model_validate_json(row[5])
            # dependency resolve + installed
            for dep in manifest.dependencies:
                dep_id, constraint = _parse_dependency(dep)
                dep_row = self._get_row(conn, dep_id)
                if dep_row is None:
                    raise SkillError(f"dependency not found: {dep}")
                dep_state = SkillState(dep_row[4])
                if dep_state == SkillState.REMOVED:
                    raise SkillError(f"dependency removed: {dep_id}")  # C1-08
                if not is_installed_state(dep_state):
                    raise SkillError(f"dependency not installed: {dep_id}")
                if constraint is not None:
                    have = dep_row[2]
                    if compare(have, constraint) < 0:
                        raise SkillError(
                            f"dependency not compatible: {dep_id} (need >={constraint}, have {have})"
                        )
        return self._transition(skill_id, "validate")

    def install(self, skill_id: str) -> Skill:
        now = _now_iso()
        skill = self._transition(skill_id, "install", {"installed_at": now})
        self._emit(_EVENT_INSTALLED, {"skill_id": skill_id, "version": skill.version})
        return skill

    def enable(self, skill_id: str) -> Skill:
        return self._transition(skill_id, "enable")

    def disable(self, skill_id: str) -> Skill:
        return self._transition(skill_id, "disable")

    def unload(self, skill_id: str) -> Skill:
        return self._transition(skill_id, "unload")

    def reload(self, skill_id: str) -> Skill:
        return self._transition(skill_id, "reload")

    def upgrade(self, skill_id: str, new_version: str) -> Skill:
        """T8: new_version must be > current; push current manifest+version to history."""
        try:
            parse_version(new_version)
        except ValueError:
            raise SkillError(f"invalid new version: {new_version!r}") from None  # C2-03
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, skill_id)
            if row is None:
                raise SkillError(f"skill not found: {skill_id}")
            current_version = row[2]
            if compare(new_version, current_version) <= 0:
                raise SkillError(
                    f"new version must be greater than current: {new_version} <= {current_version}"
                )
            target = assert_transition(SkillState(row[4]), "upgrade")
            history = json.loads(row[6] or "[]")
            history.append({"version": current_version, "manifest": json.loads(row[5])})
            now = _now_iso()
            manifest = json.loads(row[5])
            manifest["version"] = new_version
            cur = conn.execute(
                "UPDATE skills SET state=?, version=?, manifest_json=?, history_json=?, updated_at=?"
                " WHERE id=? AND state=?",
                (target.value, new_version, json.dumps(manifest, ensure_ascii=False),
                 json.dumps(history, ensure_ascii=False), now, skill_id, row[4]),
            )
            if cur.rowcount == 0:
                raise SkillError(f"upgrade {skill_id}: state changed concurrently")
        skill = self.get(skill_id)
        assert skill is not None
        self._emit(_EVENT_UPDATED, {"skill_id": skill_id, "version": skill.version})
        return skill

    def rollback(self, skill_id: str) -> Skill:
        """T9: pop history; dependent check (R1); emit skill.updated."""
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, skill_id)
            if row is None:
                raise SkillError(f"skill not found: {skill_id}")
            target = assert_transition(SkillState(row[4]), "rollback")
            history = json.loads(row[6] or "[]")
            if not history:
                raise SkillStateError("no history to rollback")
            entry = history.pop()
            target_version = entry["version"]
            # R1: dependent constraint check
            self._check_dependents(conn, skill_id, target_version, op="rollback")
            manifest = json.loads(row[5])
            manifest["version"] = target_version
            now = _now_iso()
            cur = conn.execute(
                "UPDATE skills SET state=?, version=?, manifest_json=?, history_json=?, updated_at=?"
                " WHERE id=? AND state=?",
                (target.value, target_version, json.dumps(manifest, ensure_ascii=False),
                 json.dumps(history, ensure_ascii=False), now, skill_id, row[4]),
            )
            if cur.rowcount == 0:
                raise SkillError(f"rollback {skill_id}: state changed concurrently")
        skill = self.get(skill_id)
        assert skill is not None
        self._emit(_EVENT_UPDATED, {"skill_id": skill_id, "version": skill.version})
        return skill

    def remove(self, skill_id: str) -> Skill:
        """T10: soft-delete terminal. Dependent check (R1): active dependents block."""
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, skill_id)
            if row is None:
                raise SkillError(f"skill not found: {skill_id}")
            self._check_dependents(conn, skill_id, target_version=None, op="remove")
            target = assert_transition(SkillState(row[4]), "remove")
            now = _now_iso()
            cur = conn.execute(
                "UPDATE skills SET state=?, updated_at=? WHERE id=? AND state=?",
                (target.value, now, skill_id, row[4]),
            )
            if cur.rowcount == 0:
                raise SkillError(f"remove {skill_id}: state changed concurrently")
        self._emit(_EVENT_REMOVED, {"skill_id": skill_id})
        return self.get(skill_id)  # type: ignore[return-value]

    def _check_dependents(self, conn: sqlite3.Connection, skill_id: str,
                          target_version: str | None, op: str) -> None:
        """R1: block op if a dependent's constraint breaks (rollback) or a
        dependent is active (remove)."""
        for dep_row in conn.execute("SELECT * FROM skills WHERE id != ?", (skill_id,)).fetchall():
            dep_manifest = json.loads(dep_row[5])
            dep_state = SkillState(dep_row[4])
            for dep in dep_manifest.get("dependencies", []):
                try:
                    dep_id, constraint = _parse_dependency(dep)
                except SkillError:
                    continue
                if dep_id != skill_id:
                    continue
                if op == "rollback":
                    if constraint is not None and compare(target_version, constraint) < 0:
                        raise SkillError(
                            f"dependent broken: {dep_row[0]} (need >={constraint},"
                            f" have {target_version})"
                        )
                elif dep_state in (SkillState.ENABLED, SkillState.RELOADED):
                    raise SkillError(f"dependent broken: {dep_row[0]} (active)")

    # -- queries --------------------------------------------------------------

    def get(self, skill_id: str) -> Skill | None:
        with closing(self._connect()) as conn:
            row = self._get_row(conn, skill_id)
            return self._row_to_skill(row) if row else None

    def list(self) -> list[Skill]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM skills ORDER BY created_at").fetchall()
        return [self._row_to_skill(r) for r in rows]

    def list_by_state(self, state: SkillState) -> list[Skill]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM skills WHERE state=? ORDER BY created_at", (state.value,)
            ).fetchall()
        return [self._row_to_skill(r) for r in rows]

    def list_by_capability(self, capability: str) -> list[Skill]:
        return [s for s in self.list() if capability in s.manifest.get("capabilities", [])]

    @staticmethod
    def _default_loader(source: SkillSource, ref: str) -> dict:
        raise SkillError(f"no source loader configured for {source.value}")

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex
