"""Configuration loading with YAML + environment override.

Search order:
    1. `AIOS_CONFIG_PATH` (env) — explicit path to a YAML file
    2. `<CWD>/config.yaml`
    3. Built-in defaults (pydantic model defaults)

Precedence: env > YAML > model defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX = "AIOS_"
CONFIG_PATH_ENV = "AIOS_CONFIG_PATH"
DEFAULT_CONFIG_FILE = "config.yaml"

#: Env vars that control the loader itself, not settings fields.
_LOADER_ENV_VARS = {CONFIG_PATH_ENV}


class AppSettings(BaseModel):
    name: str = "aios"
    env: str = "dev"


class LoggingSettings(BaseModel):
    level: str = "INFO"
    console: bool = True
    file: bool = True
    file_path: str = "aios/logs/aios.jsonl"


class AuditSettings(BaseModel):
    db_path: str = "aios/data/audit.db"


class ArtifactsSettings(BaseModel):
    dir: str = "aios/data/artifacts"


class ResourcesSettings(BaseModel):
    max_tokens: int | None = None
    max_concurrent: int | None = None


class RoutingRuleSettings(BaseModel):
    """Mirror of PolicyRule (config-local, no import from models)."""

    model_config = ConfigDict(extra="forbid")

    max_cost: float | None = None
    max_latency_ms: int | None = None
    min_quality: float | None = None
    providers: list[str] | None = None


class RoutingSettings(BaseModel):
    """Routing policy config (PLAN §8): default balanced + named policies."""

    model_config = ConfigDict(extra="forbid")

    default: str = "balanced"
    policies: dict[str, RoutingRuleSettings] = Field(default_factory=dict)


class ModelsSettings(BaseModel):
    """TASK-025: +routing policy (extra=forbid — typo nested bị chặn, C2-04)."""

    model_config = ConfigDict(extra="forbid")

    default: str = "mock"
    routing: RoutingSettings = RoutingSettings()


class RoutingSettings(BaseModel):
    """Routing policy config (PLAN §8): default balanced + named policies."""

    model_config = ConfigDict(extra="forbid")

    default: str = "balanced"
    policies: dict[str, RoutingRuleSettings] = Field(default_factory=dict)


class MemoryBudgetSettings(BaseModel):
    """TASK-023: token budget caps per category (PLAN §3.3, total 20K).

    ``system``/``reserve`` are reserved for TASK-024 Context Optimizer.
    Mirrors memory.contracts.MemoryBudget (same schema, local to config).
    """

    system: int = 3000
    task: int = 2000
    knowledge: int = 6000
    history: int = 5000
    artifacts: int = 3000
    reserve: int = 1000


class MemorySettings(BaseModel):
    conversation_db_path: str = "aios/data/conversations.db"
    knowledge_db_path: str = "aios/data/knowledge.db"
    budget: MemoryBudgetSettings = MemoryBudgetSettings()


class GoalsSettings(BaseModel):
    """TASK-012: Goal Manager + Task Queue persistence (shared goals.db)."""

    db_path: str = "aios/data/goals.db"


class SkillsSettings(BaseModel):
    """TASK-017: SkillManager persistence (C2-01)."""

    db_path: str = "aios/data/skills.db"


class ObservabilitySettings(BaseModel):
    """TASK-021: metrics/prompt-history/evaluations persistence."""

    db_path: str = "aios/data/observability.db"


class PlanningSettings(BaseModel):
    """TASK-026: planning engine tuning (INV-014 validation bounds)."""

    model_config = ConfigDict(extra="forbid")

    max_nodes: int = 32
    default_timeout_s: float = 300.0
    min_timeout_s: float = 1.0
    max_timeout_s: float = 3600.0
    warn_token_threshold: int = 20_000


class GraphSettings(BaseModel):
    """TASK-027: execution graph tuning (INV-015 bounds).

    ``default_failure_policy`` is consumed by TASK-028 when building graphs
    via plan_to_graph; the executor reads the policy from the graph itself.
    """

    model_config = ConfigDict(extra="forbid")

    max_parallel: int = 1
    default_failure_policy: str = "fail_fast"

    @field_validator("max_parallel")
    @classmethod
    def _validate_parallel(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_parallel must be >= 1")
        return value

    @field_validator("default_failure_policy")
    @classmethod
    def _validate_policy(cls, value: str) -> str:
        if value not in ("fail_fast", "continue", "skip_dependents"):
            raise ValueError(f"unknown failure policy: {value!r}")
        return value


class SchedulerSettings(BaseModel):
    """TASK-028: graph scheduler tuning (INV-016 bounds).

    ``resource_wait_timeout_s=None`` = wait forever (FIFO fair — F-003).
    """

    model_config = ConfigDict(extra="forbid")

    resource_wait_timeout_s: float | None = None

    @field_validator("resource_wait_timeout_s")
    @classmethod
    def _validate_timeout(cls, value: float | None) -> float | None:
        if value is not None and value < 0:
            raise ValueError("resource_wait_timeout_s must be >= 0 (or None)")
        return value


class HarnessSettings(BaseModel):
    """TASK-029: harness kernel tuning (M6-H1)."""

    model_config = ConfigDict(extra="forbid")

    diagnose_on_failure: bool = True


class ExecutionSettings(BaseModel):
    """TASK-030: execution verification tuning (M6-H2)."""

    model_config = ConfigDict(extra="forbid")

    event_window: int = 10_000  # P2-01: query_audit limit (truncation heuristic)
    persist_verdict_artifact: bool = True  # AC5: verdict.json convention P2-05


class TestingSettings(BaseModel):
    """TASK-031: test & simulation tuning (M6-H3)."""

    model_config = ConfigDict(extra="forbid")

    default_retries: int = 1  # P3-02: fault retries mặc định
    strict: bool = True  # TestHarness: MISMATCH/ERROR → raise
    simulation_timeout_s: float = 30.0  # reserved (runner không block v1)


class Settings(BaseSettings):
    """Application settings. Env vars use `AIOS_` prefix, nested via `__`."""

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_nested_delimiter="__",
        extra="forbid",
        case_sensitive=False,
    )

    app: AppSettings = AppSettings()
    logging: LoggingSettings = LoggingSettings()
    audit: AuditSettings = AuditSettings()
    artifacts: ArtifactsSettings = ArtifactsSettings()
    resources: ResourcesSettings = ResourcesSettings()
    models: ModelsSettings = ModelsSettings()
    memory: MemorySettings = MemorySettings()
    goals: GoalsSettings = GoalsSettings()
    skills: SkillsSettings = SkillsSettings()
    observability: ObservabilitySettings = ObservabilitySettings()
    planning: PlanningSettings = PlanningSettings()
    graph: GraphSettings = GraphSettings()
    scheduler: SchedulerSettings = SchedulerSettings()
    harness: HarnessSettings = HarnessSettings()
    execution: ExecutionSettings = ExecutionSettings()
    testing: TestingSettings = TestingSettings()


def _yaml_extra_keys_guard(data: dict) -> None:
    """Reject unknown top-level keys in the YAML file (extra='forbid')."""
    known = set(Settings.model_fields.keys())
    unknown = set(data.keys()) - known
    if unknown:
        raise ValidationError.from_exception_data(
            "Settings",
            [{"type": "extra_forbidden", "loc": (sorted(unknown)[0],), "msg": "Extra inputs are not permitted"}],
        )


def _validate_env_vars() -> None:
    """Reject unknown `AIOS_*` env vars (pydantic-settings does NOT do this).

    Whitelist: loader env vars (e.g. AIOS_CONFIG_PATH) are not settings fields.
    """
    known = set(Settings.model_fields.keys())
    unknown = []
    for key in os.environ:
        if not key.startswith(ENV_PREFIX):
            continue
        if key in _LOADER_ENV_VARS:
            continue
        # Strip prefix, take the root field (before nested delimiter).
        field = key[len(ENV_PREFIX) :].lower()
        root = field.split("__")[0].split(".")[0]
        if root not in known:
            unknown.append(key)
    if unknown:
        raise ValueError(f"Unknown AIOS_* env vars (typo?): {sorted(unknown)}")


def load_settings(config_path: str | Path | None = None) -> Settings:
    """Load settings following the documented search order.

    Raises:
        ValueError: unknown `AIOS_*` env var.
        ValidationError: invalid YAML content or env value types.
    """
    _validate_env_vars()

    yaml_data: dict = {}

    # 1. Explicit path via env or argument.
    if config_path is None:
        config_path = os.environ.get(CONFIG_PATH_ENV)
    if config_path is not None:
        path = Path(config_path)
        if path.is_file():
            yaml_data = _load_yaml(path)
        # Missing explicit path → fall through to CWD (no crash).

    # 2. CWD config.yaml.
    if not yaml_data:
        cwd_file = Path.cwd() / DEFAULT_CONFIG_FILE
        if cwd_file.is_file():
            yaml_data = _load_yaml(cwd_file)

    if yaml_data:
        _yaml_extra_keys_guard(yaml_data)

    # 3. Model defaults fill the rest; env overrides on top.
    return Settings(**yaml_data)


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must contain a mapping at top level")
    return data


def config_paths() -> list[Path]:
    """Return candidate config paths in search order (for diagnostics)."""
    paths: list[Path] = []
    env_path = os.environ.get(CONFIG_PATH_ENV)
    if env_path:
        paths.append(Path(env_path))
    paths.append(Path.cwd() / DEFAULT_CONFIG_FILE)
    return paths
