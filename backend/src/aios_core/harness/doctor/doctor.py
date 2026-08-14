"""DoctorHarness (TASK-034, H5): 13 doctor checks qua H1 runner."""

from __future__ import annotations

from typing import Any

from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..registry import Harness
from .checks import DoctorChecks
from .contracts import DoctorKind, DoctorResult, DoctorStatus
from .errors import DoctorError

logger = get_logger("aios.harness.doctor")


class DoctorHarness(Harness):
    """H5 harness: id="doctor" — chạy doctor checks per kind."""

    id = "doctor"
    name = "Doctor"
    version = "1.0.0"
    description = "Run 13-kind doctor checks (architecture..evidence)"

    def __init__(self, checks: DoctorChecks, *,
                 state_service: StateService | None = None) -> None:
        self._checks = checks
        self._state = state_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        kinds = ctx.config.get("kinds")  # list[str] | None (C1-01)
        selected: list[DoctorKind] | None = None
        if kinds is not None:
            try:
                selected = [DoctorKind(k) if isinstance(k, str) else k
                            for k in kinds]
            except ValueError as exc:
                raise DoctorError(f"invalid doctor kind: {exc}") from exc
        results = self._checks.run_all(selected)
        ctx.config["_results"] = results
        return [r.model_dump(mode="json") for r in results]

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        results = ctx.config.get("_results")
        if results is None:
            raise DoctorError("no results — run() not executed")
        strict = bool(ctx.config.get("strict", False))
        self._persist(ctx, results, strict)
        errors = [r for r in results if r.status == DoctorStatus.ERROR]
        if errors:  # P3-01: ERROR raise (WARNING/UNKNOWN không)
            if strict:
                raise DoctorError(
                    f"doctor error on {[e.kind.value for e in errors]}")
            logger.warning("doctor warning (strict=False): %d error(s)",
                           len(errors))

    # -- persistence ----------------------------------------------------------

    def _persist(self, ctx: HarnessContext, results: list[DoctorResult],
                 strict: bool) -> None:
        if self._state is None:
            return
        try:
            self._state.update_state(ctx.run_id, doctor={
                "results": [r.model_dump(mode="json") for r in results],
                "summary": {r.kind.value: r.status.value for r in results},
                "strict": strict,
                "metrics": {
                    "doctors_run": len(results),
                    "passed": sum(1 for r in results
                                  if r.status == DoctorStatus.PASS),
                    "warning": sum(1 for r in results
                                   if r.status == DoctorStatus.WARNING),
                    "error": sum(1 for r in results
                                 if r.status == DoctorStatus.ERROR),
                    "unknown": sum(1 for r in results
                                   if r.status == DoctorStatus.UNKNOWN),
                },
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("doctor state persist failed: %s", exc)

    # -- queries --------------------------------------------------------------

    def get_results(self, run_id: str) -> dict[str, Any] | None:
        if self._state is None:
            return None
        state = self._state.get_state(run_id)
        if not state or "doctor" not in state:
            return None
        return state["doctor"]
