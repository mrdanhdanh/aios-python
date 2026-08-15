"""PluginManager — lifecycle 10 trạng thái (TASK-044, M8-E2).

The state machine itself is REUSED from skills (``assert_transition`` /
``SkillState``) — no second lifecycle machine exists (PLAN §M8-E2). This
manager adds plugin-specific concerns on top: aios version compatibility
(``aios.min/max``), plugin-to-plugin dependencies, the provides index
(kind → active plugin ids) and optimistic concurrency (UPDATE ... WHERE
state=old, mirroring SkillManager). Plugins never touch Runtime/Registry/
DB/Filesystem/Network directly — they are passive records managed here.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Callable
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from ..semver import compare, parse_version
from ..skills.base import SkillState, is_installed_state
from ..skills.errors import SkillStateError as _SkillStateError
from .compat import check_compatibility
from .contracts import Plugin, PluginManifest, PluginType, assert_transition
from .errors import (
    PluginCompatibilityError,
    PluginDependencyError,
    PluginError,
    PluginStateError,
)
from .schema import PLUGINS_SCHEMA_SQL

_EVENT_RESOLVED = "plugin.resolved"
_EVENT_INSTALLED = "plugin.installed"
_EVENT_UPDATED = "plugin.updated"
_EVENT_REMOVED = "plugin.removed"

ManifestLoader = Callable[[str], dict]  # (ref) -> manifest dict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_dependency(dep: str) -> tuple[str, str | None]:
    """'id' -> (id, None); 'id@>=X.Y.Z' -> (id, 'X.Y.Z'). Malformed -> PluginDependencyError."""
    if "@" in dep:
        parts = dep.split("@")
        if len(parts) != 2 or not parts[1].startswith(">="):
            raise PluginDependencyError(f"invalid dependency constraint: {dep!r}")
        constraint = parts[1][2:]
        try:
            parse_version(constraint)
        except ValueError:
            raise PluginDependencyError(f"invalid dependency constraint: {dep!r}") from None
        return parts[0], constraint
    return dep, None


class PluginManager:
    def __init__(
        self,
        db_path: Path | str,
        manifest_loader: ManifestLoader | None = None,
        event_sink: Callable[[str, dict], None] | None = None,
        aios_version: str = "1.0.0",
        strict: bool = True,
    ) -> None:
        self._db_path = Path(db_path)
        self._manifest_loader = manifest_loader or self._default_loader
        self._event_sink = event_sink
        self._aios_version = aios_version
        self.strict = strict
        self._lock = threading.RLock()
        self._init_db()
        self._rebuild_provides()

    # -- persistence ----------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(PLUGINS_SCHEMA_SQL)

    def _emit(self, event_type: str, payload: dict) -> None:
        if self._event_sink is None:
            return
        try:
            self._event_sink(event_type, payload)
        except Exception:  # noqa: BLE001 — best-effort
            pass

    def _row_to_plugin(self, row: tuple) -> Plugin:
        try:
            manifest = json.loads(row[5])
            history = json.loads(row[6])
        except (ValueError, TypeError):
            raise PluginError(f"corrupt plugin data for {row[0]!r}") from None
        if not isinstance(history, list):
            raise PluginError(f"corrupt history for {row[0]!r}")
        return Plugin(
            id=row[0], name=row[1], version=row[2], plugin_type=PluginType(row[3]),
            state=SkillState(row[4]), manifest=manifest, history=history,
            installed_at=row[7], created_at=row[8], updated_at=row[9],
        )

    def _get_row(self, conn: sqlite3.Connection, plugin_id: str) -> tuple | None:
        return conn.execute("SELECT * FROM plugins WHERE id=?", (plugin_id,)).fetchone()

    def _transition(self, plugin_id: str, op: str, extra_sets: dict | None = None) -> Plugin:
        """Apply op with optimistic concurrency: UPDATE WHERE state=old."""
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, plugin_id)
            if row is None:
                raise PluginError(f"plugin not found: {plugin_id}")
            current = SkillState(row[4])
            try:
                target = assert_transition(current, op)
            except _SkillStateError as exc:
                raise PluginStateError(
                    f"invalid transition: {current.value} -> {op}"
                ) from exc
            now = _now_iso()
            sets = {"state": target.value, "updated_at": now}
            if extra_sets:
                sets.update(extra_sets)
            assignments = ", ".join(f"{k}=?" for k in sets)
            params = list(sets.values()) + [plugin_id, current.value]
            cur = conn.execute(
                f"UPDATE plugins SET {assignments} WHERE id=? AND state=?",
                params,
            )
            if cur.rowcount == 0:
                raise PluginError(f"{op} {plugin_id}: state changed concurrently")
        plugin = self.get(plugin_id)  # type: ignore[return-value]
        self._rebuild_provides()
        return plugin

    # -- provides index -------------------------------------------------------

    def _active_rows(self) -> list[tuple]:
        with closing(self._connect()) as conn:
            return conn.execute(
                "SELECT id, manifest_json, state FROM plugins"
            ).fetchall()

    def _rebuild_provides(self) -> None:
        """kind -> {provided id -> plugin id} for plugins in active states."""
        index: dict[str, dict[str, str]] = {}
        with self._lock:
            for row in self._active_rows():
                plugin_id, manifest_json, state = row[0], row[1], row[2]
                if SkillState(state) not in {SkillState.ENABLED, SkillState.RELOADED}:
                    continue
                try:
                    manifest = PluginManifest.model_validate_json(manifest_json)
                except Exception:  # noqa: BLE001 — corrupt record
                    continue
                for entry in manifest.provides:
                    index.setdefault(entry.kind.value, {})[entry.id] = plugin_id
            self._provides = index

    def provides(self, kind: PluginType | str) -> dict[str, str]:
        """Map provided id -> plugin id for active plugins of the given kind."""
        kind_value = kind.value if isinstance(kind, PluginType) else kind
        with self._lock:
            return dict(self._provides.get(kind_value, {}))

    # -- lifecycle ------------------------------------------------------------

    @staticmethod
    def _default_loader(ref: str) -> dict:
        raise PluginError(f"no manifest loader registered for {ref!r}")

    def resolve(self, ref: str, manifest_dict: dict | None = None) -> Plugin:
        """T1: load manifest (via loader or caller), compat check, insert record."""
        if manifest_dict is None:
            manifest_dict = self._manifest_loader(ref)
        manifest = PluginManifest.validate_manifest(**manifest_dict)
        if not check_compatibility(manifest.aios.min, manifest.aios.max, self._aios_version):
            raise PluginCompatibilityError(
                f"plugin {manifest.id} requires aios {manifest.aios.min}..{manifest.aios.max}, "
                f"running {self._aios_version}"
            )
        now = _now_iso()
        with closing(self._connect()) as conn, conn:
            try:
                conn.execute(
                    "INSERT INTO plugins (id, name, version, plugin_type, state, manifest_json,"
                    " history_json, created_at, updated_at) VALUES (?, ?, ?, ?, 'resolved', ?, '[]', ?, ?)",
                    (manifest.id, manifest.name, manifest.version, manifest.plugin_type.value,
                     json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False),
                     now, now),
                )
            except sqlite3.IntegrityError:
                raise PluginError(f"plugin already exists: {manifest.id}") from None
        self._emit(_EVENT_RESOLVED, {"plugin_id": manifest.id, "version": manifest.version})
        return self.get(manifest.id)  # type: ignore[return-value]

    def _check_dependencies(self, conn: sqlite3.Connection, manifest: PluginManifest) -> None:
        for dep in manifest.dependencies:
            dep_id, constraint = _parse_dependency(dep)
            dep_row = self._get_row(conn, dep_id)
            if dep_row is None:
                raise PluginDependencyError(f"dependency not found: {dep}")
            dep_state = SkillState(dep_row[4])
            if dep_state == SkillState.REMOVED:
                raise PluginDependencyError(f"dependency removed: {dep_id}")
            if not is_installed_state(dep_state):
                raise PluginDependencyError(f"dependency not installed: {dep_id}")
            if constraint is not None:
                have = dep_row[2]
                if compare(have, constraint) < 0:
                    raise PluginDependencyError(
                        f"dependency not compatible: {dep_id} (need >={constraint}, have {have})"
                    )

    def validate(self, plugin_id: str) -> Plugin:
        """T2: deps + aios compat re-check (one-shot — validated->validated cấm)."""
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, plugin_id)
            if row is None:
                raise PluginError(f"plugin not found: {plugin_id}")
            manifest = PluginManifest.model_validate_json(row[5])
            if not check_compatibility(manifest.aios.min, manifest.aios.max, self._aios_version):
                raise PluginCompatibilityError(
                    f"plugin {plugin_id} requires aios {manifest.aios.min}..{manifest.aios.max}, "
                    f"running {self._aios_version}"
                )
            self._check_dependencies(conn, manifest)
        return self._transition(plugin_id, "validate")

    def install(self, plugin_id: str) -> Plugin:
        now = _now_iso()
        plugin = self._transition(plugin_id, "install", {"installed_at": now})
        self._emit(_EVENT_INSTALLED, {"plugin_id": plugin_id, "version": plugin.version})
        return plugin

    def enable(self, plugin_id: str) -> Plugin:
        plugin = self._transition(plugin_id, "enable")
        self._rebuild_provides()
        self._emit(_EVENT_UPDATED, {"plugin_id": plugin_id, "state": plugin.state.value})
        return plugin

    def disable(self, plugin_id: str) -> Plugin:
        plugin = self._transition(plugin_id, "disable")
        self._rebuild_provides()
        self._emit(_EVENT_UPDATED, {"plugin_id": plugin_id, "state": plugin.state.value})
        return plugin

    def unload(self, plugin_id: str) -> Plugin:
        plugin = self._transition(plugin_id, "unload")
        self._rebuild_provides()
        return plugin

    def reload(self, plugin_id: str) -> Plugin:
        plugin = self._transition(plugin_id, "reload")
        self._rebuild_provides()
        return plugin

    def upgrade(self, plugin_id: str, new_version: str) -> Plugin:
        """T8: new_version must be > current; push full current manifest to history."""
        try:
            parse_version(new_version)
        except ValueError:
            raise PluginError(f"invalid new version: {new_version!r}") from None  # C2-03
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, plugin_id)
            if row is None:
                raise PluginError(f"plugin not found: {plugin_id}")
            current_version = row[2]
            if compare(new_version, current_version) <= 0:
                raise PluginError(
                    f"new version {new_version} must be > current {current_version}"
                )
            manifest = PluginManifest.model_validate_json(row[5])
            history = json.loads(row[6])
            history.append({
                "version": current_version,
                "manifest": manifest.model_dump(mode="json"),
                "at": _now_iso(),
            })
            new_manifest = manifest.model_copy(deep=True)
            new_manifest.version = new_version
            plugin = self._transition(
                plugin_id, "upgrade",
                {
                    "version": new_version,
                    "manifest_json": json.dumps(new_manifest.model_dump(mode="json"), ensure_ascii=False),
                    "history_json": json.dumps(history, ensure_ascii=False),
                },
            )
        self._emit(_EVENT_UPDATED, {"plugin_id": plugin_id, "version": new_version})
        return plugin

    def rollback(self, plugin_id: str) -> Plugin:
        """T9: restore previous manifest+version from history (dependent check)."""
        self._assert_no_dependents(plugin_id)
        with closing(self._connect()) as conn, conn:
            row = self._get_row(conn, plugin_id)
            if row is None:
                raise PluginError(f"plugin not found: {plugin_id}")
            history = json.loads(row[6])
            if not history:
                raise PluginStateError(f"plugin {plugin_id} has no history to roll back to")
            prev = history.pop()
            prev_manifest = PluginManifest.model_validate(prev["manifest"])
            plugin = self._transition(
                plugin_id, "rollback",
                {
                    "version": prev_manifest.version,
                    "manifest_json": json.dumps(prev_manifest.model_dump(mode="json"), ensure_ascii=False),
                    "history_json": json.dumps(history, ensure_ascii=False),
                },
            )
        self._emit(_EVENT_UPDATED, {"plugin_id": plugin_id, "version": plugin.version})
        return plugin

    def _assert_no_dependents(self, plugin_id: str) -> None:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT id, manifest_json, state FROM plugins").fetchall()
        for other_id, manifest_json, state in rows:
            if other_id == plugin_id or SkillState(state) == SkillState.REMOVED:
                continue
            try:
                manifest = PluginManifest.model_validate_json(manifest_json)
            except Exception:  # noqa: BLE001 — corrupt record
                continue
            for dep in manifest.dependencies:
                dep_id, _ = _parse_dependency(dep)
                if dep_id == plugin_id:
                    raise PluginDependencyError(
                        f"cannot modify {plugin_id}: plugin {other_id} depends on it"
                    )

    def remove(self, plugin_id: str) -> Plugin:
        """T10: terminal state — dependent check first."""
        self._assert_no_dependents(plugin_id)
        plugin = self._transition(plugin_id, "remove")
        self._rebuild_provides()
        self._emit(_EVENT_REMOVED, {"plugin_id": plugin_id})
        return plugin

    # -- reads ----------------------------------------------------------------

    def get(self, plugin_id: str) -> Plugin | None:
        with closing(self._connect()) as conn:
            row = self._get_row(conn, plugin_id)
        return self._row_to_plugin(row) if row is not None else None

    def list(self) -> list[Plugin]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM plugins ORDER BY id").fetchall()
        return [self._row_to_plugin(row) for row in rows]

    def list_by_state(self, state: SkillState) -> list[Plugin]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM plugins WHERE state=? ORDER BY id", (state.value,)
            ).fetchall()
        return [self._row_to_plugin(row) for row in rows]

    def list_by_type(self, plugin_type: PluginType) -> list[Plugin]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM plugins WHERE plugin_type=? ORDER BY id", (plugin_type.value,)
            ).fetchall()
        return [self._row_to_plugin(row) for row in rows]
