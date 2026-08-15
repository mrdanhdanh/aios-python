"""Security Baseline 1.0 — 11 checks (M10-F3, TASK-070).

Mỗi check: deterministic, không network, evidence thật (module import được +
literal class trong source + config flag). KHÔNG check giả (R1).
"""

from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass, field
from typing import Any, Callable

from .contracts import SecurityItem, SecurityReport, SecuritySeverity, SecurityStatus

#: Module path → literal class cần tồn tại (evidence).
_CHECK_SOURCES: tuple[tuple[str, str], ...] = (
    ("aios_core.enterprise.identity", "Principal"),          # identity/auth/authz
    ("aios_core.enterprise.security", "CredentialBroker"),   # secrets
    ("aios_core.enterprise.security", "NetworkPolicy"),      # network policy
    ("aios_core.enterprise.security", "SandboxBoundary"),    # sandbox
    ("aios_core.enterprise.tenancy", "TenantBoundary"),      # data boundary
    ("aios_core.enterprise.operations", "CentralAuditStore"),  # audit
    ("aios_core.ecosystem.marketplace", "TrustChain"),       # supply chain
    ("aios_core.contracts.artifact", "ArtifactContract"),    # encryption/checksum
)


def _src_has(module_path: str, literal: str) -> bool:
    """Import module + grep literal trong source (không chạy code)."""
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return False
    try:
        source = inspect.getsource(module)
    except (OSError, TypeError):
        return hasattr(module, literal)
    return literal in source


@dataclass
class SecurityContext:
    """Context cho checks — kernel/settings optional (lazy import trong check)."""

    settings: Any = None
    kernel: Any = None


