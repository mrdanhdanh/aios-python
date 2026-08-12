"""FailureRecovery tests (AC9-10, AC11-recovery, C1-10)."""

import pytest

from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import EventService
from aios_core.orchestrator.goals import FailureRecovery, RecoveryStatus


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def event_service(bus, tmp_path):
    return EventService(bus, tmp_path / "audit.db")


def _recovery(event_service, **kwargs):
    kwargs.setdefault("sleeper", lambda s: None)  # never sleep for real
    kwargs.setdefault("backoff_base_s", 0.1)
    return FailureRecovery(event_service=event_service, **kwargs)


def _fail_n_times(n, value="ok"):
    """Executor that fails the first n calls, then succeeds with `value`."""
    calls = {"n": 0}

    def executor(agent, workflow):
        calls["n"] += 1
        if calls["n"] <= n:
            raise RuntimeError(f"boom {calls['n']}")
        return value

    return executor


def test_retry_until_success(event_service):
    rec = _recovery(event_service, max_retries=3)
    result = rec.run("coder", "crud", _fail_n_times(2))
    assert result.status == RecoveryStatus.RECOVERED
    assert result.attempts == 3  # 1 original + 2 retries
    assert result.final_result == "ok"


def test_fail_after_max_retries(event_service):
    rec = _recovery(event_service, max_retries=2)
    result = rec.run("coder", "crud", _fail_n_times(999))
    assert result.status == RecoveryStatus.FAILED
    assert result.attempts == 3  # 1 original + 2 retries
    assert result.error


def test_backoff_sequence_injected_sleeper(event_service):
    sleeps = []
    rec = FailureRecovery(
        event_service=event_service,
        max_retries=3,
        backoff_base_s=0.1,
        backoff_max_s=2.0,
        sleeper=sleeps.append,
    )
    rec.run("coder", "crud", _fail_n_times(999))
    # attempt_idx 0,1,2 -> min(0.1*2**i, 2.0) = [0.1, 0.2, 0.4]
    assert sleeps == pytest.approx([0.1, 0.2, 0.4])


def test_success_first_try_no_retries(event_service):
    rec = _recovery(event_service, max_retries=5)
    result = rec.run("coder", "crud", lambda a, w: "ok")
    assert result.status == RecoveryStatus.RECOVERED
    assert result.attempts == 1
    assert result.history == ["agent:coder"]


def test_fallback_agent_then_workflow(event_service):
    rec = _recovery(
        event_service,
        max_retries=1,
        fallback_agents={"coder": "doctor"},
        fallback_workflows={"crud": "crud_v2"},
    )
    # doctor succeeds
    calls = []

    def executor(agent, workflow):
        calls.append((agent, workflow))
        if agent == "doctor":
            return "healed"
        raise RuntimeError("coder broke")

    result = rec.run("coder", "crud", executor)
    assert result.status == RecoveryStatus.RECOVERED
    assert result.fallback_used == "agent"
    assert result.final_result == "healed"
    assert "fallback_agent:doctor" in result.history


def test_fallback_workflow_success(event_service):
    rec = _recovery(
        event_service,
        max_retries=0,
        fallback_agents={"coder": "doctor"},
        fallback_workflows={"crud": "crud_v2"},
    )
    calls = []

    def executor(agent, workflow):
        calls.append((agent, workflow))
        if workflow == "crud_v2":
            return "v2-ok"
        raise RuntimeError("nope")

    result = rec.run("coder", "crud", executor)
    assert result.status == RecoveryStatus.RECOVERED
    assert result.fallback_used == "workflow"
    # fallback workflow runs with fallback agent if any: doctor + crud_v2
    assert ("doctor", "crud_v2") in calls


def test_all_fail_reports_history(event_service, bus):
    events = []
    bus.subscribe(None, events.append)
    rec = _recovery(
        event_service,
        max_retries=2,
        fallback_agents={"coder": "doctor"},
        fallback_workflows={"crud": "crud_v2"},
    )
    result = rec.run("coder", "crud", _fail_n_times(999))
    assert result.status == RecoveryStatus.FAILED
    assert result.attempts == 5  # original + 2 retries + fallback agent + fallback workflow
    assert result.error
    assert result.history == [
        "agent:coder", "retry:1", "retry:2", "fallback_agent:doctor", "fallback_workflow:crud_v2",
    ]
    types = {e.type for e in events}
    assert EventType.ERROR_OCCURRED in types
    assert EventType.RECOVERY_RETRY in types
    assert EventType.RECOVERY_FALLBACK in types
    # C2-07: every executor failure emits ERROR_OCCURRED (5 failures -> 5 events)
    error_events = [e for e in events if e.type == EventType.ERROR_OCCURRED]
    assert len(error_events) == 5


def test_fallback_runs_once_no_retry(event_service):
    # C1-10: fallbacks execute exactly once — no retry loop on them.
    calls = []

    def executor(agent, workflow):
        calls.append((agent, workflow))
        raise RuntimeError("always fails")

    rec = _recovery(
        event_service,
        max_retries=1,
        fallback_agents={"coder": "doctor"},
        fallback_workflows={"crud": "crud_v2"},
    )
    result = rec.run("coder", "crud", executor)
    assert result.status == RecoveryStatus.FAILED
    assert calls == [("coder", "crud"), ("coder", "crud"), ("doctor", "crud"), ("doctor", "crud_v2")]


def test_recovery_events_emitted(event_service):
    # audit trail for recovery events
    rec = _recovery(event_service, max_retries=1)
    rec.run("coder", "crud", _fail_n_times(999))
    audit_types = {a.type.value for a in event_service.query_audit()}
    assert "error.occurred" in audit_types
    assert "recovery.retry" in audit_types


def test_validate_config_negative_values(event_service):
    with pytest.raises(ValueError, match="max_retries"):
        FailureRecovery(event_service, max_retries=-1)
    with pytest.raises(ValueError, match="backoff"):
        FailureRecovery(event_service, backoff_base_s=-0.5)
    with pytest.raises(ValueError, match="backoff"):
        FailureRecovery(event_service, backoff_max_s=-1.0)
