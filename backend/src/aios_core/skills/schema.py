"""Shared SQLite DDL for skills (TASK-015). CHECK constraints generated from
the same constants as base.py to prevent drift (C1-17)."""

from .base import _ALL_SOURCES, _ALL_STATES

_STATES_SQL = ", ".join(f"'{s}'" for s in _ALL_STATES)
_SOURCES_SQL = ", ".join(f"'{s}'" for s in _ALL_SOURCES)

SKILLS_SCHEMA_SQL = f"""
CREATE TABLE IF NOT EXISTS skills (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    version       TEXT NOT NULL,
    source        TEXT NOT NULL CHECK (source IN ({_SOURCES_SQL})),
    state         TEXT NOT NULL CHECK (state IN ({_STATES_SQL})),
    manifest_json TEXT NOT NULL DEFAULT '{{}}',
    history_json  TEXT NOT NULL DEFAULT '[]',
    installed_at  TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
"""