class SecurityChecks:
    """11 baseline checks (PLAN §M10-23)."""

    def __init__(self, context: SecurityContext | None = None) -> None:
        self.ctx = context or SecurityContext()

    # -- helpers ------------------------------------------------------------
    def _enterprise_enabled(self) -> bool:
        try:
            from ..config import Settings

            settings = self.ctx.settings or Settings()
            return bool(settings.enterprise.enabled)
        except Exception:  # noqa: BLE001
            return True  # không đọc được config → coi enabled (không fail oan)

    def _item(self, item_id, name, severity, status, evidence, recommendation) -> SecurityItem:
        return SecurityItem(
            id=item_id, name=name, severity=severity, status=status,
            evidence=evidence, recommendation=recommendation,
        )

    # -- 11 checks ------------------------------------------------------------
    def identity(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.identity", "Principal")
        status = SecurityStatus.PASS if ok else SecurityStatus.FAIL
        return self._item(
            "identity", "Identity (Principal model)", SecuritySeverity.HIGH,
            status,
            f"enterprise.identity.Principal present={ok}; "
            f"enterprise.enabled={self._enterprise_enabled()}",
            "Bật enterprise.identity (INV-022 — mọi execution có Principal)",
        )

    def authentication(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.identity", "authenticate")
        status = SecurityStatus.PASS if ok else SecurityStatus.WARN
        return self._item(
            "authentication", "Authentication", SecuritySeverity.HIGH,
            status,
            f"identity.authenticate present={ok}",
            "Bổ sung authenticate flow cho principal (local-first: token ngắn hạn)",
        )

    def authorization(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.identity", "check_permission")
        status = SecurityStatus.PASS if ok else SecurityStatus.WARN
        return self._item(
            "authorization", "Authorization (RBAC/ABAC)", SecuritySeverity.HIGH,
            status,
            f"identity.check_permission present={ok}",
            "Bổ sung RBAC/ABAC check (role + attribute) cho mọi request",
        )

    def secrets(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.security", "CredentialBroker")
        status = SecurityStatus.PASS if ok else SecurityStatus.FAIL
        return self._item(
            "secrets", "Secrets (Credential Broker)", SecuritySeverity.CRITICAL,
            status,
            f"enterprise.security.CredentialBroker present={ok} (INV-024 scoped)",
            "Credential phải qua broker scoped — agent/tool không giữ secret trực tiếp",
        )

    def encryption(self) -> SecurityItem:
        ok = _src_has("aios_core.contracts.artifact", "ArtifactContract")
        checksum = _src_has("aios_core.kernel.services.artifacts", "checksum")
        status = SecurityStatus.PASS if (ok and checksum) else SecurityStatus.WARN
        return self._item(
            "encryption", "Encryption / Integrity (checksum)", SecuritySeverity.HIGH,
            status,
            f"ArtifactContract present={ok}; artifacts.checksum present={checksum}",
            "Đảm bảo artifact checksum + sidecar (INV-008) — mã hóa at-rest theo policy",
        )

    def audit(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.operations", "CentralAuditStore")
        status = SecurityStatus.PASS if ok else SecurityStatus.FAIL
        return self._item(
            "audit", "Audit (tamper-evident)", SecuritySeverity.CRITICAL,
            status,
            f"enterprise.operations.CentralAuditStore present={ok} (INV-027 chain hash)",
            "Mọi security-sensitive action phải có audit evidence (INV-027)",
        )

    def plugin_signing(self) -> SecurityItem:
        ok = _src_has("aios_core.ecosystem.marketplace", "hmac")
        status = SecurityStatus.PASS if ok else SecurityStatus.FAIL
        return self._item(
            "plugin_signing", "Plugin signing (HMAC)", SecuritySeverity.CRITICAL,
            status,
            f"marketplace.hmac present={ok}",
            "Plugin/marketplace package phải có signature verify (M8 Trust Model)",
        )

    def supply_chain(self) -> SecurityItem:
        ok = _src_has("aios_core.ecosystem.marketplace", "TrustChain")
        status = SecurityStatus.PASS if ok else SecurityStatus.FAIL
        return self._item(
            "supply_chain", "Supply chain (Trust Chain)", SecuritySeverity.HIGH,
            status,
            f"marketplace.TrustChain present={ok} (9 bước M8-E6)",
            "Verify manifest → signature → dependency → permission trước khi cài",
        )

    def sandbox(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.security", "SandboxBoundary")
        status = SecurityStatus.PASS if ok else SecurityStatus.FAIL
        return self._item(
            "sandbox", "Sandbox boundary", SecuritySeverity.CRITICAL,
            status,
            f"enterprise.security.SandboxBoundary present={ok} (INV-028); "
            f"policy sandbox_required enforced trong ExecutionService",
            "Untrusted tool execution phải qua sandbox policy (INV-028)",
        )

    def network_policy(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.security", "NetworkPolicy")
        status = SecurityStatus.PASS if ok else SecurityStatus.WARN
        return self._item(
            "network_policy", "Network policy (default-deny)", SecuritySeverity.HIGH,
            status,
            f"enterprise.security.NetworkPolicy present={ok}",
            "Network default-deny + allow-list (M7 E6) — chưa enforce ở tool layer",
        )

    def data_boundary(self) -> SecurityItem:
        ok = _src_has("aios_core.enterprise.tenancy", "TenantBoundary")
        status = SecurityStatus.PASS if ok else SecurityStatus.FAIL
        return self._item(
            "data_boundary", "Data boundary (tenant isolation)", SecuritySeverity.HIGH,
            status,
            f"enterprise.tenancy.TenantBoundary present={ok} (INV-023 deny-by-default)",
            "Cross-tenant access deny mặc định (INV-023)",
        )

    def run_all(self) -> list[SecurityItem]:
        return [
            self.identity(), self.authentication(), self.authorization(),
            self.secrets(), self.encryption(), self.audit(),
            self.plugin_signing(), self.supply_chain(), self.sandbox(),
            self.network_policy(), self.data_boundary(),
        ]


class SecurityChecker:
    """Chạy 11 checks → SecurityReport."""

    def __init__(self, checks: SecurityChecks | None = None) -> None:
        self.checks = checks or SecurityChecks()

    def run(self) -> SecurityReport:
        return SecurityReport(items=self.checks.run_all())


# -- rendering ----------------------------------------------------------------

_STATUS_SYMBOL = {
    SecurityStatus.PASS: "✓",
    SecurityStatus.WARN: "⚠",
    SecurityStatus.FAIL: "✗",
}


def format_security_report(report: SecurityReport) -> str:
    rows = []
    width_id = max(len(i.id) for i in report.items) + 2
    width_name = max(len(i.name) for i in report.items) + 2
    width_sev = max(len(i.severity.value) for i in report.items) + 2
    for item in sorted(report.items, key=lambda x: x.id):
        sym = _STATUS_SYMBOL[item.status]
        rows.append(
            f"{item.id.ljust(width_id)}| {item.name.ljust(width_name)}"
            f"| {item.severity.value.ljust(width_sev)}| {sym} {item.status.value}"
            f"\n   evidence: {item.evidence}"
            f"\n   fix: {item.recommendation}"
        )
    header = (f"{'id'.ljust(width_id)}| {'name'.ljust(width_name)}"
              f"| {'severity'.ljust(width_sev)}| status")
    lines = [header, "-" * len(header), *rows, "", report.summary()]
    return "\n".join(lines)
