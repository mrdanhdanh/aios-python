"""EvaluationCollector tests (TASK-022)."""

from datetime import datetime, timezone

from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.observability.evaluation import EvaluationStore, EvaluationVerdict
from aios_core.orchestrator.evaluation_collector import EvaluationCollector


def _emit(bus, type_, execution_id, plan_id="wf:a"):
    bus.publish(Event(type=type_,
                      payload={"execution_id": execution_id, "plan_id": plan_id},
                      timestamp=datetime.now(timezone.utc)))


class FakeEvaluator:
    def __init__(self, quality=0.9, feedback="ok"):
        self.quality = quality
        self.feedback = feedback
        self.calls = []

    def evaluate(self, workflow_id, execution_id, result):
        self.calls.append((workflow_id, execution_id))
        return EvaluationVerdict(quality=self.quality, feedback=self.feedback)


def test_collect_workflow_attaches_quality(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "e.db")
    _emit(bus, EventType.WORKFLOW_STARTED, "e1")
    _emit(bus, EventType.WORKFLOW_COMPLETED, "e1")

    evaluator = FakeEvaluator(0.85, "good")
    collector = EvaluationCollector(store, evaluator)
    collector.collect_workflow("wf:a", "e1", {"result": 1})
    assert evaluator.calls == [("wf:a", "e1")]
    rows = store.list()
    assert rows[0].quality == 0.85
    assert rows[0].feedback == "good"
    store.close()


def test_collect_workflow_without_evaluator_noop(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "e.db")
    collector = EvaluationCollector(store, evaluator=None)
    collector.collect_workflow("wf:a", "e1", {})  # không crash, không đổi gì
    rows = store.list()
    assert rows == []
    store.close()


def test_evaluator_error_swallowed(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "e.db")

    class BoomEvaluator:
        def evaluate(self, workflow_id, execution_id, result):
            raise RuntimeError("evaluator boom")

    collector = EvaluationCollector(store, BoomEvaluator())
    collector.collect_workflow("wf:a", "e1", {})  # không crash (P1-4 v1)
    store.close()


def test_keyerror_missing_row_swallowed(tmp_path):
    """Store chưa có row (restart giữa chừng) → KeyError bị nuốt (P1-4 v1)."""
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "e.db")
    collector = EvaluationCollector(store, FakeEvaluator())
    collector.collect_workflow("wf:a", "ghost-execution", {})  # không crash
    store.close()


def test_collect_all_aggregate(tmp_path):
    bus = EventBus()
    store = EvaluationStore(bus, tmp_path / "e.db")
    t0 = datetime.now(timezone.utc)
    bus.publish(Event(type=EventType.WORKFLOW_STARTED,
                      payload={"execution_id": "e1", "plan_id": "wf:a"}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_COMPLETED,
                      payload={"execution_id": "e1", "plan_id": "wf:a"}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_STARTED,
                      payload={"execution_id": "e2", "plan_id": "wf:a"}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_FAILED,
                      payload={"execution_id": "e2", "plan_id": "wf:a"}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_STARTED,
                      payload={"execution_id": "e3", "plan_id": "wf:b"}, timestamp=t0))
    bus.publish(Event(type=EventType.WORKFLOW_COMPLETED,
                      payload={"execution_id": "e3", "plan_id": "wf:b"}, timestamp=t0))
    store.evaluate("e1", 0.7, "")

    collector = EvaluationCollector(store)
    agg = collector.collect_all()
    assert agg["wf:a"] == {"count": 2, "success": 1, "failed": 1, "avg_quality": 0.7}
    assert agg["wf:b"] == {"count": 1, "success": 1, "failed": 0, "avg_quality": None}
    assert list(agg.keys()) == ["wf:a", "wf:b"]  # deterministic sort
    store.close()
