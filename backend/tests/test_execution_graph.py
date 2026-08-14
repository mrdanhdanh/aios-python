"""TASK-027 — Execution Graph tests (M5-P10): contracts, state machine,
converter, executor (order/join/policies/cancel/retries), INV-015, wiring."""

from __future__ import annotations

import threading

import pytest
from pydantic import ValidationError

from aios_core.config import GraphSettings
from aios_core.kernel.execution_plan import (
    ExecutionPlan,
    ExecutionPlanBuilder,
    ExecutionPlanStatus,
    PlanNode,
    PlanNodeType,
)
from aios_core.kernel.graph import (
    Condition,
    Dependency,
    ExecutionGraph,
    FailurePolicy,
    GraphEdge,
    GraphExecutor,
    GraphNode,
    GraphNodeStatus,
    GraphResult,
    GraphRunStatus,
    JoinPolicy,
    plan_to_graph,
    validate_graph_acyclic,
)
from aios_core.kernel.graph.errors import GraphExecutionError, GraphValidationError
from aios_core.kernel.graph.state_machine import TRANSITIONS, GraphStateMachine
from aios_core.kernel.services import StateService

STATUSES = list(GraphNodeStatus)


def node(nid: str, *deps: str, join: JoinPolicy = JoinPolicy.ALL,
         retries: int = 0, **kwargs) -> GraphNode:
    return GraphNode(
        id=nid, type=PlanNodeType.TASK, name=nid,
        depends_on=[Dependency(node_id=d) for d in deps],
        join_policy=join, retries=retries, **kwargs)


def graph(gid: str, nodes: list[GraphNode],
          policy: FailurePolicy = FailurePolicy.FAIL_FAST) -> ExecutionGraph:
    return ExecutionGraph(id=gid, nodes=nodes, failure_policy=policy)


def make_executor(max_parallel: int = 1) -> GraphExecutor:
    return GraphExecutor(StateService(), GraphSettings(max_parallel=max_parallel))


def plan3() -> ExecutionPlan:
    return ExecutionPlan(
        id="plan:t",
        request_ref="r",
        nodes=[
            PlanNode(id="A", type=PlanNodeType.TASK, name="a"),
            PlanNode(id="B", type=PlanNodeType.TASK, name="b", depends_on=["A"]),
            PlanNode(id="C", type=PlanNodeType.TASK, name="c", depends_on=["B"]),
        ],
        estimated_cost=0.0, estimated_tokens=600,
        required_permissions=["filesystem"],
        status=ExecutionPlanStatus.READY, created_at="",
    )


# ---------------------------------------------------------------------------
# YC-1 — Contracts
# ---------------------------------------------------------------------------

class TestContracts:
    def test_8_statuses(self):
        assert {s.value for s in GraphNodeStatus} == {
            "pending", "ready", "running", "succeeded",
            "failed", "skipped", "cancelled", "blocked"}

    def test_extra_forbid(self):
        with pytest.raises(ValidationError):
            GraphNode(id="A", type=PlanNodeType.TASK, bogus=1)
        with pytest.raises(ValidationError):
            GraphResult(status=GraphRunStatus.SUCCEEDED, execution_id="x",
                        failure_policy=FailurePolicy.FAIL_FAST, bogus=1)

    def test_negative_timeout_rejected(self):
        with pytest.raises(ValidationError):
            node("A", timeout_s=-1)

    def test_self_dep_rejected(self):
        with pytest.raises(ValidationError):
            node("A", "A")

    def test_duplicate_dep_rejected(self):
        with pytest.raises(ValidationError):
            GraphNode(id="B", type=PlanNodeType.TASK,
                      depends_on=[Dependency(node_id="A"), Dependency(node_id="A")])

    def test_empty_graph_rejected(self):
        with pytest.raises(ValidationError):
            ExecutionGraph(id="g", nodes=[])

    def test_edges_derived_plan16(self):
        g = graph("g", [
            node("analyze"),
            node("test_backend", "analyze"),
            node("test_frontend", "analyze"),
            node("report", "test_backend", "test_frontend"),
        ])
        edges = g.edges
        assert sorted((e.from_id, e.to_id) for e in edges) == [
            ("analyze", "test_backend"), ("analyze", "test_frontend"),
            ("test_backend", "report"), ("test_frontend", "report")]

    def test_cycle_build_gate(self):
        # C2-07: bypass per-node via model_construct, then validate full graph.
        cyc = [GraphNode.model_construct(id=nid, type=PlanNodeType.TASK,
                                         depends_on=[Dependency(node_id=dep)])
               for nid, dep in (("A", "C"), ("B", "A"), ("C", "B"))]
        with pytest.raises(ValidationError):
            ExecutionGraph.model_validate({"id": "g", "nodes": [
                c.model_dump() for c in cyc]})


