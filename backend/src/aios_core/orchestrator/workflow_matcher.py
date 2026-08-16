"""Workflow matcher: reuse WorkflowLibrary (macro → full → token search).

M11-P3b (TASK-082, R6): thêm bước (0) creative pre-route TRƯỚC macro —
route "build a game"/"generate pixel art" tới CreativeMatcher (offline-first).
creative_matcher=None → bỏ qua pre-route (hành vi cũ 100%).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..workflow.errors import WorkflowError
from ..workflow.library import WorkflowLibrary

STOPWORDS = {"the", "a", "an", "please", "vui", "lòng", "làm", "for", "and", "to", "of", "with", "me"}

#: Từ khóa trigger creative (R6 — proposal M11 §R6). lower-case.
CREATIVE_TRIGGERS: tuple[str, ...] = (
    "creative", "game", "sprite", "pixel art", "tileset", "map",
    "audio", "animation", "ui asset", "phaser", "canvas",
)

#: Confidence cho creative pre-route (R6).
CREATIVE_CONFIDENCE = 0.85


@dataclass
class WorkflowMatch:
    workflow_name: str
    matched_by: str  # macro | full | token | creative
    confidence: float


class WorkflowMatcher:
    """Match request text to a registered workflow.

    ``library`` comes from the constructor (same instance shared with the
    normalizer — caller responsibility). ``creative_matcher`` optional
    (R6): có thì pre-route creative, không thì bỏ qua.
    """

    def __init__(
        self,
        library: WorkflowLibrary,
        creative_matcher: Any | None = None,
    ) -> None:
        self._library = library
        self._creative = creative_matcher

    def _templates(self) -> dict[str, str]:
        # v1: derive template keywords from workflow names (id-like).
        templates: dict[str, str] = {}
        for name in self._library.list():
            key = name.replace("_", " ").replace("-", " ")
            templates[key] = name
        return templates

    def _creative_pre_route(self, lowered: str) -> WorkflowMatch | None:
        """Bước (0) — R6: từ khóa creative → CreativeMatcher.suggest()."""
        if self._creative is None:
            return None
        if not any(t in lowered for t in CREATIVE_TRIGGERS):
            return None
        try:
            suggestions = self._creative.suggest(lowered)
        except Exception:  # noqa: BLE001 — pre-route không crash matcher
            return None
        if not suggestions:
            return None
        # suggest() trả list MatchResult (top 3) — lấy kết quả tốt nhất
        top = suggestions[0]
        cap_id = getattr(top, "capability_id", None) or getattr(top, "id", None)
        if not cap_id:
            return None
        return WorkflowMatch(f"creative:asset:{cap_id}", "creative", CREATIVE_CONFIDENCE)

    def match(self, text: str) -> WorkflowMatch | None:
        lowered = text.lower()

        # 0) Creative pre-route (M11-P3b/R6) — offline-first.
        creative = self._creative_pre_route(lowered)
        if creative is not None:
            return creative

        # 1) Template macro (the ONLY place that validates macros → workflow_name).
        for keyword, name in self._templates().items():
            if keyword and keyword in lowered:
                try:
                    self._library.get(name)  # validate existence
                except WorkflowError:
                    continue
                return WorkflowMatch(name, "macro", 0.9)

        # 2) Full-sentence search.
        full = self._library.search(lowered)
        if full:
            return self._pick(full[0], lowered, "full")

        # 3) Token search: first token with a match wins.
        tokens = [
            t for t in re.findall(r"\w+", lowered) if len(t) >= 3 and t not in STOPWORDS
        ]
        for token in tokens:
            found = self._library.search(token)
            if found:
                return self._pick(found[0], token, "token")
        return None

    def _pick(self, name: str, query: str, matched_by: str) -> WorkflowMatch:
        try:
            definition = self._library.get(name)
        except WorkflowError:
            return WorkflowMatch(name, matched_by, 0.6)
        if query in name.lower():
            confidence = 0.8
        else:
            confidence = 0.6
        return WorkflowMatch(name, matched_by, confidence)
