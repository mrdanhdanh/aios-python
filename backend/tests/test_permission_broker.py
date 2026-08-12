"""PermissionBroker tests (AC7-8, C1-07/11, C2-04/12/13)."""

import pytest

from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import EventService, PermissionScope
from aios_core.kernel.services.permissions import PermissionDecision
from aios_core.kernel.services.policy import Policy, PolicyService
from aios_core.orchestrator.goals import PermissionBroker


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def event_service(bus, tmp_path):
    return EventService(bus, tmp_path / "audit.db")


def _broker(event_service, policy: Policy | None = None, approver=None):
    # PolicyService gets its own bus; the broker audits/publishes via EventService
    # (whose bus is what tests subscribe to).
    return PermissionBroker(
        event_service=event_service,
        policy_service=PolicyService(EventBus(), policy),
        approver=approver,
    )


def test_collect_dedupes_and_sorts(event_service):
    broker = _broker(event_service)
    batch = broker.collect(["network", "shell", "network", "filesystem"])
    assert [s.value for s in batch.scopes] == ["filesystem", "network", "shell"]  # sorted


def test_collect_unknown_scope_raises(event_service):
    broker = _broker(event_service)
    with pytest.raises(ValueError, match="unknown permission scope"):
        broker.collect(["nonsense-scope"])


def test_collect_empty_raises(event_service):
    broker = _broker(event_service)
    with pytest.raises(ValueError, match="empty scopes"):
        broker.collect([])


def test_policy_deny_rejects_batch(event_service):
    policy = Policy(deny_scopes=["network"])
    broker = _broker(event_service, policy)
    out = broker.collect_and_request(["network", "filesystem"])
    assert out.approved is False
    assert out.decisions["network"] == PermissionDecision.DENY
    assert "denied" in out.reason


def test_default_no_approver_denies_when_policy_requires(event_service):
    # C2-12: no approver + policy requires approval -> DENY (default-deny).
    policy = Policy(require_approval=True, allow_scopes=["filesystem"])
    broker = _broker(event_service, policy)
    out = broker.collect_and_request(["filesystem"])
    assert out.approved is False
    assert "no approver" in out.reason


def test_direct_allow_without_approval(event_service):
    # Policy allows directly (no require_approval, scope allowed) -> ALLOW, no ask.
    broker = _broker(event_service, Policy(allow_scopes=["filesystem"]))
    out = broker.collect_and_request(["filesystem"])
    assert out.approved is True
    assert out.decisions["filesystem"] == PermissionDecision.ALLOW


def test_approver_deny_all_ask(event_service):
    policy = Policy(allow_scopes=["filesystem"])  # network -> ASK
    broker = _broker(event_service, policy, approver=lambda batch: PermissionDecision.DENY)
    out = broker.collect_and_request(["network", "filesystem"])
    assert out.approved is False
    assert out.decisions["network"] == PermissionDecision.DENY
    assert out.decisions["filesystem"] == PermissionDecision.ALLOW  # allowed, never asked


def test_approver_allow_ask(event_service):
    policy = Policy(allow_scopes=["filesystem"])
    broker = _broker(event_service, policy, approver=lambda batch: PermissionDecision.ALLOW)
    out = broker.collect_and_request(["network"])
    assert out.approved is True
    assert out.decisions["network"] == PermissionDecision.ALLOW


def test_approver_raise_denies_all(event_service, bus):
    # C1-07: approver raises -> DENY everything + ERROR_OCCURRED emitted.
    events = []
    bus.subscribe(None, events.append)

    def _boom(batch):
        raise RuntimeError("approver offline")

    broker = _broker(event_service, Policy(allow_scopes=["filesystem"]), approver=_boom)
    out = broker.collect_and_request(["network"])
    assert out.approved is False
    assert out.decisions["network"] == PermissionDecision.DENY
    assert any(e.type == EventType.ERROR_OCCURRED for e in events)


def test_require_approval_with_approver_allow(event_service):
    # C1-01 special case: require_approval=True, everything allowed -> whole batch ASK,
    # approver ALLOW -> approved.
    policy = Policy(require_approval=True, allow_scopes=["filesystem"])
    broker = _broker(event_service, policy, approver=lambda b: PermissionDecision.ALLOW)
    out = broker.collect_and_request(["filesystem"])
    assert out.approved is True
    assert out.decisions["filesystem"] == PermissionDecision.ALLOW


def test_audit_events_written(event_service, bus):
    # C2-04: PERMISSION_REQUESTED payload matches policy schema (service, no batch_id);
    # batch_id lives in Event.source; GRANTED/DENIED carry batch_id in payload.
    events = []
    bus.subscribe(None, events.append)
    broker = _broker(event_service, Policy(allow_scopes=["filesystem"]),
                     approver=lambda b: PermissionDecision.DENY)
    out = broker.collect_and_request(["network"], source="workflow:crud")
    requested = [e for e in events if e.type == EventType.PERMISSION_REQUESTED]
    assert requested
    payload = requested[0].payload
    assert payload["service"] == "permission_broker"
    assert "batch_id" not in payload  # C2-04: batch id NOT in payload
    assert requested[0].source == out.batch_id  # batch id in Event.source
    denied = [e for e in events if e.type == EventType.PERMISSION_DENIED]
    assert denied and denied[0].payload["batch_id"] == out.batch_id
    # audit trail
    audit_types = {a.type.value for a in event_service.query_audit()}
    assert "permission.requested" in audit_types
    assert "permission.denied" in audit_types


def test_request_empty_batch_raises(event_service):
    broker = _broker(event_service)
    from aios_core.orchestrator.goals import PermissionBatch

    with pytest.raises(ValueError, match="empty batch"):
        broker.request(PermissionBatch(id="b", scopes=[]))


def test_collect_returns_source(event_service):
    broker = _broker(event_service)
    batch = broker.collect(["shell"], source="workflow:x")
    assert batch.source == "workflow:x"