# ---------------------------------------------------------------------------
# YC-2 — Errors
# ---------------------------------------------------------------------------

class TestErrors:
    def test_hierarchy(self):
        assert issubclass(GraphValidationError, Exception)
        assert issubclass(GraphExecutionError, Exception)


# ---------------------------------------------------------------------------
# YC-3 — State machine
# ---------------------------------------------------------------------------

class TestStateMachine:
    def test_can_transition_table(self):
        for current in STATUSES:
            for target in STATUSES:
                expected = target in TRANSITIONS[current]
                assert GraphStateMachine.can_transition(current, target) == expected

    def test_terminal(self):
        for status in STATUSES:
            assert GraphStateMachine.is_terminal(status) == (
                status in (GraphNodeStatus.SUCCEEDED, GraphNodeStatus.FAILED,
                           GraphNodeStatus.SKIPPED, GraphNodeStatus.BLOCKED,
                           GraphNodeStatus.CANCELLED))

    def test_is_ready_root(self):
        assert GraphStateMachine.is_ready(node("A"), {})

    def test_is_ready_all(self):
        n = node("D", "A", "B")
        assert not GraphStateMachine.is_ready(n, {"A": GraphNodeStatus.SUCCEEDED,
                                                  "B": GraphNodeStatus.PENDING})
        assert GraphStateMachine.is_ready(n, {"A": GraphNodeStatus.SUCCEEDED,
                                              "B": GraphNodeStatus.SUCCEEDED})

    def test_is_ready_any(self):
        n = node("D", "A", "B", join=JoinPolicy.ANY)
        assert GraphStateMachine.is_ready(n, {"A": GraphNodeStatus.SUCCEEDED,
                                              "B": GraphNodeStatus.FAILED})
        assert not GraphStateMachine.is_ready(n, {"A": GraphNodeStatus.FAILED,
                                                  "B": GraphNodeStatus.PENDING})

    def test_dead_end_priority(self):
        assert GraphStateMachine.dead_end_status(
            {"A": GraphNodeStatus.CANCELLED}) is GraphNodeStatus.BLOCKED
        assert GraphStateMachine.dead_end_status(
            {"A": GraphNodeStatus.BLOCKED}) is GraphNodeStatus.BLOCKED
        assert GraphStateMachine.dead_end_status(
            {"A": GraphNodeStatus.FAILED}) is GraphNodeStatus.SKIPPED
        assert GraphStateMachine.dead_end_status(
            {"A": GraphNodeStatus.SKIPPED}) is GraphNodeStatus.SKIPPED
        # priority: BLOCKED beats FAILED
        assert GraphStateMachine.dead_end_status(
            {"A": GraphNodeStatus.FAILED, "B": GraphNodeStatus.BLOCKED}
        ) is GraphNodeStatus.BLOCKED

    def test_graph_outcome(self):
        ok = {n: GraphNodeStatus.SUCCEEDED for n in ("A", "B")}
        assert GraphStateMachine.graph_outcome(ok, False) is GraphRunStatus.SUCCEEDED
        skipped = dict(ok); skipped["C"] = GraphNodeStatus.SKIPPED
        assert GraphStateMachine.graph_outcome(skipped, False) is GraphRunStatus.SUCCEEDED
        failed = dict(ok); failed["C"] = GraphNodeStatus.FAILED
        assert GraphStateMachine.graph_outcome(failed, False) is GraphRunStatus.FAILED
        blocked = dict(ok); blocked["C"] = GraphNodeStatus.BLOCKED
        assert GraphStateMachine.graph_outcome(blocked, False) is GraphRunStatus.FAILED
        assert GraphStateMachine.graph_outcome(ok, True) is GraphRunStatus.CANCELLED


