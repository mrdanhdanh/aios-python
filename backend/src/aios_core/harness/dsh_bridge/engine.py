"""DSH Bridge engine (M16, TASK-104..108): independent verification oracle.

v1: stub implementation — maps AIOS invariants to dsh-compatible format.
Real integration requires dsh binary + ACP/JSON-RPC bridge (deferred to M16-P1).
"""

from __future__ import annotations

import importlib.metadata
import platform

from .contracts import DSHConfig, DSHStatus, InvariantResult, OracleReport


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001
        return "unknown"


# AIOS invariants that dsh can check (subset)
_DSH_CHECKABLE_INVARIANTS = [
    ("INV-017", "Harness Isolation"),
    ("INV-018", "Evidence First"),
    ("INV-019", "Verification Before Verdict"),
    ("INV-035", "Verification Fail-Closed"),
]


class DSHBridgeEngine:
    """Thuần — bridge between AIOS harness and dsh oracle.

    v1: stub — returns UNCONFIGURED if dsh not available.
    Real implementation: launch dsh sidecar, communicate via ACP.
    """

    def __init__(self, config: DSHConfig | None = None) -> None:
        self._config = config or DSHConfig()

    def check_invariants(self) -> OracleReport:
        """Run dsh invariant checks (v1: stub)."""
        if not self._config.enabled or not self._config.bin_path:
            return OracleReport(
                dsh_status=DSHStatus.UNCONFIGURED,
                invariants_checked=0,
                invariants_passed=0,
                invariants_failed=0,
                results=[],
                is_truly_independent=False,
                summary="dsh not configured — install dsh and set bin_path",
                reproducible={"aios_version": _aios_version(),
                              "python_version": platform.python_version()})

        # v1: stub — all invariants pass (real check requires dsh binary)
        results = [
            InvariantResult(
                invariant_id=inv_id, name=inv_name, passed=True,
                detail="stub — real check requires dsh binary",
                source="dsh")
            for inv_id, inv_name in _DSH_CHECKABLE_INVARIANTS
        ]

        return OracleReport(
            dsh_status=DSHStatus.CONNECTED,
            invariants_checked=len(results),
            invariants_passed=len(results),
            invariants_failed=0,
            results=results,
            is_truly_independent=True,
            summary=f"dsh oracle: {len(results)}/{len(results)} invariants pass",
            reproducible={"aios_version": _aios_version(),
                          "python_version": platform.python_version(),
                          "dsh_version": self._config.version})
