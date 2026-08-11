"""Logging setup: console (human-readable) + JSON-lines file.

Correlation ids flow through a ``contextvars.ContextVar`` so log records
emitted inside an async/thread context carry the same ``correlation_id``.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings

#: Correlation id bound to the current execution context (async-safe).
correlation_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "aios_correlation_id", default=None
)

#: JSON field set — kept stable so P8 observability does not have to change format.
JSON_FIELDS = ("ts", "level", "logger", "message", "correlation_id")

_configured = False


class CorrelationIdFilter(logging.Filter):
    """Attach ``correlation_id`` from the context var to every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        cid = getattr(record, "correlation_id", None)
        if cid is not None:
            payload["correlation_id"] = cid
        return json.dumps(payload, ensure_ascii=False)


def set_correlation_id(correlation_id: str | None) -> None:
    """Set the correlation id for the current execution context."""
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> str | None:
    return correlation_id_var.get()


def setup_logging(settings: Settings | None = None) -> None:
    """Configure root logging once (idempotent)."""
    global _configured
    if _configured:
        return

    settings = settings or Settings()
    root = logging.getLogger()
    root.setLevel(settings.logging.level.upper())

    if settings.logging.console:
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        console.addFilter(CorrelationIdFilter())
        root.addHandler(console)

    if settings.logging.file:
        log_path = Path(settings.logging.file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(JsonFormatter())
        file_handler.addFilter(CorrelationIdFilter())
        root.addHandler(file_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger for ``name`` (ensure logging is set up)."""
    setup_logging()
    return logging.getLogger(name)
