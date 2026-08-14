"""TASK-028 — Parallel Scheduler tests (M5-P10): resource gating, queue,
timeout, cancel, metrics, ExecutionServiceRunner, INV-016, PLAN §23."""

from __future__ import annotations

import threading

import pytest
from pydantic import ValidationError

from aios_core.config import GraphSettings, ResourcesSettings, SchedulerSettings
from aios_core.kernel.execution_plan import (
    ExecutionPlan,
    ExecutionPlanStatus,
    PlanNode,
    PlanNodeType,
)
from aios_core.kernel.graph import (
    ExecutionGraph,
    FailurePolicy,
    GraphExecutor,
    GraphNode,
    plan_to_graph,
)
from aios_core.kernel.scheduler import (
    ExecutionNodeError,
    ExecutionServiceRunner,
    GraphScheduler,
    NodeResourceMetrics,
    ResourceUnavailableError,
    ScheduledGraphResult,
    SchedulerError,
)
from aios_core.kernel.scheduler.execution_runner import _noop_runner
from aios_core.kernel.services import ResourceService, StateService


def gnode(nid: str, *deps: str, retries: int = 0) -> GraphNode:
    return GraphNode(id=nid, type=PlanNodeType.TASK, name=nid,
                     depends_on=[{"node_id": d} for d in deps], retries=retries)


def make_scheduler(
    max_concurrent: int | None = None,
    max_parallel: int = 1,
    timeout: float | None = None,
) -> GraphScheduler:
    state = StateService()
    return GraphScheduler(
        resource_service=ResourceService(
            ResourcesSettings(max_concurrent=max_concurrent)),
        state_service=state,
        executor=GraphExecutor(state, GraphSettings(max_parallel=max_parallel)),
        settings=SchedulerSettings(resource_wait_timeout_s=timeout),
        graph_settings=GraphSettings(max_parallel=max_parallel),
    )


def plan3() -> ExecutionPlan:
    return ExecutionPlan(
        id="plan:t", request_ref="r",
        nodes=[
            PlanNode(id="A", type=PlanNodeType.TASK, name="a"),
            PlanNode(id="B", type=PlanNodeType.TASK, name="b", depends_on=["A"]),
            PlanNode(id="C", type=PlanNodeType.TASK, name="c", depends_on=["B"]),
        ],
        estimated_cost=0.0, estimated_tokens=600,
        status=ExecutionPlanStatus.READY, created_at="")


# ---------------------------------------------------------------------------
# YC-1 — Contracts
# ---------------------------------------------------------------------------

class TestContracts:
    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            NodeResourceMetrics(bogus=1)
        with pytest.raises(ValidationError):
            ScheduledGraphResult(execution_id="x", graph=None, bogus=1)

    def test_defaults(self):
        m = NodeResourceMetrics()
        assert m.resource_wait_ms == 0 and m.slots_acquired == 0


# ---------------------------------------------------------------------------
# YC-2 — Errors
# ---------------------------------------------------------------------------

class TestErrors:
    def test_hierarchy(self):
        assert issubclass(ResourceUnavailableError, SchedulerError)
        assert issubclass(ExecutionNodeError, SchedulerError)


# ---------------------------------------------------------------------------
# YC-3 — GraphScheduler
# ---------------------------------------------------------------------------

