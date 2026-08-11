"""Event bus tests: sync, filter, error isolation, async, concurrency."""

import asyncio
import threading

import pytest

from aios_core.kernel.events import Event, EventBus, EventType


def _event(event_type=EventType.TOOL_STARTED, payload=None):
    return Event(type=event_type, payload=payload or {}, source="test")


def test_publish_sync_handler():
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe(None, lambda ev: received.append(ev))
    ev = _event(payload={"x": 1})
    bus.publish(ev)
    assert received == [ev]


def test_filter_by_type():
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe(EventType.AGENT_STARTED, lambda ev: received.append(ev))
    bus.publish(_event(EventType.TOOL_STARTED))
    bus.publish(_event(EventType.AGENT_STARTED))
    assert len(received) == 1
    assert received[0].type == EventType.AGENT_STARTED


def test_subscribe_none_receives_all():
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe(None, lambda ev: received.append(ev))
    bus.publish(_event(EventType.AGENT_STARTED))
    bus.publish(_event(EventType.TOOL_STARTED))
    assert len(received) == 2


def test_unsubscribe():
    bus = EventBus()
    received: list[Event] = []
    sub = bus.subscribe(None, lambda ev: received.append(ev))
    bus.publish(_event())
    sub.unsubscribe()
    bus.publish(_event())
    assert len(received) == 1


def test_unsubscribe_twice_noop():
    bus = EventBus()
    received: list[Event] = []
    sub = bus.subscribe(None, lambda ev: received.append(ev))
    sub.unsubscribe()
    sub.unsubscribe()  # no-op
    bus.publish(_event())
    assert received == []


def test_same_handler_twice_called_twice():
    bus = EventBus()
    count = 0

    def handler(ev):
        nonlocal count
        count += 1

    bus.subscribe(None, handler)
    bus.subscribe(None, handler)
    bus.publish(_event())
    assert count == 2


def test_handler_order_is_subscribe_order():
    bus = EventBus()
    order: list[str] = []
    bus.subscribe(None, lambda ev: order.append("first"))
    bus.subscribe(None, lambda ev: order.append("second"))
    bus.publish(_event())
    assert order == ["first", "second"]


def test_sync_handler_error_isolation():
    bus = EventBus()
    received: list[Event] = []

    def bad(ev):
        raise RuntimeError("boom")

    bus.subscribe(None, bad)
    bus.subscribe(None, lambda ev: received.append(ev))
    bus.publish(_event())  # must not crash
    assert len(received) == 1


def test_async_handler_in_loop():
    async def scenario():
        bus = EventBus()
        received: list[Event] = []

        async def handler(ev):
            await asyncio.sleep(0.01)
            received.append(ev.payload)

        bus.subscribe(EventType.TOOL_STARTED, handler)
        bus.publish(_event(payload={"v": 42}))
        await bus.flush()
        assert received == [{"v": 42}]

    asyncio.run(scenario())


def test_async_handler_error_logged_not_crashed(caplog):
    async def scenario():
        bus = EventBus()

        async def bad(ev):
            raise RuntimeError("async boom")

        received: list[Event] = []

        bus.subscribe(None, bad)
        bus.subscribe(None, lambda ev: received.append(ev))
        bus.publish(_event())
        await bus.flush()  # must not re-raise
        assert len(received) == 1

    asyncio.run(scenario())
    assert "async boom" in caplog.text


def test_async_handler_from_sync_thread():
    bus = EventBus()
    done = threading.Event()
    result: dict = {}

    async def handler(ev):
        result["payload"] = ev.payload

    bus.subscribe(None, handler)
    bus.publish(_event(payload={"from": "thread"}))
    # Wait for the daemon thread to complete the handler.
    deadline = threading.Event()
    def poll():
        while not done.is_set() and not deadline.wait(0.05):
            pass
    # Simple bounded wait: poll up to 2s for the result.
    for _ in range(40):
        if "payload" in result:
            break
        threading.Event().wait(0.05)
    assert result.get("payload") == {"from": "thread"}


def test_concurrent_publish_two_threads():
    bus = EventBus()
    count = 0
    lock = threading.Lock()

    def handler(ev):
        nonlocal count
        with lock:
            count += 1

    bus.subscribe(None, handler)
    errors: list[Exception] = []

    def worker():
        try:
            for _ in range(50):
                bus.publish(_event())
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert count == 100


def test_unsubscribe_inside_handler():
    bus = EventBus()
    received: list[Event] = []

    def first(ev):
        received.append(ev)

    def unsubscriber(ev):
        sub.unsubscribe()  # unsubscribe during publish

    sub = bus.subscribe(None, unsubscriber)
    bus.subscribe(None, first)
    bus.publish(_event())
    bus.publish(_event())
    assert len(received) == 2  # first handler unaffected, still subscribed


def test_event_to_dict():
    ev = _event(payload={"a": 1}, )
    d = ev.to_dict()
    assert d["type"] == "tool.started"
    assert d["payload"] == {"a": 1}
    assert "timestamp" in d
    assert "id" in d
