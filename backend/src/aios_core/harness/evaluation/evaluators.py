"""Evaluators (TASK-032, H4): deterministic → semantic → LLM stub → human
stub → composite. Offline deterministic — KHÔNG import aios_core.models."""

from __future__ import annotations

import re
from typing import Any

from .contracts import EvaluationItem, EvaluationKind, Metric, Score


class DeterministicEvaluator:
    """exact / contains / regex / numeric_ge / bool (parse fail → 0.0)."""

    def evaluate(self, metric: Metric, item: EvaluationItem) -> float:
        kind = metric.params.get("kind", "exact")
        output = item.output
        expected = item.expected
        try:
            if kind == "contains":
                return 1.0 if expected in output else 0.0
            if kind == "regex":
                return 1.0 if re.search(expected, output) else 0.0
            if kind == "numeric_ge":  # R2-1: cả 2 parse float
                return 1.0 if float(output) >= float(expected) else 0.0
            if kind == "bool":
                truthy = output.strip().lower() in ("true", "1", "yes", "ok")
                return 1.0 if truthy == (expected.strip().lower() in ("true", "1", "yes", "ok")) else 0.0
            return 1.0 if output == expected else 0.0  # exact (default)
        except (ValueError, TypeError, re.error):
            return 0.0  # C2-01/C2-02: parse fail deterministic


class SemanticEvaluator:
    """Jaccard token overlap — offline, deterministic (không LLM)."""

    def evaluate(self, metric: Metric, item: EvaluationItem) -> float:
        left = set(_tokens(item.output))
        right = set(_tokens(item.expected))
        if not left or not right:
            return 0.0
        union = left | right
        return len(left & right) / len(union)


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", text.lower())


class LLMJudgeEvaluator:
    """Stub offline — score từ item.score hoặc params (INV-020 reproducible)."""

    def evaluate(self, metric: Metric, item: EvaluationItem) -> float | None:
        if item.score is not None:
            return item.score
        score = metric.params.get("score")
        return float(score) if score is not None else None

    def reproducible(self, metric: Metric) -> dict:
        params = metric.params
        return {
            "model": params.get("model", ""),
            "prompt_version": params.get("prompt_version", ""),
            "temperature": params.get("temperature", 0.0),
        }


class HumanEvaluator:
    """Stub — score từ item.score hoặc params; không có → pending (None)."""

    def evaluate(self, metric: Metric, item: EvaluationItem) -> float | None:
        if item.score is not None:
            return item.score
        score = metric.params.get("score")
        return float(score) if score is not None else None


class CompositeEvaluator:
    """Weighted mean từ params.sub_scores (C2-03); không có → None."""

    def evaluate(self, metric: Metric, item: EvaluationItem) -> float | None:
        sub_scores = metric.params.get("sub_scores")
        if not isinstance(sub_scores, list) or not sub_scores:
            return None
        total_weight = 0.0
        weighted = 0.0
        for entry in sub_scores:
            value = entry.get("value")
            if value is None:
                continue
            weight = float(entry.get("weight", 1.0))
            weighted += float(value) * weight
            total_weight += weight
        if total_weight == 0:
            return None
        return weighted / total_weight


class Engine:
    """Dispatch theo kind; score với threshold (default 0.8 — C1-03)."""

    def __init__(self, *, default_threshold: float = 0.8) -> None:
        self._default_threshold = default_threshold
        self._evaluators: dict[EvaluationKind, Any] = {
            EvaluationKind.DETERMINISTIC: DeterministicEvaluator(),
            EvaluationKind.SEMANTIC: SemanticEvaluator(),
            EvaluationKind.LLM_JUDGE: LLMJudgeEvaluator(),
            EvaluationKind.HUMAN: HumanEvaluator(),
            EvaluationKind.COMPOSITE: CompositeEvaluator(),
        }

    def evaluate(self, metric: Metric, item: EvaluationItem) -> float | None:
        return self._evaluators[metric.kind].evaluate(metric, item)

    def score(self, metric: Metric, item: EvaluationItem,
              threshold: float | None = None) -> Score:
        value = self.evaluate(metric, item)
        threshold = threshold if threshold is not None else self._default_threshold
        return Score(metric=metric.name, value=value, threshold=threshold,
                     passed=value is not None and value >= threshold,
                     kind=metric.kind)

    def reproducible(self, metric: Metric) -> dict:
        evaluator = self._evaluators[metric.kind]
        if metric.kind == EvaluationKind.LLM_JUDGE and hasattr(evaluator, "reproducible"):
            return evaluator.reproducible(metric)
        return {}  # C3-03: chỉ LLM_JUDGE
