"""Diagnose engine (M14-P0, TASK-094): analyze failures + signature + localize.

Pure function — KHÔNG I/O, deterministic. Input: HarnessReport → Output: FailureRecord.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import platform
import re
from datetime import datetime, timezone

from ..contracts import HarnessReport, HarnessRunStatus
from ..errors import (
    HarnessError,
    HarnessHookError,
    HarnessLifecycleError,
)
from .contracts import FailureRecord, FailureSeverity


def _aios_version() -> str:
    try:
        return importlib.metadata.version("aios_core")
    except Exception:  # noqa: BLE001
        return "unknown"


# --- Severity mapping (critique-2 P1: cover all error subclasses) ---

_SEVERITY_MAP: dict[str, FailureSeverity] = {
    "ReleaseGateError": FailureSeverity.HIGH,
    "MetaError": FailureSeverity.HIGH,
    "HarnessHookError": FailureSeverity.HIGH,
    "CoverageError": FailureSeverity.MEDIUM,
    "BehavioralConformanceError": FailureSeverity.MEDIUM,
    "ReadinessError": FailureSeverity.MEDIUM,
    "HarnessLifecycleError": FailureSeverity.MEDIUM,
    "HarnessRegistrationError": FailureSeverity.LOW,
    "HarnessNotFoundError": FailureSeverity.LOW,
    "HarnessError": FailureSeverity.LOW,
}

# --- Message normalization patterns ---

# Strip ISO timestamps: 2026-08-18T12:34:56.789+00:00
_RE_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[\.\d]*[Z+\-:\d]*")
# Strip UUIDs: 550e8400-e29b-41d4-a716-446655440000
_RE_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
# Strip absolute paths (Windows + Unix)
_RE_WIN_PATH = re.compile(r"[A-Z]:\\[\w\\. -]+")
_RE_UNIX_PATH = re.compile(r"/[\w/.\-]+")
# Strip hex values: 0x7fff5fbff8d0
_RE_HEX = re.compile(r"0x[0-9a-f]+", re.I)
# Strip line numbers: line 42, at line 42
_RE_LINE_NUM = re.compile(r"\bline\s+\d+", re.I)
# Strip memory addresses: 0x7fff5fbff8d0
_RE_ADDR = re.compile(r"\b0x[0-9a-f]{4,}\b", re.I)
# Strip run IDs: harness:release:18cca6f2e5dfb650
_RE_RUN_ID = re.compile(r"\b\w+:\w+:[0-9a-f]{8,}\b")


class DiagnoseEngine:
    """Thuần — phân tích failure + sinh signature + localize component."""

    def analyze(self, report: HarnessReport) -> FailureRecord | None:
        """Tạo FailureRecord từ HarnessReport. Trả None nếu report COMPLETED."""
        if report.result.status not in (
            HarnessRunStatus.FAILED, HarnessRunStatus.DIAGNOSED
        ):
            return None

        # Extract error info from report
        error_type, error_message = self._extract_error(report)
        component = self._localize_component(report, error_message)
        normalized_msg = self.normalize_message(error_message)
        signature = self.compute_signature(error_type, component, normalized_msg)
        severity = self._map_severity(error_type)

        # Extract subset evidence (critique-2 P2: lightweight)
        evidence = {
            "summary": report.result.summary,
            "error_type": error_type,
            "status": report.result.status.value,
            "metrics": report.result.metrics,
        }

        return FailureRecord(
            run_id=report.run_id,
            harness_id=report.result.summary.split(":")[0] if ":" in report.result.summary else "unknown",
            status=report.result.status.value,
            error_type=error_type,
            error_message=normalized_msg,
            component=component,
            signature=signature,
            severity=severity,
            evidence=evidence,
            timestamp=datetime.now(timezone.utc),
        )

    def compute_signature(
        self, error_type: str, component: str, normalized_message: str
    ) -> str:
        """Deterministic signature — same input → same hash."""
        raw = f"{error_type}|{component}|{normalized_message}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def normalize_message(self, message: str) -> str:
        """Strip variable data — keep pattern for signature stability."""
        msg = message
        msg = _RE_TIMESTAMP.sub("<TIMESTAMP>", msg)
        msg = _RE_UUID.sub("<UUID>", msg)
        msg = _RE_RUN_ID.sub("<RUN_ID>", msg)
        msg = _RE_WIN_PATH.sub("<PATH>", msg)
        msg = _RE_UNIX_PATH.sub("<PATH>", msg)
        msg = _RE_HEX.sub("<HEX>", msg)
        msg = _RE_ADDR.sub("<ADDR>", msg)
        msg = _RE_LINE_NUM.sub("line <N>", msg)
        # Collapse multiple spaces
        msg = re.sub(r"\s+", " ", msg).strip()
        return msg

    def _extract_error(self, report: HarnessReport) -> tuple[str, str]:
        """Extract error type + message from report summary."""
        summary = report.result.summary
        # summary format: "harness:run_id -> FAILED: ErrorType: message"
        # or "harness:run_id -> DIAGNOSED: ErrorType: message"
        error_type = "HarnessError"
        error_message = summary

        if " -> " in summary:
            error_part = summary.split(" -> ", 1)[1]
            # error_part = "FAILED: HarnessLifecycleError: bad transition"
            # Strip status prefix: "FAILED: " or "DIAGNOSED: "
            for prefix in ("FAILED: ", "DIAGNOSED: "):
                if error_part.startswith(prefix):
                    error_part = error_part[len(prefix):]
                    break
            # Now error_part = "HarnessLifecycleError: bad transition"
            if ":" in error_part:
                parts = error_part.split(":", 1)
                candidate = parts[0].strip()
                if candidate.endswith("Error") or candidate.endswith("Exception"):
                    error_type = candidate
                    error_message = parts[1].strip() if len(parts) > 1 else ""
                else:
                    error_message = error_part
            else:
                error_message = error_part

        return error_type, error_message

    def _localize_component(
        self, report: HarnessReport, error_message: str
    ) -> str:
        """Localize component from error message or report summary."""
        summary = report.result.summary

        # Extract harness id from summary (format: "harness_id:run_id -> STATUS")
        if ":" in summary:
            harness_id = summary.split(":")[0]
            return f"harness/{harness_id}"

        # Fallback: check error message for module patterns
        module_match = re.search(r"aios_core\.\S+", error_message)
        if module_match:
            return module_match.group(0)

        return "unknown"

    def _map_severity(self, error_type: str) -> FailureSeverity:
        """Map error type to severity (critique-2 P1: all subclasses)."""
        return _SEVERITY_MAP.get(error_type, FailureSeverity.LOW)


def build_corpus_report(
    records: list[FailureRecord],
) -> "FailureCorpusReport":
    """Build summary report from corpus records."""
    from .contracts import FailureCorpusReport

    by_harness: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_component: dict[str, int] = {}
    signatures: set[str] = set()

    for r in records:
        by_harness[r.harness_id] = by_harness.get(r.harness_id, 0) + 1
        by_severity[r.severity.value] = by_severity.get(r.severity.value, 0) + 1
        by_component[r.component] = by_component.get(r.component, 0) + 1
        signatures.add(r.signature)

    recent = sorted(records, key=lambda r: r.timestamp, reverse=True)[:10]

    return FailureCorpusReport(
        total=len(records),
        by_harness=by_harness,
        by_severity=by_severity,
        by_component=by_component,
        unique_signatures=len(signatures),
        recent=recent,
        reproducible={
            "aios_version": _aios_version(),
            "python_version": platform.python_version(),
        },
    )
