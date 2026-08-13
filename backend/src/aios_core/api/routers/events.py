"""Events router — GET audit history + WS realtime (C1-04 pattern)."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect

from ...kernel import EventType
from ...kernel.events import Subscription

router = APIRouter(tags=["events"])


@router.get("/events")
def list_events(request: Request, limit: int = 100, type: str | None = None) -> dict:
    event_service = request.app.state.registries["event_service"]
    event_type = None
    if type is not None:
        try:
            event_type = EventType(type)
        except ValueError:
            return _error("invalid_event_type", f"unknown event type: {type!r}")
    events = event_service.query_audit(limit=limit, event_type=event_type)
    return {"data": [_event_dict(e) for e in events]}


@router.websocket("/events/ws")
async def events_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    bus = websocket.app.state.kernel.bus
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue(maxsize=500)  # C2-05 backpressure

    def _forward(event) -> None:
        # Sync handler called from publisher thread — call_soon_threadsafe wakes
        # the WS loop's queue.get (C1-04).
        try:
            loop.call_soon_threadsafe(queue.put_nowait, _event_dict(event))
        except Exception:  # noqa: BLE001 — queue full/dropped
            pass

    sub: Subscription = bus.subscribe(None, _forward)
    try:
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                continue
            await websocket.send_json(item)
    except WebSocketDisconnect:
        pass
    finally:
        sub.unsubscribe()  # C2-05: no subscriber leak


def _event_dict(event) -> dict:
    return {
        "id": event.id,
        "type": event.type.value,
        "timestamp": event.timestamp.isoformat(),
        "source": event.source,
        "payload": event.payload,
    }


def _error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}
