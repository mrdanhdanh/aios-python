"""Evidence collection (TASK-030, H2): runtime evidence for verification."""

from __future__ import annotations

import json
from typing import Any

from .contracts import EvidenceServices, VerificationTask


def _resolve_state_key(task: VerificationTask, services: EvidenceServices) -> tuple[str, dict | None]:
    """C1-01/P3-08: (1) get_state(ref) → namespace theo dạng ref; (2) nếu ref
    chưa prefix `graph:` → get_state(f"graph:{ref}") → (3) không thấy → partial."""
    ref = task.execution_ref
    state = services.state.get_state(ref)
    if state is not None:
        return ("graph", state) if ref.startswith("graph:") else ("plan", state)
    if not ref.startswith("graph:"):
        state = services.state.get_state(f"graph:{ref}")
        if state is not None:
            return "graph", state
    return "", None


def _collect_events(
    task: VerificationTask, services: EvidenceServices,
) -> tuple[list[dict], bool]:
    """runtime-events.json: query_audit(limit=10000) + filter execution_id
    + sort (timestamp, id) asc (C2-05/P3-02); truncated detection (P2-01/R3-3)."""
    events = services.events.query_audit(limit=10000) or []
    candidates = {task.execution_ref, task.execution_ref.removeprefix("graph:")}
    filtered = [e for e in events if _event_execution_id(e) in candidates]
    truncated = len(filtered) == 10000
    filtered.sort(key=lambda e: (
        e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp),
        getattr(e, "id", ""),
    ))
    return [_event_to_dict(e) for e in filtered], truncated


def _event_execution_id(event: Any) -> str:
    payload = getattr(event, "payload", None) or {}
    return payload.get("execution_id") or payload.get("plan_id") or ""


def _event_to_dict(event: Any) -> dict:
    if hasattr(event, "to_dict"):  # kernel Event dataclass (R3-2)
        return event.to_dict()
    return {"id": getattr(event, "id", ""), "type": getattr(event, "type", ""),
            "payload": getattr(event, "payload", {}),
            "timestamp": str(getattr(event, "timestamp", ""))}


def collect_evidence(
    task: VerificationTask, services: EvidenceServices,
) -> dict[str, Any]:
    """Evidence package (P2-04: bỏ test-results/evaluation v1)."""
    namespace, state = _resolve_state_key(task, services)
    evidence: dict[str, Any] = {"namespace": namespace, "truncated": False}
    if state is None:
        return evidence  # partial — verdict INCONCLUSIVE (unless check FAIL)

    if namespace == "plan":
        evidence["plan.json"] = state.get("plan")
        evidence["tool-results"] = state.get("results", {})
        events, truncated = _collect_events(task, services)
        evidence["runtime-events.json"] = events
        evidence["truncated"] = truncated
    else:  # graph
        evidence["execution-graph.json"] = state.get("graph")
        evidence["tool-results"] = state.get("results", {})
        events, truncated = _collect_events(task, services)
        evidence["runtime-events.json"] = events
        evidence["truncated"] = truncated
    return evidence


def has_critical_evidence(evidence: dict[str, Any]) -> bool:
    """P1-01 v2: (plan.json ∨ execution-graph.json) ∧ runtime-events.json."""
    if evidence.get("truncated"):
        return False  # P2-01/R3-6: không PASS khi evidence có thể thiếu
    namespace = evidence.get("namespace", "")
    if namespace == "plan" and "plan.json" not in evidence:
        return False
    if namespace == "graph" and "execution-graph.json" not in evidence:
        return False
    if not namespace:
        return False
    events = evidence.get("runtime-events.json")
    if not isinstance(events, list):
        return False
    if namespace == "plan" and not events:
        return False  # P2-02: plan-namespace cần ≥1 event khớp
    # graph-namespace chấp nhận [] (executor không emit — P2-02)
    return True
