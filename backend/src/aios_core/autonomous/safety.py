"""Autonomy Safety 1.0 — M10-F3 (TASK-067).

Mandatory enforcement chain (PLAN §M10-16):
`Agent → Action Proposal → Risk Classifier → Governor → Policy → Permission
→ Capability → Tool` — không shortcut. Stop Anywhere: mọi side effect bị chặn
tại boundary trước khi thực thi (INV-030). ToolGuard = guardrails cấp tool
(pre/post mỗi invocation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict

#: Risk theo action (PLAN §M9-14 risk budget: read/edit=autonomous,
#: commit/deploy=approval, delete=impossible).
RISK_TABLE: dict[str, int] = {
    "read": 1,
    "edit": 2,
    "run": 2,
    "commit": 3,
    "deploy": 4,
    "network": 4,
    "delete": 5,
}

#: Target nhạy cảm → +1 risk.
SENSITIVE_TARGETS: frozenset[str] = frozenset({
    "production", "database", "credentials", "secrets", "billing",
})


class RiskLevel(str, Enum):
    LOW = "low"          # 1–2
    MEDIUM = "medium"    # 3
    HIGH = "high"        # 4 → ASK_HUMAN
    CRITICAL = "critical"  # 5 → STOP


class SafetyDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK_HUMAN = "ask_human"
    STOP = "stop"


class SafetyError(RuntimeError):
    """Side effect bất hợp lệ bị chặn tại boundary."""


class ActionProposal(BaseModel):
    """Đề xuất hành động autonomous (extra=forbid — C2-03)."""

    model_config = ConfigDict(extra="forbid")

    action: str
    target: str
    tool_id: str = ""
    approved: bool = False  # approval con người đã có sẵn?


@dataclass
class SafetyDecisionResult:
    decision: SafetyDecision
    risk_level: RiskLevel
    risk_score: int
    evidence: list[str] = field(default_factory=list)
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.decision == SafetyDecision.ALLOW


class RiskClassifier:
    """Deterministic risk từ action + target sensitivity."""

    def classify(self, proposal: ActionProposal) -> tuple[RiskLevel, int]:
        score = RISK_TABLE.get(proposal.action, 2)
        if proposal.target in SENSITIVE_TARGETS:
            score += 1
        if score >= 5:
            return RiskLevel.CRITICAL, score
        if score == 4:
            return RiskLevel.HIGH, score
        if score == 3:
            return RiskLevel.MEDIUM, score
        return RiskLevel.LOW, score


class SafetyEnforcer:
    """Chuỗi bắt buộc: Risk → Governor → Policy → Permission.

    KHÔNG sở hữu governor/policy — nhận callable (duck-typed, INV-030).
    Gate fail → dừng ngay, evidence ghi đủ 4 bước.
    """

    def __init__(
        self,
        governor_fn: Callable[[ActionProposal], str],
        policy_fn: Callable[[ActionProposal], Any],
        permission_fn: Callable[[ActionProposal], bool],
        classifier: RiskClassifier | None = None,
    ) -> None:
        self._governor = governor_fn
        self._policy = policy_fn
        self._permission = permission_fn
        self.classifier = classifier or RiskClassifier()

    def evaluate(self, proposal: ActionProposal) -> SafetyDecisionResult:
        evidence: list[str] = []

        # Gate 1 — Risk
        risk_level, score = self.classifier.classify(proposal)
        evidence.append(f"risk={risk_level.value}({score})")
        if risk_level == RiskLevel.CRITICAL and not proposal.approved:
            return SafetyDecisionResult(
                SafetyDecision.STOP, risk_level, score,
                evidence + ["denied at risk: critical (STOP)"],
                "risk critical — STOP (cần approval hoặc action thấp hơn)",
            )
        if risk_level == RiskLevel.HIGH and not proposal.approved:
            # risk cao (deploy/network/sensitive) → không tự ALLOW (R4)
            return SafetyDecisionResult(
                SafetyDecision.ASK_HUMAN, risk_level, score,
                evidence + ["denied at risk: high (ASK_HUMAN)"],
                "risk high — cần human approval",
            )

        # Gate 2 — Governor (INV-030: mọi action qua Governor)
        governor_decision = self._governor(proposal)
        evidence.append(f"governor={governor_decision}")
        if governor_decision == "stop":
            return SafetyDecisionResult(
                SafetyDecision.STOP, risk_level, score,
                evidence, "governor STOP (budget/risk vượt giới hạn)",
            )
        if governor_decision in ("ask_human", "replan", "pause"):
            return SafetyDecisionResult(
                SafetyDecision.ASK_HUMAN, risk_level, score,
                evidence, f"governor yêu cầu human: {governor_decision}",
            )

        # Gate 3 — Policy
        policy = self._policy(proposal)
        policy_approved = bool(getattr(policy, "approved", policy))
        policy_ask = bool(getattr(policy, "requires_approval", False))
        evidence.append(f"policy={'allow' if policy_approved else 'deny/ask'}")
        if not policy_approved or policy_ask:
            if policy_ask:
                return SafetyDecisionResult(
                    SafetyDecision.ASK_HUMAN, risk_level, score,
                    evidence, "policy requires approval (không tự ALLOW)",
                )
            return SafetyDecisionResult(
                SafetyDecision.DENY, risk_level, score,
                evidence, "policy deny",
            )

        # Gate 4 — Permission
        allowed = self._permission(proposal)
        evidence.append(f"permission={'allow' if allowed else 'deny'}")
        if not allowed:
            return SafetyDecisionResult(
                SafetyDecision.DENY, risk_level, score,
                evidence, "permission deny (default-deny)",
            )

        return SafetyDecisionResult(
            SafetyDecision.ALLOW, risk_level, score, evidence, "chain allow",
        )


class ToolGuard:
    """Guardrails cấp tool: pre-check TRƯỚC khi chạy + post-check sau khi chạy.

    Chặn tại boundary — tool._run KHÔNG được gọi nếu pre-check fail.
    """

    def __init__(
        self,
        tool: Any,
        enforcer: SafetyEnforcer,
        proposal_for: Callable[[Any], ActionProposal] | None = None,
        emergency_preflight: Callable[[], bool] | None = None,
    ) -> None:
        self._tool = tool
        self._enforcer = enforcer
        self._proposal_for = proposal_for or (lambda tool_input: ActionProposal(
            action="run", target="tool", tool_id=tool.id,
        ))
        self._emergency = emergency_preflight or (lambda: True)

    def run(self, tool_input: Any, context: Any) -> Any:
        """Pre-check → chạy → post-check (stop-anywhere)."""
        # Gate 0 — kill switch (TASK-068: hợp nhất hook duy nhất)
        if not self._emergency():
            raise SafetyError("emergency stop active — tool call blocked")
        proposal = self._proposal_for(tool_input)
        result = self._enforcer.evaluate(proposal)
        if not result.allowed:
            raise SafetyError(
                f"tool {proposal.tool_id} blocked: {result.decision.value} — {result.reason}"
            )
        output = self._tool.run(tool_input, context)
        self._post_check(proposal, output)
        return output

    def _post_check(self, proposal: ActionProposal, output: Any) -> None:
        """Side effect hợp lệ? Write action → output.ok bắt buộc."""
        if proposal.action in ("edit", "commit", "deploy", "delete"):
            ok = getattr(output, "ok", True)
            if not ok:
                raise SafetyError(
                    f"tool {proposal.tool_id} post-check fail: write action không hoàn thành"
                )
