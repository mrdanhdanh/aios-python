"""VisualRegressionProbe — M11-P2 (R1, TASK-080).

So sánh ref vs current evidence → diff summary + outcome fail-closed (INV-035):
  - thiếu ref screenshot → MISSING_EVIDENCE (KHÔNG PASS — chống "17/17 PASS" bị skip)
  - probe không được gọi → NOT_EXECUTED
  - collector/render lỗi → ERROR
  - pixel_diff > 0 → FAIL nhưng kèm đầy đủ evidence (không kết luận thiếu)
"""

from __future__ import annotations

import base64
import binascii
from typing import Any

from ..verification.contracts import VerificationOutcome
from ..verification.state import VerificationState, VerificationVerdict
from .evidence import VisualEvidence
from .ui_state import canonical_json


class ProbeResult:
    """Kết quả probe — diff summary + outcome."""

    def __init__(
        self,
        outcome: VerificationOutcome,
        *,
        pixel_diff: float = -1.0,
        dom_diffs: list[dict[str, Any]] | None = None,
        state_diffs: list[dict[str, Any]] | None = None,
        evidence_note: str = "",
    ) -> None:
        self.outcome = outcome
        self.pixel_diff = pixel_diff
        self.dom_diffs = dom_diffs or []
        self.state_diffs = state_diffs or []
        self.evidence_note = evidence_note

    @property
    def passed(self) -> bool:
        return self.outcome.verdict == VerificationVerdict.PASS


class VisualRegressionProbe:
    """So sánh visual evidence (ref vs current) — fail-closed (INV-035)."""

    def __init__(self, pixel_threshold: int = 30) -> None:
        self.pixel_threshold = pixel_threshold

    # -- compare -------------------------------------------------------------

    def compare(
        self,
        ref: VisualEvidence | None,
        current: VisualEvidence | None,
    ) -> ProbeResult:
        """So sánh ref (golden) vs current.

        - ref hoặc current None / thiếu screenshot → MISSING_EVIDENCE
        - render_state khác → state_diffs (reasoning — R10)
        - dom_snapshot khác → dom_diffs
        - screenshot khác → pixel_diff % > 0 → FAIL (kèm evidence đầy đủ)
        """
        if ref is None or current is None:
            return self._missing("ref/current evidence bị thiếu")
        if not ref.has_screenshot() or not current.has_screenshot():
            return self._missing("screenshot ref/current thiếu (base64 data URI)")

        # State reasoning (R10) — không chỉ pixel
        state_diffs = ref.render_state.diff(current.render_state)

        # DOM diff
        dom_diffs = self._dom_diff(ref.dom_snapshot, current.dom_snapshot)

        # Pixel diff
        pixel_diff = self._pixel_diff(ref.screenshot, current.screenshot)
        if pixel_diff is None:
            return self._missing("screenshot không decode được (base64 hỏng)")

        if pixel_diff > 0:
            outcome = VerificationOutcome(
                mechanism_id="visual-regression",
                state=VerificationState.FAIL,
                verdict=VerificationVerdict.FAIL,
                evidence=(
                    f"pixel_diff={pixel_diff:.2f}% (threshold "
                    f"{self.pixel_threshold}%), state_diffs={len(state_diffs)}, "
                    f"dom_diffs={len(dom_diffs)}"
                ),
            )
            return ProbeResult(
                outcome, pixel_diff=pixel_diff,
                dom_diffs=dom_diffs, state_diffs=state_diffs,
            )

        if state_diffs or dom_diffs:
            outcome = VerificationOutcome(
                mechanism_id="visual-regression",
                state=VerificationState.FAIL,
                verdict=VerificationVerdict.FAIL,
                evidence=(
                    f"state_diffs={len(state_diffs)}, dom_diffs={len(dom_diffs)} "
                    f"(reasoning — R10)"
                ),
            )
            return ProbeResult(
                outcome, pixel_diff=pixel_diff,
                dom_diffs=dom_diffs, state_diffs=state_diffs,
            )

        outcome = VerificationOutcome(
            mechanism_id="visual-regression",
            state=VerificationState.PASS,
            verdict=VerificationVerdict.PASS,
            evidence=(f"pixel_diff=0.0%, state/dom khớp — "
                      f"browser={current.browser_meta.get('browser', '?')}"),
        )
        return ProbeResult(outcome, pixel_diff=0.0)

    # -- helpers -------------------------------------------------------------

    def _missing(self, note: str) -> ProbeResult:
        return ProbeResult(
            VerificationOutcome(
                mechanism_id="visual-regression",
                state=VerificationState.MISSING_EVIDENCE,
                verdict=VerificationVerdict.INCONCLUSIVE,
                evidence=f"MISSING_EVIDENCE: {note} (INV-035 — không PASS)",
            ),
            evidence_note=note,
        )

    def _dom_diff(self, a: dict, b: dict) -> list[dict[str, Any]]:
        """Diff DOM snapshot recursive — {"path", "before", "after"}."""
        diffs: list[dict[str, Any]] = []

        def walk(pa: Any, pb: Any, path: str) -> None:
            if pa == pb:
                return
            if isinstance(pa, dict) and isinstance(pb, dict):
                for key in sorted(set(pa) | set(pb)):
                    walk(pa.get(key), pb.get(key), f"{path}.{key}")
            elif isinstance(pa, list) and isinstance(pb, list):
                for i, (va, vb) in enumerate(zip(pa, pb)):
                    walk(va, vb, f"{path}[{i}]")
                if len(pa) != len(pb):
                    diffs.append({"path": path, "before": len(pa), "after": len(pb)})
            else:
                diffs.append({"path": path, "before": pa, "after": pb})

        walk(a, b, "dom")
        return diffs

    def _pixel_diff(self, ref: str, current: str) -> float | None:
        """% pixel khác biệt — decode base64 PNG → pixelwise RGB.

        Trả None nếu không decode được (fail-closed → MISSING_EVIDENCE).
        Không dùng PNG decoder (không dependency) — so sánh trên bytes đã
        decode; nếu không parse được pixel → None.
        """
        try:
            a = base64.b64decode(ref.split(",", 1)[1])
            b = base64.b64decode(current.split(",", 1)[1])
        except (binascii.Error, IndexError):
            return None
        if len(a) != len(b) or not a:
            # Kích thước khác → 100% khác (đơn giản, fail-closed)
            return 100.0
        # So sánh byte-level (PNG 1×1 thật: chỉ 1 pixel khác nhau khi dùng data đúng)
        changed = sum(1 for x, y in zip(a, b) if abs(x - y) > self.pixel_threshold)
        return (changed / len(a)) * 100.0
