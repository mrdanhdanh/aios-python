"""Release Gate engine (M13-P3, TASK-092): pure combiner 2 score độc lập.

System Readiness (HarnessReadinessReport) + Harness Trust (MetaReport) →
ReleaseGateReport. Engine KHÔNG tính readiness/trust — chỉ tổ hợp report
đã có (chống circular, tách biệt thật). Pure function (không I/O).
"""

from __future__ import annotations

import importlib.metadata
import platform

from ..coverage.contracts import HarnessReadinessReport, HarnessReadinessStatus
from ..meta.contracts import MetaReport, MetaStatus
from .contracts import ReleaseGateReport, ReleaseGateStatus


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001 — dev/editable install
        return "unknown"


class ReleaseGateEngine:
    """Thuần — combiner 2 score độc lập (KHÔNG tính readiness/trust)."""

    def evaluate(
        self,
        readiness: HarnessReadinessReport,
        meta: MetaReport,
    ) -> ReleaseGateReport:
        sr_ready = readiness.status == HarnessReadinessStatus.READY
        ht_pass = meta.status == MetaStatus.PASS
        both = sr_ready and ht_pass
        status = ReleaseGateStatus.PASS if both else ReleaseGateStatus.BLOCKED

        # summary chỉ rõ lý do block (tách biệt rõ ràng giữa 2 score)
        if both:
            summary = "RELEASE PASS (system_ready + harness_trust)"
        else:
            reasons: list[str] = []
            if not sr_ready:
                reasons.append(
                    f"system_readiness {readiness.status.value.upper()}")
            if not ht_pass:
                reasons.append(f"harness_trust {meta.status.value.upper()}")
            summary = "RELEASE BLOCKED: " + " + ".join(reasons)

        return ReleaseGateReport(
            system_readiness={
                "status": readiness.status.value,
                "summary": readiness.summary,
            },
            harness_trust={
                "status": meta.status.value,
                "summary": meta.summary,
            },
            both_pass=both,
            status=status,
            summary=summary,
            reproducible={
                "aios_version": _aios_version(),
                "python_version": platform.python_version(),
            },
        )
