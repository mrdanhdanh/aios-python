"""Scenario loader (TASK-031, H3): dict / json / yaml → Scenario."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import Scenario
from .errors import ScenarioError


def load(source: dict[str, Any] | str | Path) -> Scenario:
    """Load một scenario: dict → validate; file (.json/.yaml/.yml) → parse.

    PyYAML bắt buộc safe_load (C2-07).
    """
    if isinstance(source, dict):
        return _validate(source)
    path = Path(source)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScenarioError(f"cannot read scenario file: {path}: {exc}") from exc
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ScenarioError(f"invalid JSON in {path}: {exc}") from exc
    else:
        try:
            import yaml
            data = yaml.safe_load(text)
        except Exception as exc:  # noqa: BLE001 — yaml parse errors vary
            raise ScenarioError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScenarioError(f"scenario file must contain an object: {path}")
    return _validate(data, context=str(path))


def load_many(source: dict[str, Any] | str | Path) -> list[Scenario]:
    """Load nhiều scenario: file chứa list hoặc key `scenarios:` (C3-04)."""
    if isinstance(source, dict):
        items = source.get("scenarios", source) if isinstance(source.get("scenarios"), list) else [source]
        return [_validate(item, context=f"scenario:{item.get('id', '?')}") for item in items]
    path = Path(source)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        import yaml
        data = yaml.safe_load(text)
    if isinstance(data, dict) and isinstance(data.get("scenarios"), list):
        data = data["scenarios"]
    if not isinstance(data, list):
        raise ScenarioError(f"expected a list of scenarios: {path}")
    return [_validate(item, context=f"{path}:{i}") for i, item in enumerate(data)]


def _validate(data: Any, context: str = "") -> Scenario:
    if not isinstance(data, dict):
        raise ScenarioError(f"scenario must be an object ({context})".strip())
    if "request" not in data.get("input", {}):
        raise ScenarioError(f"scenario.input.request is required: {data.get('id', context)}")
    mode = (data.get("environment") or {}).get("mode")
    if mode is not None and mode != "simulation":
        raise ScenarioError(f"environment.mode must be 'simulation' (v1): {data.get('id', context)}")
    try:
        return Scenario.model_validate(data)
    except Exception as exc:  # noqa: BLE001 — pydantic ValidationError
        raise ScenarioError(f"invalid scenario {data.get('id', context)}: {exc}") from exc
