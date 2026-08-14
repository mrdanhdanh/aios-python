"""Harness runner (TASK-029, H1): lifecycle orchestration + evidence (INV-018).

execute() = try (lifecycle hooks) / except (catch-all -> FAILED) / finally
(build evidence + report + persist) — every run produces artifacts even on
failure (C1-03, B1). Evidence via ArtifactService public API (INV-017).
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

from aios_core.contracts.artifact import ArtifactContract, ArtifactType
from aios_core.kernel.services.artifacts import ArtifactService
from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from .context import HarnessContext
from .contracts import (
    HarnessArtifact,
    HarnessReport,
    HarnessResult,
    HarnessRun,
    HarnessRunStatus,
    safe_run_id,
    utcnow,
)
from .errors import HarnessError, HarnessLifecycleError
from .lifecycle import HarnessLifecycle
from .registry import Harness

logger = get_logger("aios.harness.runner")

_PHASES: tuple[tuple[HarnessRunStatus, str], ...] = (
    (HarnessRunStatus.PREPARING, "prepare"),
    (HarnessRunStatus.VALIDATING, "validate"),
    (HarnessRunStatus.RUNNING, "run"),
)  # verify handled separately (needs payload); complete after verify


def _evidence_contract(run_id: str, kind: str) -> ArtifactContract:
    """9 required fields (C2-01/R1-1): id namespace `harness:{run_id}:{kind}`
    (≠ HarnessArtifact.id `{run_id}:{kind}` — B5)."""
    return ArtifactContract(
        id=f"harness:{run_id}:{kind}",
        name=f"harness-{kind}",
        version="1.0.0",
        author="aios-core",
        license="proprietary",
        contract_version="1.0.0",
        schema_version="1.0.0",
        type=ArtifactType.JSON,
        storage_path=f"harness/{safe_run_id(run_id)}/{kind}.json",
        metadata={"run_id": run_id, "kind": kind},
    )


class HarnessRunner:
    """Executes harness lifecycle and builds evidence for every run."""

    def __init__(
        self,
        state_service: StateService,
        artifact_service: ArtifactService | None = None,
        *,
        diagnose_on_failure: bool = True,
    ) -> None:
        self._state = state_service
        self._artifacts = artifact_service
        self._diagnose_on_failure = diagnose_on_failure
        self._executed: set[str] = set()  # duplicate run_id guard (C2-03)
        self._lock = threading.RLock()

    def create_context(
        self,
        harness: Harness,
        target: str,
        *,
        version: str | None = None,
        environment: str = "local",
        config: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> HarnessContext:
        return HarnessContext(
            run_id=run_id or f"harness:{harness.id}:{time.time_ns():x}",
            harness=harness.id,
            target=target,
            version=version,
            environment=environment,
            config=config or {},
            started_at=utcnow(),
        )

    def execute(self, harness: Harness, ctx: HarnessContext) -> HarnessReport:
        if ctx.run_id in self._executed:
            raise HarnessError(f"duplicate run_id: {ctx.run_id!r}")
        self._executed.add(ctx.run_id)

        events: list[Any] = []
        ctx.attach_sink(events.append)  # C3-06 v2: collector runner-owned
        run = HarnessRun(
            run_id=ctx.run_id, harness=harness.id, target=ctx.target,
            version=ctx.version, environment=ctx.environment,
            started_at=ctx.started_at)
        started = time.monotonic()
        payload: Any = None
        phase_count = 0
        error: Exception | None = None

        def set_failed(exc: Exception, phase: HarnessRunStatus) -> None:
            nonlocal run
            try:
                run = run.model_copy(update={
                    "status": HarnessLifecycle.transition(run.status, HarnessRunStatus.FAILED),
                    "error": str(exc)})
            except HarnessLifecycleError:
                run = run.model_copy(update={
                    "status": HarnessRunStatus.FAILED, "error": str(exc)})

        try:
            for status, hook_name in _PHASES:
                ctx.emit_event(status.value, f"entering {hook_name}")
                hook = getattr(harness, hook_name)
                if hook_name == "run":
                    payload = hook(ctx)
                else:
                    hook(ctx)
                phase_count += 1
                run = run.model_copy(update={"status": status})
            # verify
            ctx.emit_event(HarnessRunStatus.VERIFYING.value, "entering verify")
            harness.verify(ctx, payload)
            phase_count += 1
            run = run.model_copy(update={"status": HarnessRunStatus.VERIFYING})
            # complete
            ctx.emit_event(HarnessRunStatus.COMPLETED.value, "entering complete")
            harness.complete(ctx, payload)
            phase_count += 1
            run = run.model_copy(update={
                "status": HarnessLifecycle.transition(
                    run.status, HarnessRunStatus.COMPLETED)})
        except Exception as exc:  # noqa: BLE001 — hook/catch-all (B1)
            error = exc
            set_failed(exc, run.status)
            ctx.emit_event(HarnessRunStatus.FAILED.value,
                           f"failed: {exc}", level="error")
            try:
                harness.on_failure(ctx, exc)
            except Exception as hook_exc:  # noqa: BLE001 — C1-03
                logger.warning("on_failure hook failed: %s", hook_exc)
            if self._diagnose_on_failure:
                try:
                    harness.diagnose(ctx, exc)
                except Exception as hook_exc:  # noqa: BLE001 — C1-03
                    logger.warning("diagnose hook failed: %s", hook_exc)
                try:
                    run = run.model_copy(update={
                        "status": HarnessLifecycle.transition(
                            run.status, HarnessRunStatus.DIAGNOSED)})
                except HarnessLifecycleError:
                    pass
        finally:
            run = run.model_copy(update={"ended_at": utcnow()})  # B6: cả 2 nhánh
            duration_ms = int((time.monotonic() - started) * 1000)
            result = HarnessResult(
                run_id=run.run_id, status=run.status,
                summary=f"{run.harness}:{run.run_id} -> {run.status.value}",
                metrics={"duration_ms": duration_ms, "phase_count": phase_count})
            artifacts = self._build_evidence(ctx, run, events, result)
            result = result.model_copy(update={
                "artifacts": [a.id for a in artifacts]})  # B5
            report = HarnessReport(
                run_id=run.run_id, summary=result.summary,
                result=result, artifacts=artifacts, generated_at=utcnow())
            self._persist(run, result, artifacts)
        return report

    # -- evidence (INV-018) -----------------------------------------------------

    def _build_evidence(
        self, ctx: HarnessContext, run: HarnessRun, events: list[Any],
        result: HarnessResult,
    ) -> list[HarnessArtifact]:
        artifacts: list[HarnessArtifact] = []
        payloads = {
            "events": json.dumps(
                [e.model_dump(mode="json") for e in events],
                ensure_ascii=False).encode("utf-8"),  # B11
            "report": json.dumps(
                {"run": run.model_dump(mode="json"),
                 "result": result.model_dump(mode="json")},
                ensure_ascii=False).encode("utf-8"),
        }
        for kind, content in payloads.items():
            artifact = HarnessArtifact(
                id=f"{run.run_id}:{kind}",  # deterministic (C2-02/B5)
                run_id=run.run_id, kind=kind, created_at=utcnow())
            if self._artifacts is not None:
                try:
                    contract = self._artifacts.store(
                        _evidence_contract(run.run_id, kind), content)
                    artifact = artifact.model_copy(update={
                        "path": contract.storage_path, "ref": contract.checksum})
                except Exception as exc:  # noqa: BLE001 — B1: in-memory fallback
                    logger.warning("evidence store failed for %s: %s", kind, exc)
            artifacts.append(artifact)
        return artifacts

    def _persist(
        self, run: HarnessRun, result: HarnessResult,
        artifacts: list[HarnessArtifact],
    ) -> None:
        try:
            self._state.update_state(
                run.run_id,  # C3-02 v2: key = run_id trực tiếp
                run=run.model_dump(mode="json"),  # B9
                result=result.model_dump(mode="json"),
                artifacts=[a.model_dump(mode="json") for a in artifacts])
        except Exception as exc:  # noqa: BLE001 — never break the report
            logger.warning("harness state persist failed: %s", exc)

    # -- queries ---------------------------------------------------------------

    def get_run(self, run_id: str) -> HarnessRun | None:
        state = self._state.get_state(run_id)
        if not state or "run" not in state:
            return None
        return HarnessRun.model_validate(state["run"])

    def get_result(self, run_id: str) -> HarnessResult | None:
        state = self._state.get_state(run_id)
        if not state or "result" not in state:
            return None
        return HarnessResult.model_validate(state["result"])

    def get_evidence(self, run_id: str) -> list[HarnessArtifact]:
        state = self._state.get_state(run_id)
        if state and "artifacts" in state:
            return [HarnessArtifact.model_validate(a) for a in state["artifacts"]]
        # B3: restart-safe fallback — reconstruct from ArtifactService sidecars.
        if self._artifacts is None:
            return []
        found = []
        for contract in self._artifacts.list(ArtifactType.JSON):
            if (contract.metadata or {}).get("run_id") == run_id:
                found.append(HarnessArtifact(
                    id=f"{run_id}:{contract.metadata.get('kind', '?')}",
                    run_id=run_id,
                    kind=contract.metadata.get("kind", "?"),
                    path=contract.storage_path, ref=contract.checksum,
                    created_at=contract.created))
        return sorted(found, key=lambda a: (a.run_id, a.kind))  # R3-4
