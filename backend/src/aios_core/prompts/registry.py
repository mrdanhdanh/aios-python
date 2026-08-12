"""Prompt registry: versioned templates with evaluations."""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from ..semver import compare, parse_version
from .errors import PromptError

logger = logging.getLogger(__name__)

# Only `{identifier}` fields (no format spec, no positional, no spaces).
_FIELD_RE = re.compile(r"(?<!\{)\{([A-Za-z_]\w*)\}(?!\})")


class PromptTemplate(BaseModel):
    """A versioned prompt template (v1: str.format subset).

    Variables are extracted AND validated at construction — invalid braces
    raise PromptError so a broken template can never exist.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    version: str
    template: str
    description: str = ""
    variables: list[str] = []

    @field_validator("version")
    @classmethod
    def _validate_version(cls, value: str) -> str:
        parse_version(value)
        return value

    @model_validator(mode="after")
    def _extract_and_validate(self) -> "PromptTemplate":
        variables: list[str] = []
        i = 0
        template = self.template
        while i < len(template):
            if template.startswith("{{", i) or template.startswith("}}", i):
                i += 2  # escape
                continue
            match = _FIELD_RE.match(template, i)
            if match:
                var = match.group(1)
                if var not in variables:
                    variables.append(var)
                i = match.end()
                continue
            if template[i] in "{":
                raise PromptError(f"invalid placeholder at position {i} in template {self.id!r}")
            i += 1
        self.variables = variables
        return self


@dataclass
class PromptEvaluation:
    version: str
    score: float
    note: str
    timestamp: str


class PromptRegistry:
    """Versioned prompt store with render + evaluation history."""

    def __init__(self) -> None:
        self._prompts: dict[str, dict[str, PromptTemplate]] = {}  # id -> {version -> prompt}
        self._evaluations: dict[str, list[PromptEvaluation]] = {}
        self._lock = threading.RLock()

    def register(self, prompt: PromptTemplate) -> None:
        if not isinstance(prompt, PromptTemplate):
            raise TypeError("register expects a PromptTemplate instance")
        with self._lock:
            versions = self._prompts.setdefault(prompt.id, {})
            if prompt.version in versions:
                logger.warning("Overwriting prompt %s v%s", prompt.id, prompt.version)
            versions[prompt.version] = prompt

    def get(self, id: str, version: str | None = None) -> PromptTemplate:
        with self._lock:
            versions = self._prompts.get(id)
            if versions is None:
                raise PromptError(f"Unknown prompt id: {id!r}")
            if version is not None:
                prompt = versions.get(version)
                if prompt is None:
                    raise PromptError(f"Unknown prompt version: {id}@{version}")
                return prompt
            # Latest by semver precedence.
            latest = max(versions.keys(), key=lambda v: (parse_version(v).major, parse_version(v).minor, parse_version(v).patch))
            return versions[latest]

    def list(self) -> list[str]:
        with self._lock:
            return list(self._prompts.keys())  # insertion order

    def render(self, id: str, variables: dict, version: str | None = None) -> str:
        prompt = self.get(id, version)
        try:
            return prompt.template.format(**variables)
        except KeyError as exc:
            raise PromptError(f"missing variable for {id!r}: {exc}") from exc
        except (ValueError, IndexError) as exc:
            raise PromptError(f"render failed for {id!r}: {exc}") from exc

    def evaluate(self, id: str, score: float, note: str = "") -> None:
        with self._lock:
            prompt = self.get(id)  # latest (read under the same lock)
            self._evaluations.setdefault(id, []).append(
                PromptEvaluation(
                    version=prompt.version,
                    score=score,
                    note=note,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )

    def evaluations(self, id: str, version: str | None = None) -> list[PromptEvaluation]:
        with self._lock:
            if id not in self._prompts:
                raise PromptError(f"Unknown prompt id: {id!r}")
            history = self._evaluations.get(id, [])
            if version is None:
                return list(history)
            return [e for e in history if e.version == version]
