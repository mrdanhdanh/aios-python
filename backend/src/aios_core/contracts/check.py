"""Contract Checker 1.0 — M10-F2 (TASK-064).

Contract Compatibility Matrix: mỗi contract ✓/⚠/✗ + breaking/warning count +
deprecated API detector. Dùng chung CompatibilityChecker (M1) cho semver.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import ContractCatalog, ContractDefinition, ContractLifecycle


class CheckStatus(str):
    OK = "ok"            # ✓ compatible, không warning
    WARNING = "warning"  # ⚠ deprecated / dùng API cũ (không chặn release)
    BREAKING = "breaking"  # ✗ breaking (chặn release — Gate C)


@dataclass(frozen=True)
class ContractCheckResult:
    contract_id: str
    version: str
    lifecycle: str
    status: str
    reason: str


@dataclass(frozen=True)
class DeprecationWarning:
    contract_id: str
    deprecated_in: str
    migration_path: str
    message: str


@dataclass
class ContractMatrixReport:
    results: list[ContractCheckResult] = field(default_factory=list)
    deprecation_warnings: list[DeprecationWarning] = field(default_factory=list)

    @property
    def breaking_count(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.BREAKING)

    @property
    def warning_count(self) -> int:
        return sum(1 for r in self.results if r.status == CheckStatus.WARNING) + \
            len(self.deprecation_warnings)

    @property
    def blocking(self) -> bool:
        """Breaking = chặn release (Gate C — breaking compatibility = 0)."""
        return self.breaking_count > 0


class ContractChecker:
    """Đánh giá trạng thái freeze của 10 public contracts."""

    def __init__(self, catalog: ContractCatalog | None = None) -> None:
        self.catalog = catalog or ContractCatalog()

    # -- matrix ------------------------------------------------------------
    def check_all(self, used: list[str] | None = None) -> ContractMatrixReport:
        """Matrix toàn bộ contract.

        - lifecycle DEPRECATED → ⚠ (warning, có migration_path)
        - lifecycle REMOVED → ✗ (breaking)
        - schema_ref không import được → ✗ (breaking — contract hỏng)
        - còn lại → ✓
        """
        report = ContractMatrixReport()
        for contract in self.catalog.all():
            report.results.append(self._check_contract(contract))
        report.deprecation_warnings = self.check_deprecated_usage(used or [])
        return report

    def _check_contract(self, contract: ContractDefinition) -> ContractCheckResult:
        if contract.lifecycle == ContractLifecycle.REMOVED:
            return ContractCheckResult(
                contract.id, contract.version, contract.lifecycle.value,
                CheckStatus.BREAKING, "contract REMOVED — không còn hỗ trợ",
            )
        if not contract.schema_exists():
            return ContractCheckResult(
                contract.id, contract.version, contract.lifecycle.value,
                CheckStatus.BREAKING,
                f"schema_ref {contract.schema_ref[0]}.{contract.schema_ref[1]} không import được",
            )
        if contract.lifecycle == ContractLifecycle.DEPRECATED:
            return ContractCheckResult(
                contract.id, contract.version, contract.lifecycle.value,
                CheckStatus.WARNING,
                f"deprecated since {contract.deprecated_in} — migration: "
                f"{contract.migration_path}",
            )
        return ContractCheckResult(
            contract.id, contract.version, contract.lifecycle.value,
            CheckStatus.OK, "compatible",
        )

    # -- deprecated API detector --------------------------------------------
    def check_deprecated_usage(self, used: list[str]) -> list[DeprecationWarning]:
        """Detect usage của contract DEPRECATED trong danh sách `used`.

        used = id contract mà hệ thống/plugin đang dùng.
        """
        warnings: list[DeprecationWarning] = []
        for contract_id in used:
            try:
                contract = self.catalog.get(contract_id)
            except KeyError:
                continue
            if contract.lifecycle == ContractLifecycle.DEPRECATED:
                warnings.append(
                    DeprecationWarning(
                        contract_id=contract.id,
                        deprecated_in=contract.deprecated_in or "?",
                        migration_path=contract.migration_path or "",
                        message=f"{contract.name} (v{contract.version}) đã deprecated — "
                                f"nên di chuyển: {contract.migration_path}",
                    )
                )
        return warnings


# -- rendering (CLI) ---------------------------------------------------------

_STATUS_SYMBOL = {
    CheckStatus.OK: "✓",
    CheckStatus.WARNING: "⚠",
    CheckStatus.BREAKING: "✗",
}


def format_matrix(report: ContractMatrixReport, catalog: ContractCatalog) -> str:
    """In Contract Compatibility Matrix (cột padding cố định — R3)."""
    rows = []
    width_id = max(len(r.contract_id) for r in report.results) + 2
    width_ver = max(len(r.version) for r in report.results) + 2
    width_life = max(len(r.lifecycle) for r in report.results) + 2
    for r in sorted(report.results, key=lambda x: x.contract_id):
        sym = _STATUS_SYMBOL[r.status]
        rows.append(
            f"{r.contract_id.ljust(width_id)}| {r.version.ljust(width_ver)}"
            f"| {r.lifecycle.ljust(width_life)}| {sym} {r.reason}"
        )
    header = (
        f"{'id'.ljust(width_id)}| {'version'.ljust(width_ver)}"
        f"| {'lifecycle'.ljust(width_life)}| status"
    )
    lines = [header, "-" * len(header), *rows]
    if report.deprecation_warnings:
        lines.append("")
        lines.append("Deprecated usage warnings:")
        for w in report.deprecation_warnings:
            lines.append(f"  ⚠ {w.message}")
    lines.append("")
    lines.append(f"Breaking changes: {report.breaking_count} · "
                 f"Warnings: {report.warning_count}")
    return "\n".join(lines)
