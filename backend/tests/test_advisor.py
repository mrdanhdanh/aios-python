"""ImprovementAdvisor tests (TASK-022) — 5 rules + edge cases."""

from datetime import datetime, timedelta, timezone

from aios_core.kernel.events import Event, EventBus, EventType
from aios_core.observability.evaluation import EvaluationStore
from aios_core.observability.metrics import MetricsService
from aios_core.observability.prompt_history import PromptHistory
from aios_core.orchestrator.advisor import ImprovementAdvisor


def make_env(tmp_path):
    bus = EventBus()
    evals = EvaluationStore(bus, tmp_path / "e.db")
    metrics = MetricsService(bus, tmp_path / "m.db")
    prompts = PromptHistory(tmp_path / "p.db")
    advisor = ImprovementAdvisor(evals, metrics, prompts)
    return bus, evals, metrics, prompts, advisor


def _eval(bus, execution_id, workflow_id, ts, success=True, quality=None):
    bus.publish(Event(type=EventType.WORKFLOW_STARTED,
                      payload={"execution_id": execution_id, "plan_id": workflow_id}, timestamp=ts))
    fin = EventType.WORKFLOW_COMPLETED if success else EventType.WORKFLOW_FAILED
    bus.publish(Event(type=fin,
                      payload={"execution_id": execution_id, "plan_id": workflow_id},
                      timestamp=ts + timedelta(seconds=1)))


def test_empty_no_suggestions(tmp_path):
    _, _, _, _, advisor = make_env(tmp_path)
    assert advisor.suggest() == []


def test_rule_low_quality(tmp_path):
    bus, evals, _, _, advisor = make_env(tmp_path)
    t0 = datetime.now(timezone.utc)
    _eval(bus, "e1", "wf:a", t0, quality=0.3)
    _eval(bus, "e2", "wf:a", t0, quality=0.2)
    evals.evaluate("e1", 0.3)
    evals.evaluate("e2", 0.2)
    suggestions = advisor.suggest()
    assert any(s.kind == "workflow" and s.action == "improve" and s.target == "wf:a"
               for s in suggestions)


def test_rule_low_quality_ignores_none(tmp_path):
    """Quality None (auto-record không evaluator) → không fire (P1-5 v1)."""
    bus, evals, _, _, advisor = make_env(tmp_path)
    t0 = datetime.now(timezone.utc)
    _eval(bus, "e1", "wf:a", t0)  # quality None
    _eval(bus, "e2", "wf:a", t0)
    suggestions = advisor.suggest()
    assert all(not (s.kind == "workflow" and s.action == "improve") for s in suggestions)


def test_rule_many_failures(tmp_path):
    bus, _, _, _, advisor = make_env(tmp_path)
    t0 = datetime.now(timezone.utc)
    for i in range(3):
        _eval(bus, f"e{i}", "wf:b", t0, success=False)
    _eval(bus, "ok1", "wf:b", t0, success=True)
    suggestions = advisor.suggest()
    assert any(s.kind == "workflow" and s.action == "review" and s.target == "wf:b"
               for s in suggestions)


def test_rule_tool_failures(tmp_path):
    bus, _, metrics, _, advisor = make_env(tmp_path)
    t0 = datetime.now(timezone.utc)
    for i in range(3):
        bus.publish(Event(type=EventType.TOOL_STARTED,
                          payload={"execution_id": f"e{i}", "node_id": f"n{i}", "node_name": f"run{i}"},
                          timestamp=t0))
        bus.publish(Event(type=EventType.TOOL_FINISHED,
                          payload={"execution_id": f"e{i}", "node_id": f"n{i}", "node_name": f"run{i}", "ok": False},
                          timestamp=t0 + timedelta(seconds=1)))
    assert metrics.tool_failures() == 3
    suggestions = advisor.suggest()
    assert any(s.kind == "capability" and s.action == "review" and s.target == ""
               for s in suggestions)


def test_rule_unreviewed_prompts(tmp_path):
    _, _, _, prompts, advisor = make_env(tmp_path)
    for _ in range(3):
        prompts.record("p1", "1.0.0", {"x": 1}, "out")
    prompts.record("p2", "1.0.0", {"x": 1}, "out")
    suggestions = advisor.suggest()
    assert any(s.kind == "prompt" and s.action == "review" and s.target == "p1"
               for s in suggestions)
    assert all(not (s.kind == "prompt" and s.target == "p2") for s in suggestions)


def test_rule_slow_workflows(tmp_path):
    bus, _, _, _, advisor = make_env(tmp_path)
    t0 = datetime.now(timezone.utc)
    for i in range(3):
        bus.publish(Event(type=EventType.WORKFLOW_STARTED,
                          payload={"execution_id": f"slow{i}", "plan_id": "wf:slow"}, timestamp=t0))
        bus.publish(Event(type=EventType.WORKFLOW_COMPLETED,
                          payload={"execution_id": f"slow{i}", "plan_id": "wf:slow"},
                          timestamp=t0 + timedelta(seconds=12)))
    suggestions = advisor.suggest()
    assert any(s.kind == "workflow" and s.action == "improve" and s.target == "wf:slow"
               and "duration" in s.reason for s in suggestions)


def test_dedup_and_sort(tmp_path):
    bus, evals, _, _, advisor = make_env(tmp_path)
    t0 = datetime.now(timezone.utc)
    # 2 lần chạy cùng dữ liệu → dedup
    for _ in range(2):
        _eval(bus, "e1", "wf:a", t0, quality=0.4)
        evals.evaluate("e1", 0.4)
    suggestions = advisor.suggest()
    kinds = [(s.kind, s.action, s.target) for s in suggestions]
    assert len(kinds) == len(set(kinds))
    assert kinds == sorted(kinds)
