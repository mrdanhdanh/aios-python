"""CoverageHarness (M13-P1, TASK-090): id="coverage".

Coverage model 9 chiều + negative-path 8 + Harness Readiness 7 dims.
Chạy qua H1 runner lifecycle (INV-017/018): run() → coverage + readiness;
verify() → strict fail-closed (INV-035): NOT_READY → raise CoverageError.
Persist qua state_service (pattern TASK-089/benchmark).
"""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness, HarnessRegistry
from .coverage import HarnessCoverage
from .contracts import HarnessReadinessReport, HarnessReadinessStatus
from .errors import CoverageError
from .readiness import HarnessReadinessScorer

logger = get_logger("aios.harness.coverage")


class CoverageHarness(Harness):
    """M13-P1 harness: id="coverage" — coverage model + readiness score.

    "coverage" ở đây = Harness Coverage model (độ phủ kiểm chứng) — KHÁC
    test coverage / ArtifactType.COVERAGE / CheckKind.COVERAGE (P3-1 v1).
    """

    id = "coverage"
    name = "Harness Coverage & Readiness"
    version = "1.0.0"
    description = "Coverage model 9 chiều + negative-path + readiness score (M13-P1)"

    def __init__(
        self,
        registry: HarnessRegistry,
        scorer: HarnessReadinessScorer | None = None,
        *,
        state_service: StateService | None = None,
    ) -> None:
        self._coverage = HarnessCoverage(registry)
        self._scorer = scorer or HarnessReadinessScorer()
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        coverage = self._coverage.build()
        # override qua config (nếu muốn thay đổi ngưỡng per-run)
        min_overall = float(ctx.config.get("min_overall", 0.8))
        min_replay = float(ctx.config.get("min_replay", 0.75))
        production = bool(ctx.config.get("production_tests_available", False))
        scorer = HarnessReadinessScorer(
            min_overall=min_overall, min_replay=min_replay,
            production_tests_available=production)
        readiness = scorer.score(coverage)
        payload = {
            "coverage": coverage.model_dump(mode="json"),
            "readiness": readiness.model_dump(mode="json"),
        }
        ctx.config["_payload"] = payload
        return payload

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        """Persist TRƯỚC raise (pattern H2 AC5); strict → fail-closed (INV-035)."""
        data = ctx.config.get("_payload")
        if data is None:
            raise CoverageError("no payload — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, data, strict)
        if data["readiness"]["status"] != HarnessReadinessStatus.READY.value:
            if strict:
                raise CoverageError(
                    f"harness readiness NOT READY: {data['readiness']['summary']}")
            logger.warning("coverage warning (strict=False): %s",
                           data["readiness"]["summary"])

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, data: dict,
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, coverage_report={
                "coverage_overall": data["coverage"]["overall_ratio"],
                "negative_path_ratio": data["coverage"]["negative_path_ratio"],
                "readiness_status": data["readiness"]["status"],
                "readiness_overall": data["readiness"]["overall"],
                "hard_gates": data["readiness"]["hard_gates"],
                "coverage_metrics": data["coverage"]["metrics"],
                "readiness_metrics": data["readiness"]["metrics"],
                "summary": data["readiness"]["summary"],
                "strict": strict,
            })
        except Exception as exc:  # noqa: BLE001 — evidence không chặn verdict
            logger.warning("coverage state persist failed: %s", exc)

    # -- queries --------------------------------------------------------------

    def get_report(self, run_id: str) -> dict[str, Any] | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "coverage_report" not in state:
            return None
        return state["coverage_report"]