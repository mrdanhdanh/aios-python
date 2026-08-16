"""CreativeMatcher (R11) — M11-P3 (TASK-081).

Offline-first, deterministic: gợi ý/route yêu cầu creative/asset tới
Capability đã đăng ký — đóng gap "reuse vs reimplement" (worker tự viết
PNG encoder dù skill sprite-forge đã có).

Scoring (deterministic, không LLM):
  kind_match   = 10/kind (request token ∈ capability kinds)
  keyword_hit  = 1/từ request xuất hiện trong description/name
  name_prefix  = 3 nếu request bắt đầu bằng tên capability
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .asset import AssetCapability
from .registry import AssetCapabilityRegistry

KIND_WEIGHT = 10
KEYWORD_WEIGHT = 1
PREFIX_WEIGHT = 3


@dataclass
class MatchResult:
    capability_id: str
    name: str
    score: int
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "score": self.score,
            "reason": self.reason,
        }


class CreativeMatcher:
    """Matcher creative/asset — deterministic, offline-first."""

    def __init__(self, registry: AssetCapabilityRegistry | None = None) -> None:
        self._registry = registry or AssetCapabilityRegistry()

    # -- tokenize -------------------------------------------------------------

    def _tokens(self, text: str) -> list[str]:
        return [t for t in text.lower().strip().split() if t]

    # -- match ----------------------------------------------------------------

    def match(
        self,
        request: str,
        kinds: list[str] | None = None,
    ) -> list[MatchResult]:
        """Match request → capabilities sorted theo score giảm dần."""
        tokens = self._tokens(request)
        candidates = self._registry.list()
        if kinds:
            candidates = [c for c in candidates if any(k in c.kinds for k in kinds)]

        results: list[MatchResult] = []
        for cap in candidates:
            score, reason_parts = self._score(cap, tokens, request)
            if score <= 0:
                continue
            results.append(MatchResult(
                capability_id=cap.id,
                name=cap.name,
                score=score,
                reason="; ".join(reason_parts) or "no reason",
            ))
        results.sort(key=lambda r: (-r.score, r.capability_id))
        return results

    def suggest(self, request: str) -> list[MatchResult]:
        """Gợi ý capability tồn tại cho request (top 3) — reuse > reimplement."""
        return self.match(request)[:3]

    # -- scoring ----------------------------------------------------------------

    def _score(
        self,
        cap: AssetCapability,
        tokens: list[str],
        request: str,
    ) -> tuple[int, list[str]]:
        score = 0
        parts: list[str] = []
        desc = (cap.description + " " + cap.name).lower()
        cap_kinds = set(cap.kinds)
        req_lower = request.lower()

        # kind match
        for tok in tokens:
            if tok in cap_kinds:
                score += KIND_WEIGHT
                parts.append(f"kind:{tok}")
        # keyword hit trong description/name
        for tok in tokens:
            if tok in desc:
                score += KEYWORD_WEIGHT
                parts.append(f"keyword:{tok}")
        # name prefix
        if req_lower.startswith(cap.name.lower()):
            score += PREFIX_WEIGHT
            parts.append("prefix")
        return score, parts
