"""Policy service tests: precedence, budget, internet, approval."""

import pytest
from pydantic import ValidationError

from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import (
    PermissionScope,
    Policy,
    PolicyRequest,
    PolicyService,
)


def _svc(policy: Policy | None = None):
    return PolicyService(EventBus(), policy)


def test_deny_scope_rejected_lists_all():
    p = Policy(deny_scopes=["network", "docker"])
    svc = _svc(p)
    result = svc.evaluate(PolicyRequest(scopes=[PermissionScope.NETWORK, PermissionScope.DOCKER]))
    assert result.approved is False
    assert "network" in result.reason and "docker" in result.reason


def test_token_budget_rejected():
    p = Policy(max_tokens=1000)
    svc = _svc(p)
    result = svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM], tokens=2000))
    assert result.approved is False
    assert "token" in result.reason


def test_internet_blocked():
    svc = _svc(Policy(allow_internet=False))
    result = svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM], internet=True))
    assert result.approved is False
    assert "internet" in result.reason


def test_require_approval_plus_deny_deny_wins():
    p = Policy(deny_scopes=["shell"], require_approval=True)
    svc = _svc(p)
    result = svc.evaluate(PolicyRequest(scopes=[PermissionScope.SHELL]))
    assert result.approved is False  # deny wins over approval


def test_require_approval_requests_approval():
    svc = _svc(Policy(require_approval=True))
    result = svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM]))
    assert result.approved is True
    assert result.requires_approval is True


def test_scope_not_in_allow_requires_approval():
    # default policy allows only filesystem → docker is ASK
    svc = _svc()
    result = svc.evaluate(PolicyRequest(scopes=[PermissionScope.DOCKER]))
    assert result.approved is True
    assert result.requires_approval is True
    assert "docker" in result.reason


def test_scope_in_allow_no_approval():
    svc = _svc()
    result = svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM]))
    assert result.approved is True
    assert result.requires_approval is False
    assert result.policy_version == "0.1.0"


def test_policy_version_invalid_semver():
    with pytest.raises(ValidationError):
        Policy(version="nope")


def test_emits_permission_requested_for_policy():
    bus = EventBus()
    received = []
    bus.subscribe(EventType.PERMISSION_REQUESTED, lambda ev: received.append(ev))
    svc = PolicyService(bus, Policy(require_approval=True))
    svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM]))
    assert len(received) == 1
    assert received[0].payload["service"] == "policy"
    assert "request_id" in received[0].payload


def test_policy_decision_ask_scopes_field_all_branches():
    # C2-06 (TASK-012): ask_scopes must be set in ALL 5 return branches.
    # 1) deny branch -> []
    svc = _svc(Policy(deny_scopes=["network"]))
    r = svc.evaluate(PolicyRequest(scopes=[PermissionScope.NETWORK]))
    assert r.ask_scopes == []
    # 2) token branch -> []
    svc = _svc(Policy(max_tokens=100))
    r = svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM], tokens=200))
    assert r.ask_scopes == []
    # 3) internet branch -> []
    svc = _svc(Policy(allow_internet=False))
    r = svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM], internet=True))
    assert r.ask_scopes == []
    # 4) approval branch -> scopes outside allow_scopes
    svc = _svc()
    r = svc.evaluate(PolicyRequest(scopes=[PermissionScope.DOCKER, PermissionScope.FILESYSTEM]))
    assert r.requires_approval is True
    assert r.ask_scopes == ["docker"]  # filesystem is allowed
    # 5) allow branch -> []
    r = svc.evaluate(PolicyRequest(scopes=[PermissionScope.FILESYSTEM]))
    assert r.ask_scopes == []
    # dataclass default
    from aios_core.kernel.services.policy import PolicyDecision

    assert PolicyDecision(approved=True).ask_scopes == []


def test_default_policy_contents():
    svc = _svc()
    p = svc.policy
    assert p.allow_scopes == ["filesystem"]
    assert p.deny_scopes == []
    assert p.require_approval is False
    assert p.allow_internet is False
    assert p.max_tokens is None
    assert p.version == "0.1.0"
