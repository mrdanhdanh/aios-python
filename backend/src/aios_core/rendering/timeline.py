"""RenderTimeline — record ordered input events (M11-P1, TASK-079)."""

from __future__ import annotations

from .contracts import InputEvent


class RenderTimeline:
    """Record input events theo thứ tự + timestamp tăng dần."""

    def __init__(self) -> None:
        self._events: list[InputEvent] = []

    def record(self, type: str, timestamp: float, payload: dict | None = None) -> InputEvent:
        """Thêm event — timestamp phải tăng dần (fail-closed: raise nếu không)."""
        if self._events and timestamp < self._events[-1].timestamp:
            raise ValueError(
                f"timestamp không tăng dần: {timestamp} < "
                f"{self._events[-1].timestamp}"
            )
        event = InputEvent(
            type=type,
            timestamp=timestamp,
            payload=payload or {},
        )
        self._events.append(event)
        return event

    @property
    def events(self) -> list[InputEvent]:
        return list(self._events)

    @property
    def is_empty(self) -> bool:
        return not self._events

    def __len__(self) -> int:
        return len(self._events)

    def state_hash(self, frame_index: int, fps: float) -> str:
        """Hash trạng thái tại frame_index — từ các event đã xảy ra tới
        thời điểm frame (t = frame_index / fps). Deterministic."""
        import hashlib

        t_frame = frame_index / fps
        applied = [e for e in self._events if e.timestamp <= t_frame * 1000.0]
        h = hashlib.sha256()
        for e in applied:
            h.update(e.type.encode("utf-8"))
            h.update(repr(e.timestamp).encode("utf-8"))
            h.update(repr(sorted(e.payload.items())).encode("utf-8"))
        return h.hexdigest()
