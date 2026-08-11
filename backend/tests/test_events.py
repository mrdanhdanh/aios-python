"""Event service tests: publish + audit."""

import pytest

from aios_core.kernel import EventType
from aios_core.kernel.events import EventBus
from aios_core.kernel.services import EventService


@pytest.fixture
def bus():
    return EventBus()


def test_emit_publishes_to_subscribers(bus, tmp_path):
    svc = EventService(bus, tmp_path / "audit.db")
    received = []
    bus.subscribe(EventType.TOOL_STARTED, lambda ev: received.append(ev))
    event = svc.emit(EventType.TOOL_STARTED, {"t": 1}, source="test")
    assert len(received) == 1
    assert received[0].type == EventType.TOOL_STARTED
    assert event.id == received[0].id
    assert event.source == "test"


def test_audit_row_written(bus, tmp_path):
    db_path = tmp_path / "audit.db"
    svc = EventService(bus, db_path)
    svc.emit(EventType.WORKFLOW_STARTED, {"wf": "x"}, source="s1")
    events = svc.query_audit()
    assert len(events) == 1
    assert events[0].type == EventType.WORKFLOW_STARTED
    assert events[0].payload == {"wf": "x"}
    assert events[0].source == "s1"


def test_query_audit_filter_and_limit(bus, tmp_path):
    svc = EventService(bus, tmp_path / "audit.db")
    for i in range(5):
        svc.emit(EventType.TOOL_STARTED, {"i": i})
    svc.emit(EventType.AGENT_STARTED, {"a": 1})
    filtered = svc.query_audit(event_type=EventType.TOOL_STARTED)
    assert len(filtered) == 5
    limited = svc.query_audit(limit=2)
    assert len(limited) == 2
    # DESC by timestamp: newest first → last emitted AGENT_STARTED on top
    assert limited[0].type == EventType.AGENT_STARTED


def test_audit_insert_error_does_not_crash_emit(bus, tmp_path):
    # db_path pointing at an existing directory → sqlite3.connect raises OperationalError
    existing_dir = tmp_path / "adir"
    existing_dir.mkdir()
    svc = EventService(bus, existing_dir / "sub" / "audit.db")  # parent missing → mkdir, then connect fails
    # Emit must not crash even though audit fails.
    received = []
    bus.subscribe(EventType.ERROR_OCCURRED, lambda ev: received.append(ev))
    svc.emit(EventType.ERROR_OCCURRED, {"e": 1})
    assert len(received) == 1  # event still published


def test_query_audit_db_missing_returns_empty(bus, tmp_path):
    svc = EventService(bus, tmp_path / "audit.db")
    assert svc.query_audit() == []


def test_db_path_mkdir_parents(bus, tmp_path):
    nested = tmp_path / "a" / "b" / "audit.db"
    svc = EventService(bus, nested)
    assert nested.is_file()
    svc.emit(EventType.AGENT_STARTED)
    assert len(svc.query_audit()) == 1