class TestScheduler:
    def test_single_slot_serial(self):
        s = make_scheduler(max_concurrent=1)
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B", "A"), gnode("C", "B")])
        r = s.schedule(g, lambda n, ctx: n.id)
        assert r.graph.execution_order == ["A", "B", "C"]
        assert r.graph.status.value == "succeeded"
        assert r.peak_slots_used == 1

    def test_parallel_bounded(self):
        s = make_scheduler(max_concurrent=2, max_parallel=3)
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B", "A"),
                                          gnode("C", "A"), gnode("D", "A")])
        active = 0
        peak_active = 0
        lock = threading.Lock()

        def runner(n, ctx):
            nonlocal active, peak_active
            with lock:
                active += 1
                peak_active = max(peak_active, active)
            time.sleep(0.01)
            with lock:
                active -= 1
            return n.id

        import time
        r = s.schedule(g, runner)
        assert r.graph.execution_order == ["A", "B", "C", "D"]
        assert peak_active <= 2  # bounded by resource
        assert r.peak_slots_used == 2
        assert r.graph.status.value == "succeeded"

    def test_queue_observability(self):
        s = make_scheduler(max_concurrent=1, max_parallel=2)
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B")])  # same-wave, 1 slot
        a_started = threading.Event()
        release = threading.Event()
        import time as _t

        def runner(n, ctx):
            if n.id == "A":
                a_started.set()
                release.wait(timeout=5)  # holds the slot -> B waits
            return n.id

        def run():
            return s.schedule(g, runner)

        t = threading.Thread(target=run)
        t.start()
        a_started.wait(timeout=5)
        seen_pending = False
        for _ in range(40):  # poll — B's acquire may lag thread scheduling
            if s._resources.pending() >= 1:
                seen_pending = True
                break
            _t.sleep(0.05)
        release.set()
        t.join(timeout=10)
        assert seen_pending
        assert s._resources.pending() == 0

    def test_timeout_fail(self):
        s = make_scheduler(max_concurrent=1, max_parallel=3, timeout=0.1)
        g = ExecutionGraph(id="g", nodes=[gnode("X"), gnode("Y"), gnode("Z")])
        x_started = threading.Event()
        release = threading.Event()
        holder = {}

        def runner(n, ctx):
            if n.id == "X":
                x_started.set()
                release.wait(timeout=10)  # holds the slot
            return n.id

        def run2():
            holder["r"] = s.schedule(ExecutionGraph(id="g2", nodes=[
                gnode("X"), gnode("Y"), gnode("Z")]), runner)

        import time as _t
        t2 = threading.Thread(target=run2)
        t2.start()
        x_started.wait(timeout=5)
        _t.sleep(0.3)  # Y/Z time out while X holds the slot
        release.set()
        t2.join(timeout=10)
        r2 = holder["r"]
        assert r2.graph.status.value == "failed"
        assert r2.graph.node_statuses["Y"].value == "failed"
        assert "timeout" in r2.graph.node_reasons.get("Y", "")
        assert s._resources.stats()["running"] == 0
        assert s._resources.pending() == 0

    def test_runner_raise_releases_slot(self):
        s = make_scheduler(max_concurrent=1)
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B", "A")])

        def runner(n, ctx):
            if n.id == "A":
                raise RuntimeError("boom")
            return n.id

        r = s.schedule(g, runner)
        assert r.graph.status.value == "failed"
        assert s._resources.stats()["running"] == 0

    def test_cancel_while_waiting(self):
        """C2-04 v2: retries>=1 -> CANCELLED; X holds slot, Y waits."""
        s = make_scheduler(max_concurrent=1, timeout=0.1)
        g = ExecutionGraph(id="g", nodes=[gnode("X"), gnode("Y", retries=2)])
        x_started = threading.Event()
        release = threading.Event()
        holder = {}

        def runner(n, ctx):
            if n.id == "X":
                x_started.set()
                release.wait(timeout=10)
            return n.id

        def run():
            holder["r"] = s.schedule(g, runner)

        t = threading.Thread(target=run)
        t.start()
        x_started.wait(timeout=5)
        s.cancel("graph:g")
        release.set()
        t.join(timeout=15)
        r = holder["r"]
        assert r.graph.status.value == "cancelled"
        assert r.graph.node_statuses["Y"].value == "cancelled"
        assert s._resources.pending() == 0

    def test_metrics(self):
        s = make_scheduler(max_concurrent=1)
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B", "A")])
        r = s.schedule(g, lambda n, ctx: n.id)
        assert r.queue_time_ms == max(
            m.resource_wait_ms for m in r.node_metrics.values())
        assert r.resource_stats.get("max_concurrent") == 1
        assert r.node_metrics["A"].slots_acquired == 1

    def test_retries_acquire_twice(self):
        """P3-08: retries=1 -> slots_acquired == 2."""
        s = make_scheduler(max_concurrent=1)
        g = ExecutionGraph(id="g", nodes=[gnode("A", retries=1)])
        attempts = {"n": 0}

        def runner(n, ctx):
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise RuntimeError("flaky")
            return "ok"

        r = s.schedule(g, runner)
        assert r.graph.node_statuses["A"].value == "succeeded"
        assert r.node_metrics["A"].slots_acquired == 2

    def test_schedule_plan_resolves_policy(self):
        """C2-01 v2: failure_policy=None -> graph_settings.default_failure_policy."""
        s = make_scheduler()
        s._graph_settings = GraphSettings(default_failure_policy="continue")
        plan = plan3()
        r = s.schedule_plan(plan, lambda n, ctx: n.id)
        assert r.graph.failure_policy is FailurePolicy.CONTINUE

    def test_schedule_plan_override(self):
        s = make_scheduler()
        r = s.schedule_plan(plan3(), lambda n, ctx: n.id,
                            failure_policy=FailurePolicy.CONTINUE)
        assert r.graph.failure_policy is FailurePolicy.CONTINUE

    def test_deterministic(self):
        s1 = make_scheduler(max_concurrent=1)
        s2 = make_scheduler(max_concurrent=1)  # fresh instances (P3-04)
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B", "A"), gnode("C", "A")])
        r1 = s1.schedule(g, lambda n, ctx: n.id)
        r2 = s2.schedule(g, lambda n, ctx: n.id)
        d1 = r1.model_dump(); d2 = r2.model_dump()
        for d in (d1, d2):
            d.pop("queue_time_ms")
            d["graph"].pop("latency_ms")  # timing thật — không deterministic
            for m in d["node_metrics"].values():
                m.pop("resource_wait_ms")
        assert d1 == d2