# ---------------------------------------------------------------------------
# YC-4 — Converter
# ---------------------------------------------------------------------------

class TestConverter:
    def test_chain_convert(self):
        g = plan_to_graph(plan3())
        assert [n.id for n in g.nodes] == ["A", "B", "C"]
        assert [n.depends_on[0].node_id for n in g.nodes[1:]] == ["A", "B"]
        assert g.id == "plan:t"
        assert g.metadata["required_permissions"] == ["filesystem"]
        assert g.metadata["estimated_tokens"] == 600
        assert g.failure_policy is FailurePolicy.FAIL_FAST

    def test_failure_policy_override(self):
        g = plan_to_graph(plan3(), failure_policy=FailurePolicy.CONTINUE)
        assert g.failure_policy is FailurePolicy.CONTINUE

    def test_plan16_shape(self):
        plan = ExecutionPlan(
            id="p", request_ref="", nodes=[
                PlanNode(id="analyze", type=PlanNodeType.LLM, name="a"),
                PlanNode(id="test_backend", type=PlanNodeType.TASK, name="b",
                         depends_on=["analyze"]),
                PlanNode(id="test_frontend", type=PlanNodeType.TASK, name="c",
                         depends_on=["analyze"]),
                PlanNode(id="report", type=PlanNodeType.TASK, name="d",
                         depends_on=["test_backend", "test_frontend"]),
            ], estimated_cost=0.0, estimated_tokens=1000,
            status=ExecutionPlanStatus.READY, created_at="")
        g = plan_to_graph(plan)
        assert len(g.edges) == 4
        assert all(n.join_policy is JoinPolicy.ALL for n in g.nodes)

    def test_cyclic_plan_rejected(self):
        plan = ExecutionPlan.model_construct(
            id="p", request_ref="", nodes=[
                {"id": "A", "type": "task", "name": "a", "agent": "",
                 "capabilities": [], "depends_on": ["C"], "timeout_s": 300.0, "retries": 0},
                {"id": "B", "type": "task", "name": "b", "agent": "",
                 "capabilities": [], "depends_on": ["A"], "timeout_s": 300.0, "retries": 0},
                {"id": "C", "type": "task", "name": "c", "agent": "",
                 "capabilities": [], "depends_on": ["B"], "timeout_s": 300.0, "retries": 0},
            ], estimated_cost=0, estimated_tokens=0, required_permissions=[],
            required_resources={}, status=ExecutionPlanStatus.DRAFT, created_at="")
        with pytest.raises(GraphValidationError):
            plan_to_graph(plan)

    def test_deterministic(self):
        assert plan_to_graph(plan3()).model_dump() == plan_to_graph(plan3()).model_dump()


# ---------------------------------------------------------------------------
# YC-5 — Executor
# ---------------------------------------------------------------------------

