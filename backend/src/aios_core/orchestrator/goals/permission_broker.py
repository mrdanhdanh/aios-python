"""Permission Broker: collect + dedupe workflow permissions, consult policy,
ask a human (injectable callback), audit every decision.

Belongs to the Policy Engine (PLAN.md). The broker does NOT evaluate policy
scope-level itself — it maps ``PolicyDecision.ask_scopes`` (computed by
PolicyService) onto per-scope ASK/ALLOW/DENY decisions.
"""

from __future__ import annotations

import uuid
from typing import Callable

from pydantic import BaseModel, ConfigDict, Field

from ...kernel.events import EventType
from ...kernel.services.events import EventService
from ...kernel.services.permissions import PermissionDecision, PermissionScope
from ...kernel.services.policy import PolicyRequest, PolicyService

APPROVER_TYPE = Callable[["PermissionBatch"], PermissionDecision]


class PermissionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    scopes: list[PermissionScope]  # deduped + sorted by scope.value
    source: str = ""  # e.g. "workflow:crud_generator"


class PermissionBatchDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_id: str
    decisions: dict[str, PermissionDecision]  # key = scope.value -> allow/deny/ask
    approved: bool  # True when every scope is ALLOW
    reason: str = ""


class PermissionBroker:
    """Pre-flight permission gate for a workflow/plan.

    ``approver=None``: auto-ALLOW only when the policy allows directly; if the
    policy requires approval and no approver is configured, the batch is DENIED
    with reason "no approver configured" (default-deny — C2-12). Production
    should always inject a real approver callback (UI prompt).
    """

    def __init__(
        self,
        event_service: EventService,
        policy_service: PolicyService,
        approver: APPROVER_TYPE | None = None,
    ) -> None:
        self._events = event_service
        self._policy = policy_service
        self._approver = approver

    # -- public API ----------------------------------------------------------

    def collect(self, permissions: list[str], source: str = "") -> PermissionBatch:
        """Validate, dedupe and sort scopes into a batch.

        Unknown scope -> ValueError; empty list -> ValueError (C1-11).
        """
        if not permissions:
            raise ValueError("empty scopes")
        scopes: list[PermissionScope] = []
        seen: set[str] = set()
        for raw in permissions:
            try:
                scope = PermissionScope(raw)
            except ValueError:
                raise ValueError(f"unknown permission scope: {raw!r}") from None
            if scope.value not in seen:
                seen.add(scope.value)
                scopes.append(scope)
        scopes.sort(key=lambda s: s.value)
        return PermissionBatch(id=uuid.uuid4().hex, scopes=scopes, source=source)

    def request(self, batch: PermissionBatch) -> PermissionBatchDecision:
        """Evaluate the batch against policy + approver; audit everything."""
        if not batch.scopes:
            raise ValueError("empty batch")
        decision = self._policy.evaluate(PolicyRequest(scopes=batch.scopes, internet=False))

        # 1) Hard deny (policy deny / token / internet): every scope DENY.
        if not decision.approved:
            result = {s.value: PermissionDecision.DENY for s in batch.scopes}
            out = PermissionBatchDecision(
                batch_id=batch.id, decisions=result, approved=False, reason=decision.reason
            )
            self._emit_decision(out)
            return out

        # 2) Approval path: scopes in ask_scopes -> ASK; others -> ALLOW.
        #    Special case (C1-01): requires_approval=True with empty ask_scopes
        #    (policy rule demands approval although every scope is allowed) ->
        #    the whole batch becomes ASK.
        if decision.requires_approval:
            ask_scopes = decision.ask_scopes or [s.value for s in batch.scopes]
            decisions: dict[str, PermissionDecision] = {}
            for scope in batch.scopes:
                decisions[scope.value] = (
                    PermissionDecision.ASK if scope.value in ask_scopes else PermissionDecision.ALLOW
                )
            resolved: PermissionDecision | None = None
            if PermissionDecision.ASK in decisions.values():
                self._events.emit(
                    EventType.PERMISSION_REQUESTED,
                    {
                        "service": "permission_broker",
                        "request_id": uuid.uuid4().hex,
                        "scopes": [s.value for s in batch.scopes],
                        "ask_scopes": ask_scopes,
                    },
                    source=batch.id,  # C2-04: batch_id lives in Event.source, NOT payload
                )
                resolved = self._resolve_ask(batch)
                for scope in batch.scopes:
                    if decisions[scope.value] == PermissionDecision.ASK:
                        decisions[scope.value] = resolved
            if self._approver is None:
                reason = "no approver configured"  # C2-12: default-deny
            elif resolved is not None and resolved != PermissionDecision.ALLOW:
                reason = "approver decision"
            else:
                reason = "policy + approver allow"
            out = PermissionBatchDecision(
                batch_id=batch.id,
                decisions=decisions,
                approved=all(d == PermissionDecision.ALLOW for d in decisions.values()),
                reason=reason,
            )
            self._emit_decision(out)
            return out

        # 3) Direct allow: every scope ALLOW, no approval needed.
        result = {s.value: PermissionDecision.ALLOW for s in batch.scopes}
        out = PermissionBatchDecision(
            batch_id=batch.id, decisions=result, approved=True, reason=decision.reason
        )
        self._emit_decision(out)
        return out

    def collect_and_request(self, permissions: list[str], source: str = "") -> PermissionBatchDecision:
        """Convenience: collect + request in one step."""
        return self.request(self.collect(permissions, source=source))

    # -- internals -----------------------------------------------------------

    def _resolve_ask(self, batch: PermissionBatch) -> PermissionDecision:
        """Ask the approver for ASK scopes. Default-deny on any failure (C1-07)."""
        if self._approver is None:
            return PermissionDecision.DENY  # no approver configured (C2-12)
        try:
            answer = self._approver(batch)
        except Exception as exc:  # noqa: BLE001 — default-deny is the safe path
            self._events.emit(
                EventType.ERROR_OCCURRED,
                {"service": "permission_broker", "batch_id": batch.id, "error": str(exc)},
                source="permission_broker",
            )
            return PermissionDecision.DENY
        if answer == PermissionDecision.ALLOW:
            return PermissionDecision.ALLOW
        return PermissionDecision.DENY  # ASK/other -> treated as DENY

    def _emit_decision(self, out: PermissionBatchDecision) -> None:
        if out.approved:
            self._events.emit(
                EventType.PERMISSION_GRANTED,
                {
                    "service": "permission_broker",
                    "batch_id": out.batch_id,
                    "scopes": list(out.decisions.keys()),
                },
                source="permission_broker",
            )
        else:
            self._events.emit(
                EventType.PERMISSION_DENIED,
                {
                    "service": "permission_broker",
                    "batch_id": out.batch_id,
                    "scopes": list(out.decisions.keys()),
                    "reason": out.reason,
                },
                source="permission_broker",
            )
