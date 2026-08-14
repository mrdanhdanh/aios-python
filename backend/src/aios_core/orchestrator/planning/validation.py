"""Plan validator (TASK-026 §YC-8 / INV-014): 8 categories, deterministic."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ...kernel.dag import validate_dag
from ...kernel.execution_plan import ExecutionPlan
from ...kernel.services import PermissionScope
from .contracts import (
    PlanValidationIssue,
    PlanValidationReport,
    ValidationRule,
)

_NODE_ID_RE = re.compile(r"node ([^:]+):")


@dataclass
class ValidationContext:
    """Injected dependencies for validation (deterministic, no side effects)."""

    capabilities: Any
    policy: Any | None = None  # PolicyService
    resources: Any | None = None  # ResourcesSettings
    settings: Any = None  # PlanningSettings

    def __init__(self, capabilities, policy=None, resources=None, settings=None):
        self.capabilities = capabilities
        self.policy = policy
        self.resources = resources
        self.settings = settings


def _node_id_from(message: str) -> str:
    match = _NODE_ID_RE.search(message)
    return match.group(1) if match else ""


class PlanValidator:
    """Validates all 8 PLAN §14 categories; issues sorted deterministically."""

    def validate(self, plan: ExecutionPlan, ctx: ValidationContext) -> PlanValidationReport:
        issues: list[PlanValidationIssue] = []

        # 1. Contract — strict re-validation (defense-in-depth).
        try:
            ExecutionPlan.model_validate(plan.model_dump())
        except Exception as exc:  # noqa: BLE001 — pydantic ValidationError or ValueError
            issues.append(PlanValidationIssue(
                rule=ValidationRule.CONTRACT, message=str(exc), fatal=True))
            return PlanValidationReport(issues=issues)  # contract fail = stop (nodes may be raw)

        # 2. Capability.
        known = set(ctx.capabilities.list())
        for node in plan.nodes:
            for capability in node.capabilities:
                if capability not in known:
                    issues.append(PlanValidationIssue(
                        rule=ValidationRule.CAPABILITY, node_id=node.id,
                        message=f"unknown capability {capability!r}", fatal=True))

        # 3. Permission.
        valid_scopes = {scope.value for scope in PermissionScope}
        for permission in plan.required_permissions:
            if permission not in valid_scopes:
                issues.append(PlanValidationIssue(
                    rule=ValidationRule.PERMISSION,
                    message=f"unknown permission scope {permission!r}", fatal=True))

        # 4. Policy (deterministic — deny > ask > allow).
        if ctx.policy is not None:
            from ...kernel.services import PolicyRequest

            decision = ctx.policy.evaluate(PolicyRequest(
                scopes=[PermissionScope(p) for p in plan.required_permissions
                        if p in valid_scopes],
                tokens=plan.estimated_tokens or None,
            ))
            if decision.requires_approval:
                issues.append(PlanValidationIssue(
                    rule=ValidationRule.POLICY,
                    message="requires human approval", fatal=False))
            elif not decision.approved:
                issues.append(PlanValidationIssue(
                    rule=ValidationRule.POLICY,
                    message=decision.reason or "denied", fatal=True))
        else:
            issues.append(PlanValidationIssue(
                rule=ValidationRule.POLICY,
                message="policy service unavailable", fatal=False))

        # 5. Dependency.
        node_ids = {node.id for node in plan.nodes}
        for node in plan.nodes:
            for dep in node.depends_on:
                if dep not in node_ids or dep == node.id:
                    issues.append(PlanValidationIssue(
                        rule=ValidationRule.DEPENDENCY, node_id=node.id,
                        message=f"invalid dependency {dep!r}", fatal=True))

        # 6. Resource.
        if ctx.resources is not None and ctx.resources.max_tokens is not None:
            if plan.estimated_tokens > ctx.resources.max_tokens:
                issues.append(PlanValidationIssue(
                    rule=ValidationRule.RESOURCE,
                    message=f"estimated {plan.estimated_tokens} > max_tokens "
                            f"{ctx.resources.max_tokens}", fatal=True))

        # 7. Cycle.
        try:
            validate_dag(plan.nodes)
        except (ValueError, AttributeError, TypeError) as exc:
            issues.append(PlanValidationIssue(
                rule=ValidationRule.CYCLE, node_id=_node_id_from(str(exc)),
                message=str(exc), fatal=True))

        # 8. Timeout.
        if ctx.settings is not None:
            for node in plan.nodes:
                if node.timeout_s < ctx.settings.min_timeout_s:
                    issues.append(PlanValidationIssue(
                        rule=ValidationRule.TIMEOUT, node_id=node.id,
                        message=f"timeout {node.timeout_s} < min {ctx.settings.min_timeout_s}",
                        fatal=True))
                if node.timeout_s > ctx.settings.max_timeout_s:
                    issues.append(PlanValidationIssue(
                        rule=ValidationRule.TIMEOUT, node_id=node.id,
                        message=f"timeout {node.timeout_s} > max {ctx.settings.max_timeout_s}",
                        fatal=True))

        issues.sort(key=lambda issue: (issue.rule.value, issue.node_id))
        return PlanValidationReport(issues=issues)
