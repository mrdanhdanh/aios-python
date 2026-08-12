"""Workflow definition: declarative, engine-agnostic (Contract-First)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..kernel.dag import validate_dag
from ..kernel.execution_plan import PlanNodeType
from ..kernel.services import PermissionScope
from ..semver import parse_version


class WorkflowNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: PlanNodeType
    name: str
    agent: str = ""
    capabilities: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    timeout_s: float | None = None  # None = fall through to definition default
    retries: int | None = None  # None = fall through; 0 = 1 attempt (engine)

    @model_validator(mode="after")
    def _validate_non_negative(self) -> "WorkflowNode":
        if self.timeout_s is not None and self.timeout_s < 0:
            raise ValueError("timeout_s must be >= 0")
        if self.retries is not None and self.retries < 0:
            raise ValueError("retries must be >= 0")
        return self


class WorkflowDefinition(BaseModel):
    """Declarative workflow contract — compiled to an engine plan."""

    model_config = ConfigDict(extra="forbid")

    name: str
    version: str
    description: str = ""
    nodes: list[WorkflowNode] = Field(min_length=1)
    retries: int = 0
    timeout_s: float = 300.0
    resources: dict[str, Any] = Field(default_factory=dict)
    permissions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty or whitespace-only")
        return stripped

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        parse_version(value)  # raises ValueError on invalid semver
        return value

    @field_validator("permissions")
    @classmethod
    def _validate_permissions(cls, value: list[str]) -> list[str]:
        known = {s.value for s in PermissionScope}
        unknown = [p for p in value if p not in known]
        if unknown:
            raise ValueError(f"unknown permission scopes: {unknown}")
        return value

    @model_validator(mode="after")
    def _validate_definition(self) -> "WorkflowDefinition":
        if self.retries < 0:
            raise ValueError("retries must be >= 0")
        if self.timeout_s < 0:
            raise ValueError("timeout_s must be >= 0")
        validate_dag(self.nodes)
        return self

    @property
    def edges(self) -> list[tuple[str, str]]:
        """Read-only derived edges (display/debug)."""
        edges: list[tuple[str, str]] = []
        for node in self.nodes:
            for dep in node.depends_on:
                edges.append((dep, node.id))
        return edges

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowDefinition":
        return cls.model_validate(data)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "WorkflowDefinition":
        """Load from YAML (raises FileNotFoundError/yaml.YAMLError naturally)."""
        with Path(path).open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        return cls.model_validate(data)
