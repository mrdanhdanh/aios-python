"""Suite loader (TASK-032, H4): dict / json / yaml (safe_load)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import Suite
from .errors import SuiteError


def load(source: dict[str, Any] | str | Path) -> Suite:
    if isinstance(source, dict):
        return _validate(source)
    path = Path(source)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SuiteError(f"cannot read suite file: {path}: {exc}") from exc
    data = _parse(text, path)
    if not isinstance(data, dict):
        raise SuiteError(f"suite file must contain an object: {path}")
    return _validate(data, context=str(path))


def load_many(source: dict[str, Any] | str | Path) -> list[Suite]:
    if isinstance(source, dict):
        items = source.get("suites")
        if isinstance(items, list):
            return [_validate(item, context=f"suite:{item.get('id', '?')}")
                    for item in items]
        return [_validate(source, context=f"suite:{source.get('id', '?')}")]
    path = Path(source)
    data = _parse(path.read_text(encoding="utf-8"), path)
    if isinstance(data, dict) and isinstance(data.get("suites"), list):
        data = data["suites"]
    if not isinstance(data, list):
        raise SuiteError(f"expected a list of suites: {path}")
    return [_validate(item, context=f"{path}:{i}") for i, item in enumerate(data)]


def _parse(text: str, path: Path) -> Any:
    if path.suffix.lower() == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise SuiteError(f"invalid JSON in {path}: {exc}") from exc
    try:
        import yaml
        return yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        raise SuiteError(f"invalid YAML in {path}: {exc}") from exc


def _validate(data: Any, context: str = "") -> Suite:
    if not isinstance(data, dict):
        raise SuiteError(f"suite must be an object ({context})".strip())
    try:
        suite = Suite.model_validate(data)
    except Exception as exc:  # noqa: BLE001 — pydantic ValidationError
        raise SuiteError(f"invalid suite {data.get('id', context)}: {exc}") from exc
    # thresholds lạ (không thuộc metric) → bỏ qua deterministic
    names = {m.name for m in suite.metrics}
    suite.thresholds = {k: v for k, v in suite.thresholds.items() if k in names}
    return suite
