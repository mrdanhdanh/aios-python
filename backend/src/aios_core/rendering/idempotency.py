"""AssetIdempotencyClassifier — M11-P1 (TASK-079).

Mượn IdempotencyClassifier (M10 durability) cho asset generation:
  - exactly-once  : idempotent write — retry OK (kết quả như nhau)
  - at-least-once : read-like — retry OK
  - at-most-once  : non-idempotent — approve/compensate (KHÔNG tự retry)
Fail-closed: asset không khai báo class → at-most-once (giống M10).
"""

from __future__ import annotations

from enum import Enum


class AssetOpClass(str, Enum):
    EXACTLY_ONCE = "exactly_once"
    AT_LEAST_ONCE = "at_least_once"
    AT_MOST_ONCE = "at_most_once"


class AssetRetryDecision(str, Enum):
    RETRY = "retry"          # exactly-once / at-least-once
    APPROVE = "approve"      # at-most-once chưa fail — cần human
    COMPENSATE = "compensate"  # at-most-once đã fail — bù trừ trước khi chạy lại


class AssetIdempotencyClassifier:
    """Phân loại idempotency cho asset generation (fail-closed)."""

    def __init__(
        self,
        exactly_once: set[str] | None = None,
        at_least_once: set[str] | None = None,
    ) -> None:
        self._exact = exactly_once or set()
        self._least = at_least_once or set()

    def classify(self, asset_kind: str) -> AssetOpClass:
        if asset_kind in self._exact:
            return AssetOpClass.EXACTLY_ONCE
        if asset_kind in self._least:
            return AssetOpClass.AT_LEAST_ONCE
        # Fail-closed: không khai báo → at-most-once (KHÔNG tự retry)
        return AssetOpClass.AT_MOST_ONCE

    def decision(self, asset_kind: str, has_failed: bool = False) -> AssetRetryDecision:
        cls = self.classify(asset_kind)
        if cls in (AssetOpClass.EXACTLY_ONCE, AssetOpClass.AT_LEAST_ONCE):
            return AssetRetryDecision.RETRY
        # at-most-once: không tự retry
        return (
            AssetRetryDecision.COMPENSATE
            if has_failed
            else AssetRetryDecision.APPROVE
        )

    def is_retryable(self, asset_kind: str) -> bool:
        return self.classify(asset_kind) in (
            AssetOpClass.EXACTLY_ONCE,
            AssetOpClass.AT_LEAST_ONCE,
        )
