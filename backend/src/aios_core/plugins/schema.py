"""Shared SQLite DDL for plugins (TASK-044). CHECK constraints generated from
the same constants as contracts.py to prevent drift."""

from .contracts import _ALL_TYPES, _PLUGIN_STATES

_TYPES_SQL = ", ".join(f"'{t}'" for t in _ALL_TYPES)
_STATES_SQL = ", ".join(f"'{s}'" for s in _PLUGIN_STATES)

PLUGINS_SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS plugins (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    version       TEXT NOT NULL,
    plugin_type   TEXT NOT NULL CHECK (plugin_type IN ({_TYPES_SQL})),
    state         TEXT NOT NULL CHECK (state IN ({_STATES_SQL})),
    manifest_json TEXT NOT NULL DEFAULT '{{}}',
    history_json  TEXT NOT NULL DEFAULT '[]',
    installed_at  TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
"""
