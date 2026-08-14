"""EvaluationHarness (TASK-032, H4): đánh giá output + trajectory theo suite."""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .contracts import (
    EvaluationItem, EvaluationKind, EvaluationResult, EvaluationStatus,
    Score, Suite, Trajectory,
)
from .errors import EvaluationError
from .evaluators import Engine
from .trajectory import TrajectoryEvaluator

logger = get_logger("aios.harness.evaluation")


class EvaluationHarness(Harness):
    """H4 harness: id="evaluation" — suite metrics + thresholds + trajectory."""

    id = "evaluation"
    name = "Evaluation"
    version = "1.0.0"
    description = "Evaluate outputs and trajectories against a suite"

    def __init__(self, engine: Engine | None = None, *,
                 state_service: StateService | None = None,
                 max_items: int = 1000) -> None:
        self._engine = engine or Engine()
        self._state = state_service
        self._max_items = max_items
        self._trajectories = TrajectoryEvaluator()

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        suite = ctx.config.get("suite")
        if suite is None:
            raise EvaluationError("ctx.config['suite'] missing (Suite)")
        items = ctx.config.get("items") or []
        items = list(items)[: self._max_items]  # C2-06 cap
        result = self._evaluate(suite, items)
        ctx.config["_result"] = result
        return result.model_dump(mode="json")

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        result = ctx.config.get("_result")
        if result is None:
            raise EvaluationError("no result — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, result, strict)
        if not result.passed_all:
            if strict:
                raise EvaluationError(f"evaluation failed: {result.summary}")
            logger.warning("evaluation warning (strict=False): %s", result.summary)

    # -- evaluation -----------------------------------------------------------

    def _evaluate(self, suite: Suite, items: list[EvaluationItem]) -> EvaluationResult:
        trajectory_by_item: list[Trajectory] = []
        per_metric: dict[str, list[float]] = {}
        reproducible: dict = {}
        for item in items:
            for metric in suite.metrics:
                score = self._engine.score(
                    metric, item, suite.thresholds.get(metric.name))
                if score.value is not None:
                    per_metric.setdefault(metric.name, []).append(score.value)
                if metric.kind == EvaluationKind.LLM_JUDGE:
                    reproducible.update(self._engine.reproducible(metric))
            if item.trajectory:
                trajectory_by_item.append(self._trajectories.analyze(item.trajectory))

        scores: list[Score] = []
        for metric in suite.metrics:
            values = per_metric.get(metric.name, [])
            threshold = suite.thresholds.get(metric.name, self._engine._default_threshold)
            if not values:
                scores.append(Score(metric=metric.name, value=None,
                                    threshold=threshold, passed=False,
                                    kind=metric.kind))  # R2-2: all None → inconclusive
            else:
                mean = sum(values) / len(values)
                scores.append(Score(metric=metric.name, value=mean,
                                    threshold=threshold, passed=mean >= threshold,
                                    kind=metric.kind))

        passed_all = bool(scores) and all(s.passed for s in scores)  # C2-07
        inconclusive = any(s.value is None for s in scores)
        status = (EvaluationStatus.PASSED if passed_all else
                  EvaluationStatus.INCONCLUSIVE if inconclusive
                  else EvaluationStatus.FAILED)
        trajectory = trajectory_by_item[0] if trajectory_by_item else None  # P1-01
        return EvaluationResult(
            suite_id=suite.id, dataset=suite.dataset, scores=scores,
            passed_all=passed_all, status=status, trajectory=trajectory,
            summary=self._summarize(status, scores),
            metrics={"items_total": len(items), "items_with_trajectory": len(trajectory_by_item),
                     "metrics_total": len(scores),
                     "metrics_passed": sum(1 for s in scores if s.passed),
                     "inconclusive": int(inconclusive)},
            reproducible=reproducible,
        )

    @staticmethod
    def _summarize(status: EvaluationStatus, scores: list[Score]) -> str:
        parts = [f"{status.value}"]
        for score in scores:
            value = "n/a" if score.value is None else f"{score.value:.3f}"
            parts.append(f"{score.metric}={value}/{score.threshold}")
        return "; ".join(parts)

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, result: EvaluationResult,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, evaluation={
                "suite_id": result.suite_id,
                "passed_all": result.passed_all,
                "status": result.status.value,
                "scores": [s.model_dump(mode="json") for s in result.scores],
                "summary": result.summary,
                "metrics": result.metrics,
                "reproducible": result.reproducible,
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("evaluation state persist failed: %s", exc)

    # -- queries --------------------------------------------------------------

    def get_result(self, run_id: str) -> dict[str, Any] | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "evaluation" not in state:
            return None
        return state["evaluation"]