# ---------------------------------------------------------------------------
# YC-4 — ExecutionServiceRunner
# ---------------------------------------------------------------------------

class FakeExecutionService:
    """Spy on the public API only (INV-016)."""

    def __init__(self, fail: bool = False, result: str = "r"):
        from aios_core.kernel.services import ExecutionResult, ExecutionStatus

        self.calls = []
        self.fail = fail
        self.result = result
        self._ok = ExecutionResult(ExecutionStatus.COMPLETED, "x", node_results={})
        self._bad = ExecutionResult(ExecutionStatus.FAILED, "x", reason="node boom")

    def execute(self, plan, runner):
        from aios_core.kernel.services import ExecutionResult, ExecutionStatus

        self.calls.append(plan)
        if self.fail:
            return self._bad
        node = plan.nodes[0]
        result = runner[node.id](node, {})  # run inner like ExecutionService
        return ExecutionResult(ExecutionStatus.COMPLETED, plan.id,
                               node_results={node.id: result})


class TestExecutionRunner:
    def test_one_node_plan(self):
        fake = FakeExecutionService()
        runner = ExecutionServiceRunner(fake, permissions=["filesystem"], tokens=10)
        out = runner(gnode("N1", retries=2), {})
        assert fake.calls[0].id == "gnode:N1"
        assert [n.id for n in fake.calls[0].nodes] == ["N1"]
        assert fake.calls[0].nodes[0].retries == 2
        assert fake.calls[0].required_permissions == ["filesystem"]
        assert fake.calls[0].estimated_tokens == 10
        assert out is None  # noop inner -> None result

    def test_failed_raises(self):
        fake = FakeExecutionService(fail=True)
        runner = ExecutionServiceRunner(fake)
        with pytest.raises(ExecutionNodeError, match="node boom"):
            runner(gnode("N1"), {})

    def test_inner_called(self):
        fake = FakeExecutionService()
        seen = {}

        def inner(node, results):
            seen["id"] = node.id
            return "inner-result"

        runner = ExecutionServiceRunner(fake, inner=inner)
        out = runner(gnode("N1"), {})
        assert seen["id"] == "N1"
        assert out == "inner-result"

    def test_noop_inner(self):
        fake = FakeExecutionService()
        runner = ExecutionServiceRunner(fake)
        assert _noop_runner is not None
        out = runner(gnode("N1"), {})
        assert out is None  # noop inner -> None


# ---------------------------------------------------------------------------
# C1-01 (critique-1) — adapter + finite max_concurrent limitation test
# ---------------------------------------------------------------------------