class TestExecutor:
    def test_chain_order(self):
        ex = make_executor()
        g = graph("g", [node("A"), node("B", "A"), node("C", "B")])
        calls = []
        r = ex.execute(g, lambda n, ctx: calls.append(n.id) or n.id)
        assert r.execution_order == ["A", "B", "C"]
        assert r.status is GraphRunStatus.SUCCEEDED
        assert all(s is GraphNodeStatus.SUCCEEDED for s in r.node_statuses.values())

    def test_join_all_plan23(self):
        ex = make_executor()
        g = graph("g", [node("A"), node("B", "A"), node("C", "A"),
                        node("D", "B", "C")])
        r = ex.execute(g, lambda n, ctx: n.id)
        assert r.execution_order == ["A", "B", "C", "D"]
        assert r.max_concurrent_running == 1

    def test_ready_persist(self):
        ex = make_executor(max_parallel=1)
        g = graph("g", [node("A"), node("B", "A"), node("C", "A")])
        seen_ready: list[str] = []

        def runner(n, ctx):
            if n.id == "B":
                state = ex._state.get_state("graph:g")
                seen_ready.append(state["nodes"]["C"])  # C should be READY (persisted)
            return n.id

        ex.execute(g, runner)
        assert seen_ready == [GraphNodeStatus.READY.value]

    def test_parallelism_barrier(self):
        ex = make_executor(max_parallel=2)
        g = graph("g", [node("A"), node("B", "A"), node("C", "A")])
        started = threading.Event()
        release = threading.Event()
        order: list[str] = []

        def runner(n, ctx):
            if n.id in ("B", "C"):
                order.append(n.id)
                if n.id == "B":
                    started.set()
                    assert release.wait(timeout=5)  # C2-10: timeout guard
                else:
                    started.wait(timeout=5)
            return n.id

        r = ex.execute(g, runner)
        release.set()
        assert r.max_concurrent_running == 2
        assert r.execution_order == ["A", "B", "C"]  # submit order (deterministic)

    def test_max_concurrent_bound(self):
        ex = make_executor(max_parallel=2)
        g = graph("g", [node("A"), node("B"), node("C")])  # 3 roots
        r = ex.execute(g, lambda n, ctx: n.id)
        assert r.max_concurrent_running == 2  # min(3 ready, max 2) — C2-11

    def test_fail_fast(self):
        ex = make_executor()
        g = graph("g", [node("A"), node("B", "A"), node("C", "B")])

        def runner(n, ctx):
            if n.id == "A":
                raise RuntimeError("boom A")
            return n.id

        r = ex.execute(g, runner)
        assert r.status is GraphRunStatus.FAILED
        assert r.execution_order == ["A"]
        assert r.node_statuses["B"] is GraphNodeStatus.BLOCKED
        assert r.node_statuses["C"] is GraphNodeStatus.BLOCKED
        assert "boom A" in r.reason

    def test_continue(self):
        """CONTINUE: failed dep -> dependents SKIPPED; independent branch runs."""
        ex = make_executor()
        # A fails; B/C depend on A (SKIPPED); E independent (runs).
        g = graph("g", [node("A"), node("B", "A"), node("C", "A"), node("E")],
                  policy=FailurePolicy.CONTINUE)

        def runner(n, ctx):
            if n.id == "A":
                raise RuntimeError("A fails")
            return n.id

        r = ex.execute(g, runner)
        assert r.status is GraphRunStatus.FAILED  # parity: any FAILED → FAILED
        assert r.node_statuses["A"] is GraphNodeStatus.FAILED
        assert r.node_statuses["B"] is GraphNodeStatus.SKIPPED
        assert r.node_statuses["C"] is GraphNodeStatus.SKIPPED
        assert r.node_statuses["E"] is GraphNodeStatus.SUCCEEDED  # independent branch
        assert r.node_results["E"] == "E"  # partial results kept

    def test_skip_dependents(self):
        ex = make_executor()
        g = graph("g", [node("A"), node("B", "A"), node("C", "A"),
                        node("D", "B", "C")], policy=FailurePolicy.SKIP_DEPENDENTS)

        def runner(n, ctx):
            if n.id == "A":
                raise RuntimeError("A fails")
            return n.id

        r = ex.execute(g, runner)
        assert r.node_statuses["B"] is GraphNodeStatus.SKIPPED  # transitive
        assert r.node_statuses["C"] is GraphNodeStatus.SKIPPED
        assert r.node_statuses["D"] is GraphNodeStatus.SKIPPED
        assert r.execution_order == ["A"]

    def test_join_any(self):
        ex = make_executor()
        g = graph("g", [
            node("A"), node("B"),
            node("D", "A", "B", join=JoinPolicy.ANY),
        ], policy=FailurePolicy.CONTINUE)

        def runner(n, ctx):
            if n.id == "A":
                raise RuntimeError("A fails")
            return n.id

        r = ex.execute(g, runner)
        assert r.node_statuses["D"] is GraphNodeStatus.SUCCEEDED  # >=1 dep ok
        assert r.execution_order == ["A", "B", "D"]

    def test_retries_success(self):
        ex = make_executor()
        g = graph("g", [node("A", retries=2)])
        attempts = {"n": 0}

        def runner(n, ctx):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise RuntimeError("flaky")
            return "ok"

        r = ex.execute(g, runner)
        assert r.node_statuses["A"] is GraphNodeStatus.SUCCEEDED
        assert attempts["n"] == 3

    def test_retries_exhausted(self):
        ex = make_executor()
        g = graph("g", [node("A", retries=2)])
        r = ex.execute(g, lambda n, ctx: (_ for _ in ()).throw(RuntimeError("always")))
        assert r.node_statuses["A"] is GraphNodeStatus.FAILED
        assert "always" in r.node_reasons["A"]

    def test_cancel_queued(self):
        """C2-02 v2: queued nodes never run after cancel."""
        ex = make_executor(max_parallel=2)
        g = graph("g", [node("A"), node("B", "A"), node("C", "A"), node("D", "A")])
        b_started = threading.Event()
        release = threading.Event()
        calls: list[str] = []

        def runner(n, ctx):
            calls.append(n.id)
            if n.id == "B":
                b_started.set()
                release.wait(timeout=5)
            return n.id

        def execute_in_thread():
            return ex.execute(g, runner)

        t = threading.Thread(target=execute_in_thread)
        t.start()
        b_started.wait(timeout=5)
        ex.cancel("graph:g")
        release.set()
        t.join(timeout=10)
        r = ex.last_result if hasattr(ex, "last_result") else None
        # Re-fetch: execute returns inside thread; grab via a holder.
        holder = {}

        def execute_in_thread2():
            holder["r"] = ex.execute(g, runner)

        # Simpler: run fresh with pre-set cancel mid-flight via a second call.
        ex2 = make_executor(max_parallel=2)
        calls2: list[str] = []

        def runner2(n, ctx):
            calls2.append(n.id)
            if n.id == "B":
                b_started.set()
                release.wait(timeout=5)
            return n.id

        def exec2():
            holder["r"] = ex2.execute(graph("g2", [node("A"), node("B", "A"),
                                                   node("C", "A"), node("D", "A")]),
                                      runner2)

        t2 = threading.Thread(target=exec2)
        t2.start()
        b_started.wait(timeout=5)
        ex2.cancel("graph:g2")
        release.set()
        t2.join(timeout=10)
        r2 = holder["r"]
        assert "D" not in calls2  # queued node never ran
        assert r2.status is GraphRunStatus.CANCELLED
        assert r2.node_statuses["D"] is GraphNodeStatus.CANCELLED

    def test_cancel_before_execute(self):
        ex = make_executor()
        g = graph("g", [node("A")])
        ex.cancel("graph:g")
        r = ex.execute(g, lambda n, ctx: n.id)
        assert r.status is GraphRunStatus.CANCELLED
        assert r.execution_order == []  # R3-6: nothing ran; no state written

    def test_cancel_idempotent(self):
        ex = make_executor()
        ex.cancel("x")
        ex.cancel("x")
        assert ex._is_cancelled("x")

    def test_state_persist_namespace(self):
        ex = make_executor()
        g = graph("g", [node("A")])
        ex.execute(g, lambda n, ctx: "r1")
        state = ex._state.get_state("graph:g")  # default namespace C2-05 v2
        assert state is not None
        assert state["nodes"]["A"] == "succeeded"
        assert ex._state.get_state("g") is None
        assert state["metrics"]["max_concurrent_running"] == 1

    def test_condition_fail_loud(self):
        ex = make_executor()
        g = ExecutionGraph(id="g", nodes=[
            GraphNode(id="B", type=PlanNodeType.TASK,
                      depends_on=[Dependency(node_id="A", condition=Condition(expression="x > 1"))]),
            GraphNode(id="A", type=PlanNodeType.TASK),
        ])
        with pytest.raises(GraphValidationError, match="conditions not supported"):
            ex.execute(g, lambda n, ctx: n.id)

    def test_no_progress_guard(self):
        """C2-04 v2: stuck READY node -> GraphExecutionError."""
        from unittest.mock import patch

        ex = make_executor()
        g = graph("g", [node("A"), node("B", "A")])

        class NoopPool:
            def __init__(self, *a, **k):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def submit(self, *a, **k):
                class _F:
                    def result(self):
                        pass
                return _F()

        with patch("aios_core.kernel.graph.executor.ThreadPoolExecutor", NoopPool):
            # Node A stays READY forever (submit is a no-op) → no progress.
            with pytest.raises(GraphExecutionError, match="cannot make progress"):
                ex.execute(g, lambda n, ctx: n.id)

    def test_init_validation_bogus_policy(self):
        with pytest.raises(GraphValidationError):
            GraphExecutor(StateService(), "bogus-policy")

    def test_deterministic(self):
        ex = make_executor()
        g = graph("g", [node("A"), node("B", "A"), node("C", "A"), node("D", "B", "C")])
        r1 = ex.execute(g, lambda n, ctx: n.id)
        r2 = ex.execute(g, lambda n, ctx: n.id)
        d1 = r1.model_dump(); d2 = r2.model_dump()
        d1.pop("latency_ms"); d2.pop("latency_ms")
        assert d1 == d2


