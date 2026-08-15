"""TASK-067 — Autonomy Safety 1.0: mandatory enforcement chain (M10-F3)."""

from __future__ import annotations

import pytest

from aios_core.autonomous.safety import (
    RISK_TABLE,
    SENSITIVE_TARGETS,
    ActionProposal,
    RiskClassifier,
    RiskLevel,
    SafetyDecision,
    SafetyEnforcer,
    SafetyError,
    ToolGuard,
)


def _governor(decision: str = "continue"):
    return lambda p: decision


def _policy(approved=True, ask=False):
    from types import SimpleNamespace

    return lambda p: SimpleNamespace(approved=approved, requires_approval=ask)


def _permission(allowed=True):
    return lambda p: allowed


# ---------------------------------------------------------------------------
# AC2: RiskClassifier bảng deterministic
# ---------------------------------------------------------------------------

def test_risk_table():
    assert RISK_TABLE["read"] == 1
    assert RISK_TABLE["edit"] == 2
    assert RISK_TABLE["commit"] == 3
    assert RISK_TABLE["deploy"] == 4
    assert RISK_TABLE["delete"] == 5
    assert "production" in SENSITIVE_TARGETS


def test_risk_classifier():
    clf = RiskClassifier()
    assert clf.classify(ActionProposal(action="read", target="file")) == (RiskLevel.LOW, 1)
    assert clf.classify(ActionProposal(action="commit", target="repo")) == (RiskLevel.MEDIUM, 3)
    assert clf.classify(ActionProposal(action="deploy", target="staging")) == (RiskLevel.HIGH, 4)
    assert clf.classify(ActionProposal(action="delete", target="tmp")) == (RiskLevel.CRITICAL, 5)
    # target nhạy cảm +1
    assert clf.classify(ActionProposal(action="edit", target="production")) == (RiskLevel.MEDIUM, 3)
    assert clf.classify(ActionProposal(action="deploy", target="production")) == (RiskLevel.CRITICAL, 5)


# ---------------------------------------------------------------------------
# AC1: chain đúng thứ tự — gate fail dừng ngay
# ---------------------------------------------------------------------------

def test_chain_allow_all():
    enforcer = SafetyEnforcer(_governor(), _policy(), _permission())
    result = enforcer.evaluate(ActionProposal(action="read", target="file"))
    assert result.allowed
    assert len(result.evidence) == 4  # risk/governor/policy/permission
    assert result.evidence[0].startswith("risk=")
    assert result.evidence[1].startswith("governor=")


def test_chain_deny_at_risk_critical():
    enforcer = SafetyEnforcer(_governor(), _policy(), _permission())
    result = enforcer.evaluate(ActionProposal(action="delete", target="db"))
    assert result.decision == SafetyDecision.STOP
    assert "denied at risk" in result.evidence[-1]


def test_chain_deny_at_governor_stop():
    enforcer = SafetyEnforcer(_governor("stop"), _policy(), _permission())
    result = enforcer.evaluate(ActionProposal(action="read", target="file"))
    assert result.decision == SafetyDecision.STOP
    # permission không được gọi — dừng sớm nhưng evidence vẫn đủ 4 gate (R2)
    assert len(result.evidence) == 2  # risk + governor


def test_chain_ask_human_at_governor():
    enforcer = SafetyEnforcer(_governor("ask_human"), _policy(), _permission())
    result = enforcer.evaluate(ActionProposal(action="read", target="file"))
    assert result.decision == SafetyDecision.ASK_HUMAN


def test_chain_deny_at_policy():
    enforcer = SafetyEnforcer(_governor(), _policy(approved=False), _permission())
    result = enforcer.evaluate(ActionProposal(action="read", target="file"))
    assert result.decision == SafetyDecision.DENY


# ---------------------------------------------------------------------------
# AC5: ASK_HUMAN từ policy không tự ALLOW
# ---------------------------------------------------------------------------

def test_policy_ask_human_not_auto_allow():
    enforcer = SafetyEnforcer(_governor(), _policy(approved=True, ask=True), _permission())
    result = enforcer.evaluate(ActionProposal(action="read", target="file"))
    assert result.decision == SafetyDecision.ASK_HUMAN


# ---------------------------------------------------------------------------
# AC4: risk cao → ASK_HUMAN/STOP
# ---------------------------------------------------------------------------

def test_high_risk_asks_human():
    enforcer = SafetyEnforcer(_governor(), _policy(), _permission())
    result = enforcer.evaluate(ActionProposal(action="deploy", target="staging"))
    assert result.decision == SafetyDecision.ASK_HUMAN  # risk high (4)


def test_critical_with_approval_allowed():
    """Risk critical nhưng có approval sẵn → đi tiếp chain."""
    enforcer = SafetyEnforcer(_governor(), _policy(), _permission())
    result = enforcer.evaluate(
        ActionProposal(action="delete", target="tmp", approved=True)
    )
    assert result.allowed


# ---------------------------------------------------------------------------
# AC6/AC7: ToolGuard pre/post + không phá tool hợp lệ
# ---------------------------------------------------------------------------

def test_tool_guard_blocks_before_run():
    """Deny → tool._run KHÔNG được gọi (C2-01: đếm)."""
    calls = {"n": 0}

    class FakeTool:
        id = "tool.test"

        def run(self, inp, ctx):
            calls["n"] += 1
            return "ok"

    enforcer = SafetyEnforcer(_governor(), _policy(approved=False), _permission())
    guard = ToolGuard(FakeTool(), enforcer)
    with pytest.raises(SafetyError, match="blocked"):
        guard.run(None, None)
    assert calls["n"] == 0  # pre-check chặn TRƯỚC khi chạy


def test_tool_guard_allows_valid_tool():
    calls = {"n": 0}

    class FakeTool:
        id = "tool.test"

        def run(self, inp, ctx):
            calls["n"] += 1
            return "ok"

    enforcer = SafetyEnforcer(_governor(), _policy(), _permission())
    guard = ToolGuard(FakeTool(), enforcer)
    assert guard.run(None, None) == "ok"
    assert calls["n"] == 1


def test_tool_guard_post_check_write_fail():
    """Write action output.ok=False → post-check fail (stop-anywhere)."""
    class FakeTool:
        id = "tool.write"

        def run(self, inp, ctx):
            class Out:
                ok = False
            return Out()

    proposal_for = lambda inp: ActionProposal(action="edit", target="file", tool_id="tool.write")
    enforcer = SafetyEnforcer(_governor(), _policy(), _permission())
    guard = ToolGuard(FakeTool(), enforcer, proposal_for=proposal_for)
    with pytest.raises(SafetyError, match="post-check"):
        guard.run(None, None)


def test_tool_guard_emergency_hook():
    """Kill switch emergency → chặn tool ngay (hợp nhất TASK-068 hook)."""
    class FakeTool:
        id = "tool.test"

        def run(self, inp, ctx):
            return "ok"

    enforcer = SafetyEnforcer(_governor(), _policy(), _permission())
    guard = ToolGuard(FakeTool(), enforcer, emergency_preflight=lambda: False)
    with pytest.raises(SafetyError, match="emergency"):
        guard.run(None, None)


def test_evidence_records_gates_on_early_deny():
    """R2: dù deny sớm, evidence vẫn ghi các gate đã qua."""
    enforcer = SafetyEnforcer(_governor("stop"), _policy(), _permission())
    result = enforcer.evaluate(ActionProposal(action="read", target="file"))
    assert result.evidence[0].startswith("risk=")
    assert result.evidence[1] == "governor=stop"
