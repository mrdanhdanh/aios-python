"""VerificationHarness (TASK-030, H2): verify executions, kế thừa H1 Harness.

Persist TRƯỚC khi verify raise (AC5): state[run_id].verification chứa
evidence tóm tắt + verdict — sống sót qua H1 _persist (merge shallow).
Verdict.json qua ArtifactService theo convention P2-05
(id=harness:{run_id}:verdict, storage_path=harness/{safe}/verdict.json,
metadata kind="verdict") — khớp _evidence_contract H1 để get_evidence
fallback tìm thấy.
"""

from __future__ import annotations

import json
from typing import Any

from aios_core.contracts.artifact import ArtifactContract, ArtifactType
from aios_core.kernel.services.artifacts import ArtifactService
from aios_core.kernel.services.state import StateService
from aios_core.logging import get_logger

from ..context import HarnessContext
from ..contracts import safe_run_id
from ..registry import Harness
from .contracts import (
    CheckResult, EvidenceServices, VerificationResult, Verdict,
)
from .errors import VerificationError
from .evidence import collect_evidence, has_critical_evidence
from .pipeline import build_result, run_checks

logger = get_logger("aios.harness.execution")


class VerificationHarness(Harness):
    """H2 harness: collect evidence -> deterministic checks -> verdict."""

    id = "verification"
    name = "Execution Verification"
    version = "1.0.0"
    description = "Verify executions (plan/graph) via deterministic checks"

    def __init__(
        self,
        services: EvidenceServices,
        *,
        state_service: StateService | None = None,
        artifact_service: ArtifactService | None = None,
    ) -> None:
        self._services = services
        self._state = state_service
        self._artifacts = artifact_service

    # -- hooks ----------------------------------------------------------------

    def run(self, ctx: HarnessContext) -> Any:
        """P3-06: task từ ctx.config; collect evidence + preconditions."""
        task = ctx.config.get("task")  # VerificationTask
        if task is None:
            raise VerificationError("ctx.config['task'] missing (VerificationTask)")
        evidence = collect_evidence(task, self._services)
        pre = run_checks(task.preconditions, task.base_dir,
                         ctx.config.get("runners"))
        ctx.config["_evidence"] = evidence
        ctx.config["_pre_results"] = pre
        return {"evidence_keys": sorted(evidence.keys()),
                "preconditions": [r.model_dump(mode="json") for r in pre]}

    def verify(self, ctx: HarnessContext, payload: Any) -> None:
        """Persist verification TRƯỚC; raise nếu verdict FAIL (AC5)."""
        task = ctx.config.get("task")
        evidence: dict[str, Any] = ctx.config.get("_evidence") or {}
        pre: list[CheckResult] = ctx.config.get("_pre_results") or []
        post = run_checks(task.postconditions, task.base_dir,
                          ctx.config.get("runners"))
        invariants = run_checks(task.invariants, task.base_dir,
                                ctx.config.get("runners"))
        result = build_result(
            task.execution_ref, pre + post + invariants,
            has_critical_evidence(evidence), evidence.get("truncated", False))
        self._persist_verification(ctx, evidence, result)
        if result.verdict == Verdict.FAIL:
            raise VerificationError(
                f"verification failed: {result.summary}")

    # -- persistence ----------------------------------------------------------

    def _persist_verification(
        self, ctx: HarnessContext, evidence: dict[str, Any],
        result: VerificationResult,
    ) -> None:
        state_payload = {
            "execution_ref": result.execution_ref,
            "verdict": result.verdict.value,
            "summary": result.summary,
            "check_results": [r.model_dump(mode="json") for r in result.check_results],
            "critical_evidence": has_critical_evidence(evidence),
            "truncated": bool(evidence.get("truncated", False)),
            "metrics": result.metrics,
        }
        if self._state is not None:
            try:
                self._state.update_state(ctx.run_id, verification=state_payload)
            except Exception as exc:  # noqa: BLE001 — evidence never blocks verdict
                logger.warning("verification state persist failed: %s", exc)
        if self._artifacts is not None:
            try:
                content = json.dumps(
                    {"verification": state_payload}, ensure_ascii=False).encode("utf-8")
                self._artifacts.store(
                    ArtifactContract(
                        id=f"harness:{ctx.run_id}:verdict",
                        name="harness-verdict",
                        version="1.0.0",
                        author="aios-core",
                        license="proprietary",
                        contract_version="1.0.0",
                        schema_version="1.0.0",
                        type=ArtifactType.JSON,
                        storage_path=f"harness/{safe_run_id(ctx.run_id)}/verdict.json",
                        metadata={"run_id": ctx.run_id, "kind": "verdict"},
                    ),
                    content,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("verdict artifact store failed: %s", exc)

    def get_verdict(self, run_id: str) -> VerificationResult | None:
        """Đọc verification từ state (fallback: verdict.json artifact)."""
        if self._state is not None:
            state = self._state.get_state(run_id)
            if state and state.get("verification"):
                v = state["verification"]
                return VerificationResult(
                    execution_ref=v["execution_ref"],
                    verdict=Verdict(v["verdict"]),
                    check_results=[CheckResult(**c) for c in v.get("check_results", [])],
                    summary=v.get("summary", ""),
                    metrics=v.get("metrics", {}),
                )
        return None
