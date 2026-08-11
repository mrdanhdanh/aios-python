"""Permission service tests."""

import pytest

from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import (
    PermissionDecision,
    PermissionRequest,
    PermissionScope,
    PermissionService,
)


@pytest.fixture
def bus():
    return EventBus()


def test_filesystem_default_allow(bus):
    svc = PermissionService(bus)
    assert svc.request(PermissionScope.FILESYSTEM, "/tmp/x") == PermissionDecision.ALLOW


def test_network_default_ask(bus):
    svc = PermissionService(bus)
    assert svc.request(PermissionScope.NETWORK, "api.example.com") == PermissionDecision.ASK


def test_set_policy_override(bus):
    svc = PermissionService(bus)
    svc.set_policy(PermissionScope.NETWORK, PermissionDecision.DENY)
    assert svc.request(PermissionScope.NETWORK, "x") == PermissionDecision.DENY


def test_set_policy_validates_enum(bus):
    svc = PermissionService(bus)
    with pytest.raises(ValueError):
        svc.set_policy("not-a-scope", PermissionDecision.ALLOW)
    with pytest.raises(ValueError):
        svc.set_policy(PermissionScope.GIT, "maybe")


def test_ask_request_goes_to_pending_and_emits(bus):
    svc = PermissionService(bus)
    received = []
    bus.subscribe(EventType.PERMISSION_REQUESTED, lambda ev: received.append(ev))
    decision = svc.request(PermissionScope.DOCKER, "container")
    assert decision == PermissionDecision.ASK
    assert svc.pending_count() == 1
    assert len(received) == 1
    assert received[0].payload["service"] == "permission"
    assert "request_id" in received[0].payload


def test_allow_decision_not_pending(bus):
    svc = PermissionService(bus)
    svc.request(PermissionScope.FILESYSTEM, "/x")  # ALLOW
    assert svc.pending_count() == 0


def test_grant_pending_emits_granted(bus):
    svc = PermissionService(bus)
    received = []
    bus.subscribe(EventType.PERMISSION_GRANTED, lambda ev: received.append(ev))
    svc.request(PermissionScope.SHELL, "ls")
    # find the pending request id
    request_id = next(iter(svc._pending.keys()))  # noqa: SLF001
    assert svc.grant(request_id) is True
    assert svc.pending_count() == 0
    assert len(received) == 1
    assert received[0].payload["scope"] == "shell"


def test_deny_pending_emits_denied(bus):
    svc = PermissionService(bus)
    received = []
    bus.subscribe(EventType.PERMISSION_DENIED, lambda ev: received.append(ev))
    svc.request(PermissionScope.BROWSER, "url")
    request_id = next(iter(svc._pending.keys()))  # noqa: SLF001
    assert svc.deny(request_id) is True
    assert len(received) == 1


def test_grant_unknown_id_noop(bus):
    svc = PermissionService(bus)
    assert svc.grant("nope") is False
    assert svc.deny("nope") is False


def test_on_ask_callback_allow(bus):
    svc = PermissionService(bus, on_ask=lambda req: PermissionDecision.ALLOW)
    received = []
    bus.subscribe(EventType.PERMISSION_GRANTED, lambda ev: received.append(ev))
    assert svc.request(PermissionScope.NETWORK, "x") == PermissionDecision.ALLOW
    assert svc.pending_count() == 0
    assert len(received) == 1


def test_on_ask_callback_deny(bus):
    svc = PermissionService(bus, on_ask=lambda req: PermissionDecision.DENY)
    received = []
    bus.subscribe(EventType.PERMISSION_DENIED, lambda ev: received.append(ev))
    assert svc.request(PermissionScope.NETWORK, "x") == PermissionDecision.DENY
    assert len(received) == 1


def test_on_ask_callback_raises_falls_back_ask(bus):
    def bad(req):
        raise RuntimeError("boom")

    svc = PermissionService(bus, on_ask=bad)
    assert svc.request(PermissionScope.NETWORK, "x") == PermissionDecision.ASK
    assert svc.pending_count() == 1


def test_on_ask_signature_is_permission_request(bus):
    def handler(req: PermissionRequest) -> PermissionDecision:
        assert isinstance(req, PermissionRequest)
        return PermissionDecision.DENY

    svc = PermissionService(bus, on_ask=handler)
    assert svc.request(PermissionScope.GIT, "repo") == PermissionDecision.DENY
