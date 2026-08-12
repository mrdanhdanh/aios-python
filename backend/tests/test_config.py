"""Config loading tests — all CWD-independent (tmp_path + monkeypatch)."""

import os

import pytest
from pydantic import ValidationError

from aios_core.config import CONFIG_PATH_ENV, ENV_PREFIX, load_settings


def _write_yaml(path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_defaults_when_no_file(tmp_path, monkeypatch):
    """No file anywhere (env unset, empty CWD) → model defaults, no crash."""
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    for key in list(os.environ):
        if key.startswith(ENV_PREFIX):
            monkeypatch.delenv(key)
    monkeypatch.chdir(tmp_path)
    settings = load_settings()
    assert settings.app.name == "aios"
    assert settings.logging.level == "INFO"
    assert settings.logging.file_path == "aios/logs/aios.jsonl"


def test_loads_cwd_config_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    _write_yaml(tmp_path / "config.yaml", "app:\n  name: custom\n")
    settings = load_settings()
    assert settings.app.name == "custom"
    assert settings.logging.level == "INFO"  # missing key → default


def test_missing_key_in_file_uses_default(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    _write_yaml(tmp_path / "config.yaml", "app:\n  name: custom\n")
    settings = load_settings()
    assert settings.logging.level == "INFO"


def test_env_override_nested(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)  # no config.yaml
    monkeypatch.setenv("AIOS_LOGGING__LEVEL", "DEBUG")
    settings = load_settings()
    assert settings.logging.level == "DEBUG"


def test_env_typo_raises_value_error(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIOS_LOGGNIG__LEVEL", "DEBUG")
    with pytest.raises(ValueError, match="LOGGNIG"):
        load_settings()


def test_env_wrong_type_raises_validation_error(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIOS_LOGGING__LEVEL", "not-a-level")
    # "not-a-level" is a str — accepted by pydantic; use a bool field instead
    monkeypatch.setenv("AIOS_LOGGING__CONSOLE", "not-a-bool")
    with pytest.raises(ValidationError):
        load_settings()


def test_config_path_env_wins(tmp_path, monkeypatch):
    """AIOS_CONFIG_PATH → that file wins over CWD config.yaml."""
    monkeypatch.chdir(tmp_path)
    _write_yaml(tmp_path / "config.yaml", "app:\n  name: from_cwd\n")
    custom = tmp_path / "custom" / "config.yaml"
    _write_yaml(custom, "app:\n  name: from_env\n")
    monkeypatch.setenv(CONFIG_PATH_ENV, str(custom))
    settings = load_settings()
    assert settings.app.name == "from_env"


def test_config_path_missing_falls_back_to_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(CONFIG_PATH_ENV, str(tmp_path / "nope" / "missing.yaml"))
    settings = load_settings()
    assert settings.app.name == "aios"


def test_yaml_extra_key_raises_validation_error(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    _write_yaml(tmp_path / "config.yaml", "unknown_section:\n  x: 1\n")
    with pytest.raises(ValidationError):
        load_settings()


def test_config_path_arg_overrides_env(tmp_path, monkeypatch):
    """Explicit argument path wins over env var."""
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    _write_yaml(a, "app:\n  name: from_a\n")
    _write_yaml(b, "app:\n  name: from_b\n")
    monkeypatch.setenv(CONFIG_PATH_ENV, str(a))
    settings = load_settings(config_path=b)
    assert settings.app.name == "from_b"


def test_audit_artifacts_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = load_settings()
    assert settings.audit.db_path == "aios/data/audit.db"
    assert settings.artifacts.dir == "aios/data/artifacts"


def test_audit_artifacts_from_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    _write_yaml(
        tmp_path / "config.yaml",
        "audit:\n  db_path: custom/audit.db\nartifacts:\n  dir: custom/arts\n",
    )
    settings = load_settings()
    assert settings.audit.db_path == "custom/audit.db"
    assert settings.artifacts.dir == "custom/arts"


def test_models_default(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = load_settings()
    assert settings.models.default == "mock"


def test_memory_settings(tmp_path, monkeypatch):
    monkeypatch.delenv(CONFIG_PATH_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    settings = load_settings()
    assert settings.memory.conversation_db_path == "aios/data/conversations.db"
    assert settings.memory.knowledge_db_path == "aios/data/knowledge.db"
