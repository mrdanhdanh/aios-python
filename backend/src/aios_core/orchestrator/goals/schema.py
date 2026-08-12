"""Shared SQLite DDL for the goals plane (review R1/R2).

Defined once so GoalManager and TaskQueue initialize the SAME schema
idempotently — ``cancel_goal`` cascade touches ``queue_items`` even when only
GoalManager was constructed.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS goals (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL CHECK (status IN ('active','paused','completed','failed','cancelled')),
    progress    REAL NOT NULL DEFAULT 0.0,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS goal_tasks (
    id            TEXT PRIMARY KEY,
    goal_id       TEXT NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    workflow_name TEXT NOT NULL,
    status        TEXT NOT NULL CHECK (status IN ('pending','queued','running','completed','failed','paused','cancelled')),
    priority      INTEGER NOT NULL DEFAULT 0,
    position      INTEGER NOT NULL DEFAULT 0,
    result        TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_goal_tasks_goal ON goal_tasks(goal_id);

CREATE TABLE IF NOT EXISTS queue_items (
    id            TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    priority      INTEGER NOT NULL DEFAULT 0,
    status        TEXT NOT NULL CHECK (status IN ('queued','running','paused','cancelled','completed','failed')),
    payload_json  TEXT NOT NULL DEFAULT '{}',
    task_id       TEXT,
    goal_id       TEXT,
    position      INTEGER NOT NULL UNIQUE,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_queue_status_prio ON queue_items(status, priority DESC, position ASC);
"""
