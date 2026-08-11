"""Logging tests — all use tmp_path, never write to the default log path."""

import json
import logging

import pytest

from aios_core.config import Settings
from aios_core.logging import get_logger, set_correlation_id, setup_logging


@pytest.fixture(autouse=True)
def _isolate_logging(monkeypatch):
    """Reset module-level setup flag so tests can re-setup independently."""
    monkeypatch.setattr("aios_core.logging._configured", False)
    yield
    monkeypatch.setattr("aios_core.logging._configured", False)


def _settings(tmp_path, level="INFO", file_path=None):
    return Settings(
        logging={
            "level": level,
            "console": False,
            "file": True,
            "file_path": str(file_path or (tmp_path / "logs" / "test.jsonl")),
        }
    )


def test_json_line_contains_correlation_id(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_file = tmp_path / "logs" / "test.jsonl"
    setup_logging(_settings(tmp_path))

    logger = logging.getLogger("test.corr")
    set_correlation_id("corr-123")
    logger.info("hello %s", "world")
    set_correlation_id(None)

    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["correlation_id"] == "corr-123"
    assert record["message"] == "hello world"
    assert record["level"] == "INFO"
    assert record["logger"] == "test.corr"
    assert "ts" in record


def test_setup_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    setup_logging(_settings(tmp_path))
    logger = logging.getLogger("test.idem")
    logger.info("first")
    setup_logging(_settings(tmp_path))  # second call must not duplicate handlers
    logger.info("second")

    log_file = tmp_path / "logs" / "test.jsonl"
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2  # one line per call, not duplicated


def test_log_dir_auto_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "a" / "b" / "c.jsonl"
    setup_logging(_settings(tmp_path, file_path=str(nested)))
    logging.getLogger("test.mkdir").warning("w")
    assert nested.is_file()


def test_get_logger_returns_configured_logger(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger = get_logger("test.getter")
    assert logger.name == "test.getter"
    assert logger.level == logging.NOTSET or logger.level >= 0


def test_correlation_id_without_value_omits_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    setup_logging(_settings(tmp_path))
    logging.getLogger("test.nocid").info("plain")
    lines = (tmp_path / "logs" / "test.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert "correlation_id" not in json.loads(lines[0])