# ---------------------------------------------------------------------------
# YC-7 — Integration (plan → convert → execute) + PLAN §23
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_plan_to_execute(self):
        ex = make_executor()
        g = plan_to_graph(plan3())
        calls = []
        r = ex.execute(g, lambda n, ctx: calls.append(n.id) or n.id)
        assert calls == ["A", "B", "C"]
        assert r.status is GraphRunStatus.SUCCEEDED

    def test_plan23_chain(self):
        """PLAN §23: A→B→C verify execution order."""
        ex = make_executor()
        r = ex.execute(graph("g", [node("A"), node("B", "A"), node("C", "B")]),
                       lambda n, ctx: n.id)
        assert r.execution_order == ["A", "B", "C"]

    def test_plan23_fork_join(self):
        """PLAN §23: A→B, A→C, B/C→D verify execution order."""
        ex = make_executor()
        r = ex.execute(graph("g", [node("A"), node("B", "A"), node("C", "A"),
                                   node("D", "B", "C")]), lambda n, ctx: n.id)
        assert r.execution_order == ["A", "B", "C", "D"]


# ---------------------------------------------------------------------------
# INV-015 behavioral
# ---------------------------------------------------------------------------

def test_inv015_acyclicity():
    with pytest.raises(ValidationError):
        ExecutionGraph(id="g", nodes=[
            GraphNode(id="A", type=PlanNodeType.TASK, depends_on=[Dependency(node_id="B")]),
            GraphNode(id="B", type=PlanNodeType.TASK, depends_on=[Dependency(node_id="A")]),
        ])
    # helper exposed
    validate_graph_acyclic([node("A"), node("B", "A")])
