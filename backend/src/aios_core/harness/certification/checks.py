"""Certification Suite 1.0 — 11 area checks (structural, M10-F5 + M11 + M12).

Area = "hệ thống có đúng cơ chế" (structural). Mỗi check dùng component
thật — không hard-code PASS (R1).
"""

from __future__ import annotations

from typing import Any

from .contracts import AreaResult, CertificationArea, PassFail


class AreaChecks:
    """11 area checks — deterministic, component thật."""

    def __init__(self, kernel: Any | None = None) -> None:
        self.kernel = kernel

    def _get_kernel(self):
        if self.kernel is None:
            from ...kernel.runtime_kernel import RuntimeKernel

            self.kernel = RuntimeKernel.create()
        return self.kernel

    def _result(self, area, ok: bool, evidence: str) -> AreaResult:
        return AreaResult(area, PassFail.PASS if ok else PassFail.FAIL, evidence)

    # -- 9 checks ------------------------------------------------------------
    def architecture(self) -> AreaResult:
        try:
            from ...observability.arch_health import ArchitectureHealth

            report = ArchitectureHealth().scan()
            ok = bool(report.healthy) and len(report.violations) == 0
            return self._result("architecture", ok,
                                f"scanner violations={len(report.violations)}")
        except Exception as exc:  # noqa: BLE001
            return self._result("architecture", False, str(exc))

    def contracts(self) -> AreaResult:
        try:
            from ...contracts.check import ContractChecker

            report = ContractChecker().check_all()
            ok = report.breaking_count == 0
            return self._result("contracts", ok,
                                f"breaking={report.breaking_count}, "
                                f"warnings={report.warning_count}")
        except Exception as exc:  # noqa: BLE001
            return self._result("contracts", False, str(exc))

    def runtime(self) -> AreaResult:
        try:
            from ...cli.doctor import DoctorFirstClass

            report = DoctorFirstClass(self._get_kernel()).run()
            by_id = {c.item_id: c for c in report.checks}
            ok = by_id["runtime"].status == "pass" and by_id["events"].status == "pass"
            return self._result("runtime", ok,
                                f"doctor score={report.score}/100")
        except Exception as exc:  # noqa: BLE001
            return self._result("runtime", False, str(exc))

    def policy(self) -> AreaResult:
        try:
            from ...kernel.services import PolicyService

            kernel = self._get_kernel()
            policy = kernel.container.resolve(PolicyService)
            ok = policy is not None
            return self._result("policy", ok, "PolicyService registered (INV-007)")
        except Exception as exc:  # noqa: BLE001
            return self._result("policy", False, str(exc))

    def security(self) -> AreaResult:
        try:
            from ...security import SecurityChecker

            report = SecurityChecker().run()
            # Gate B: FAIL critical ∨ FAIL high → fail
            hard_fails = [
                i for i in report.failures
                if i.severity.value in ("critical", "high")
            ]
            ok = not hard_fails
            return self._result("security", ok,
                                f"failures={len(report.failures)}, "
                                f"hard={[i.id for i in hard_fails]}")
        except Exception as exc:  # noqa: BLE001
            return self._result("security", False, str(exc))

    def autonomy(self) -> AreaResult:
        try:
            from ...autonomous import AutonomyManager

            kernel = self._get_kernel()
            mgr = kernel.container.resolve(AutonomyManager)
            ok = mgr is not None and mgr.governor is not None
            return self._result("autonomy", ok, "AutonomyManager + Governor present")
        except Exception as exc:  # noqa: BLE001
            return self._result("autonomy", False, str(exc))

    def harness(self) -> AreaResult:
        try:
            from ...harness import HarnessRegistry

            kernel = self._get_kernel()
            registry = kernel.container.resolve(HarnessRegistry)
            count = len(registry.list()) if hasattr(registry, "list") else 0
            ok = count >= 5
            return self._result("harness", ok, f"{count} harnesses registered")
        except Exception as exc:  # noqa: BLE001
            return self._result("harness", False, str(exc))

    def enterprise(self) -> AreaResult:
        try:
            from ...enterprise import EnterpriseManager

            kernel = self._get_kernel()
            mgr = kernel.container.resolve(EnterpriseManager)
            ok = mgr is not None and mgr.identity is not None
            return self._result("enterprise", ok, "EnterpriseManager + identity present")
        except Exception as exc:  # noqa: BLE001
            return self._result("enterprise", False, str(exc))

    def ecosystem(self) -> AreaResult:
        try:
            from ...ecosystem.registry import EcosystemRegistry
            from ...plugins.registry import PluginRegistry

            # structural: module + method tồn tại (registry tạo qua settings)
            has_eco = hasattr(EcosystemRegistry, "index_entry") and \
                hasattr(EcosystemRegistry, "search")
            has_plugin = hasattr(PluginRegistry, "get")
            ok = has_eco and has_plugin
            return self._result("ecosystem", ok,
                                f"EcosystemRegistry={has_eco}, PluginRegistry={has_plugin}")
        except Exception as exc:  # noqa: BLE001
            return self._result("ecosystem", False, str(exc))

    def verification(self) -> AreaResult:
        """INV-035 (M11-P0): Verification Kernel tồn tại + fail-closed thật.

        Chạy component thật (không hard-code PASS — R1): gate với một
        mechanism mock trả non-terminal + claim PASS → verdict không PASS.
        """
        try:
            from ...verification import (
                VerificationGate,
                VerificationOutcome,
                VerificationState,
                VerificationVerdict,
            )

            class _BadMechanism:
                id = "mock-nonterminal"
                name = "Mock non-terminal"
                version = "0.0.0"

                def check(self) -> VerificationOutcome:
                    # Cố tình vi phạm: state SKIPPED nhưng claim PASS
                    return VerificationOutcome(
                        mechanism_id=self.id,
                        state=VerificationState.SKIPPED,
                        verdict=VerificationVerdict.PASS,
                        evidence="mock skip → PASS claim",
                    )

            report = VerificationGate([_BadMechanism()]).check_all()
            ok = not report.fail_closed and len(report.violations) == 1
            return self._result(
                "verification", ok,
                "INV-035: gate chặn non-terminal→PASS "
                f"(violations={report.violations})",
            )
        except Exception as exc:  # noqa: BLE001
            return self._result("verification", False, str(exc))

    def compatibility(self) -> AreaResult:
        """AIOS 1.1 Compatibility (M12-P3 C4, TASK-087): matrix + backward suite.

        Structural — KHÔNG gọi ``_get_kernel()`` (C2-05); CHỈ relative import
        upgrade/* (layer rule cấm import root ``aios_core`` — arch-health
        bắt `from ... import __version__`). Component thật:
        CompatibilityMatrix.list() + BackwardCompatibilitySuite.run() + version.
        """
        try:
            from ...upgrade.backward_compat import BackwardCompatibilitySuite
            from ...upgrade.compatibility import AIOS_VERSION, CompatibilityMatrix

            rows = CompatibilityMatrix().list()
            report = BackwardCompatibilitySuite().run()
            ok = (len(rows) >= 14 and report.ok
                  and AIOS_VERSION == "1.1.0")
            passed = sum(1 for r in report.results if r.ok)
            return self._result(
                "compatibility", ok,
                f"matrix={len(rows)} entries, "
                f"verify={passed}/{len(report.results)}, version={AIOS_VERSION}",
            )
        except Exception as exc:  # noqa: BLE001
            return self._result("compatibility", False, str(exc))

    def run_all(self) -> list[AreaResult]:
        return [
            self.architecture(), self.contracts(), self.runtime(),
            self.policy(), self.security(), self.autonomy(),
            self.harness(), self.enterprise(), self.ecosystem(),
            self.verification(), self.compatibility(),
        ]
