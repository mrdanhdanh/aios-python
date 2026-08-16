"""Visual observability metrics — M11-P2 (R1, TASK-080).

In-memory counters + gauge (không SQLite — visual probe là tần suất thấp):
  - visual_probe_count               : tổng probe chạy
  - visual_fail_closed_violations    : probe outcome KHÔNG PASS (fail-closed)
  - visual_pixel_diff_max            : gauge — pixel diff % lớn nhất (quan sát,
                                       KHÔNG phải SLO — metric sau evidence)
Register idempotent + lazy (không sửa RuntimeKernel).
"""

from __future__ import annotations

import threading
from typing import Any


class VisualMetrics:
    """Registry visual metrics — thread-safe, idempotent."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {
            "visual_probe_count": 0,
            "visual_fail_closed_violations": 0,
        }
        self._gauges: dict[str, float] = {
            "visual_pixel_diff_max": -1.0,
        }

    def record_probe(self, *, passed: bool, pixel_diff: float) -> None:
        """Ghi kết quả một probe."""
        with self._lock:
            self._counters["visual_probe_count"] += 1
            if not passed:
                self._counters["visual_fail_closed_violations"] += 1
            if pixel_diff > self._gauges["visual_pixel_diff_max"]:
                self._gauges["visual_pixel_diff_max"] = pixel_diff

    def snapshot(self) -> dict[str, Any]:
        """Snapshot metrics hiện tại."""
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }


#: Singleton idempotent (lazy — chỉ tạo khi dùng).
_visual_metrics: VisualMetrics | None = None
_metrics_lock = threading.Lock()


def get_visual_metrics() -> VisualMetrics:
    """Lấy singleton VisualMetrics (idempotent)."""
    global _visual_metrics
    if _visual_metrics is None:
        with _metrics_lock:
            if _visual_metrics is None:
                _visual_metrics = VisualMetrics()
    return _visual_metrics