class TestAdapterLimitation:
    def test_double_slot_failed(self, tmp_path):
        """C1-01 (a): adapter + max_concurrent=1 -> inner ExecutionService
        acquire_slot() non-blocking fails -> node FAILED 'resource unavailable'."""
        from aios_core.kernel.events import EventBus
        from aios_core.kernel.services import (
            EventService,
            ExecutionService,
            PolicyService,
        )

        state = StateService()
        resources = ResourceService(ResourcesSettings(max_concurrent=1))
        bus = EventBus()
        execution = ExecutionService(
            event_service=EventService(bus, str(tmp_path / "audit.db")),
            policy_service=PolicyService(bus),
            state_service=state, resource_service=resources)
        s = GraphScheduler(resource_service=resources, state_service=state,
                           executor=GraphExecutor(state),
                           graph_settings=GraphSettings())
        plan = ExecutionPlan(
            id="p", request_ref="", nodes=[
                PlanNode(id="A", type=PlanNodeType.TASK, name="a"),
                PlanNode(id="B", type=PlanNodeType.TASK, name="b", depends_on=["A"]),
            ], estimated_cost=0.0, estimated_tokens=400,
            status=ExecutionPlanStatus.READY, created_at="")
        g = plan_to_graph(plan)
        r = s.schedule(g, ExecutionServiceRunner(execution))
        assert r.graph.status.value == "failed"
        assert "resource unavailable" in r.graph.reason
        assert resources.stats()["running"] == 0
        assert resources.pending() == 0


# ---------------------------------------------------------------------------
# YC-6 — Integration (PLAN §23)
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_plan23_a_to_b_to_c_via_scheduler(self):
        s = make_scheduler(max_concurrent=1)
        r = s.schedule_plan(plan3(), lambda n, ctx: n.id)
        assert r.graph.execution_order == ["A", "B", "C"]
        assert r.graph.status.value == "succeeded"

    def test_plan23_fork_join_via_scheduler(self):
        s = make_scheduler(max_concurrent=2, max_parallel=3)
        plan = ExecutionPlan(
            id="p", request_ref="", nodes=[
                PlanNode(id="A", type=PlanNodeType.TASK, name="a"),
                PlanNode(id="B", type=PlanNodeType.TASK, name="b", depends_on=["A"]),
                PlanNode(id="C", type=PlanNodeType.TASK, name="c", depends_on=["A"]),
                PlanNode(id="D", type=PlanNodeType.TASK, name="d",
                         depends_on=["B", "C"]),
            ], estimated_cost=0.0, estimated_tokens=800,
            status=ExecutionPlanStatus.READY, created_at="")
        r = s.schedule_plan(plan, lambda n, ctx: n.id)
        assert r.graph.execution_order == ["A", "B", "C", "D"]
        assert r.peak_slots_used <= 2

    def test_inv016_chain_spy(self):
        """INV-016 behavioral: acquire/release interleaving deterministic."""
        from aios_core.kernel.services import ResourceService as RS

        calls = []

        class SpyResource(RS):
            def acquire_slot_wait(self, timeout=None):
                calls.append("acquire")
                return super().acquire_slot_wait(timeout=timeout)

            def release_slot(self):
                calls.append("release")
                super().release_slot()

        state = StateService()
        resources = SpyResource(ResourcesSettings(max_concurrent=1))
        s = GraphScheduler(resource_service=resources, state_service=state,
                           executor=GraphExecutor(state))
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B", "A")])
        s.schedule(g, lambda n, ctx: n.id)
        assert calls == ["acquire", "release", "acquire", "release"]

    def test_duck_typed_stub(self):
        """INV-016: GraphScheduler chạy với stub chỉ implement public API."""

        class StubResource:
            def __init__(self):
                self._slots = 1
                self._held = 0
                self._lock = threading.Lock()

            def acquire_slot_wait(self, timeout=None):
                with self._lock:
                    if self._held < self._slots:
                        self._held += 1
                        return True
                return False

            def release_slot(self):
                with self._lock:
                    self._held -= 1

            def stats(self):
                return {"running": self._held, "max_concurrent": self._slots}

            def pending(self):
                return 0

        state = StateService()
        s = GraphScheduler(resource_service=StubResource(), state_service=state,
                           executor=GraphExecutor(state))
        g = ExecutionGraph(id="g", nodes=[gnode("A"), gnode("B", "A")])
        r = s.schedule(g, lambda n, ctx: n.id)
        assert r.graph.status.value == "succeeded"
