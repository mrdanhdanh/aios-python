"""Stable public DTOs for AIOS SDK v1."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = "1.0"


def _dump(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, tuple):
        return [_dump(item) for item in value]
    if isinstance(value, list):
        return [_dump(item) for item in value]
    if isinstance(value, dict):
        return {key: _dump(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class AgentRequest:
    input: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **_dump(asdict(self))}


@dataclass(frozen=True)
class AgentResponse:
    output: str
    status: str = "completed"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "AgentResponse":
        allowed = {"output", "status", "metadata", "schema_version"}
        unknown = set(value) - allowed
        if unknown or "output" not in value:
            raise ValueError(f"invalid agent response fields: {sorted(unknown)}")
        return cls(str(value["output"]), str(value.get("status", "completed")), dict(value.get("metadata", {})))

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **_dump(asdict(self))}


@dataclass(frozen=True)
class ToolInput:
    value: Any
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **_dump(asdict(self))}


@dataclass(frozen=True)
class ToolOutput:
    value: Any
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ToolOutput":
        allowed = {"value", "success", "metadata", "schema_version"}
        unknown = set(value) - allowed
        if unknown or "value" not in value:
            raise ValueError(f"invalid tool response fields: {sorted(unknown)}")
        return cls(value["value"], bool(value.get("success", True)), dict(value.get("metadata", {})))

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **_dump(asdict(self))}


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return _dump(asdict(self))


@dataclass(frozen=True)
class ChatResponse:
    message: ChatMessage
    model: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **_dump(asdict(self))}
