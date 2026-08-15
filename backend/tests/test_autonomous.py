"""Autonomous layer tests (M9 — TASK-050..062).

Batch 1: TASK-050 Goal Engine · TASK-051 Planner · TASK-052 World Model ·
TASK-053 Loop · TASK-054 Governor. Các batch sau bổ sung vào cuối file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from aios_core.autonomous import (
    AutonomyBudget,
    AutonomyDecision,
    AutonomyGovernor,
    AutonomyLevel,
    AutonomousGoalEngine,
    AutonomousLoop,
    AutonomousPlanner,
    GoalConstraints,
    GoalContract,
    GoalLifecycleError,
    GoalLifecycleState,
    LoopFinalState,
    RiskClass,
    UsageSnapshot,
    VerificationResult,
    WorldModel,
    WorldScope,
    new_goal_id,
)

# ---------------------------------------------------------------------------
# TASK-050 — Autonomous Goal Engine
# ---------------------------------------------------------------------------

def _goal(**kw) -> GoalContract:
    base = dict(
        id=new_goal_id(),
        objective="fix authentication module",
        success={"test_pass": 0.9},
        permissions=["edit", "test"],
        autonomy=AutonomyLevel.A2_GOAL,
        steps=["analyze", "fix", "test"],
    )
    base.update(kw)
    return GoalContract(**base)


@pytest.fixture()
def engine(tmp_path: Path):
    return AutonomousGoalEngine(event_service=None, db_path=tmp_path / "autonomous.db")


def test_g050_lifecycle_chain(engine):
    g = engine.propose(_goal())
    assert engine.get_state(g.id) == GoalLifecycleState.PROPOSED
    engine.validate(g.id)
    engine.approve(g.id)
    engine.plan(g.id)
    engine.execute(g.id)
    engine.evaluate(g.id)
    engine.complete(g.id)
    assert engine.get_state(g.id) == GoalLifecycleState.COMPLETED


def test_g050_recovery_chain(engine):
    g = engine.propose(_goal())
    engine.validate(g.id)
    engine.approve(g.id)
    engine.plan(g.id)
    engine.execute(g.id)
    engine.block(g.id)
    assert engine.get_state(g.id) == GoalLifecycleState.BLOCKED
    engine.recover(g.id)
    engine.replan(g.id)
    engine.execute(g.id)
    assert engine.get_state(g.id) == GoalLifecycleState.EXECUTING


def test_g050_escalate_terminal(engine):
    g = engine.propose(_goal())
    engine.validate(g.id)
    engine.approve(g.id)
    engine.plan(g.id)
    engine.execute(g.id)
    engine.escalate(g.id, "needs human")
    assert engine.get_state(g.id) == GoalLifecycleState.ESCALATED
    with pytest.raises(GoalLifecycleError):
        engine.transition(g.id, GoalLifecycleState.EXECUTING)  # terminal


def test_g050_invalid_transition_raises(engine):
    g = engine.propose(_goal())
    with pytest.raises(GoalLifecycleError):
        engine.transition(g.id, GoalLifecycleState.COMPLETED)  # PROPOSED → COMPLETED


def test_g050_persist_reload(tmp_path: Path):
    db = tmp_path / "autonomous.db"
    e1 = AutonomousGoalEngine(event_service=None, db_path=db)
    g = e1.propose(_goal(steps=["a", "b", "c"]))
    e1.validate(g.id)
    e1.approve(g.id)
    e1.plan(g.id)
    e1.execute(g.id)
    e1.mark_step_completed(g.id, "a")
    e2 = AutonomousGoalEngine(event_service=None, db_path=db)  # cross-instance
    reloaded = e2.get(g.id)
    assert reloaded.completed_steps == ["a"]
    assert engine_state(e2, g.id) == GoalLifecycleState.EXECUTING
    assert reloaded.progress() == pytest.approx(1 / 3)


def engine_state(engine, goal_id):
    return engine.get_state(goal_id)


def test_g050_progress_and_steps(engine):
    g = engine.propose(_goal(steps=["a", "b"]))
    engine.validate(g.id)
    engine.approve(g.id)
    engine.plan(g.id)
    engine.execute(g.id)
    engine.mark_step_completed(g.id, "a")
    assert engine.get(g.id).progress() == pytest.approx(0.5)
    with pytest.raises(GoalLifecycleError):
        engine.mark_step_completed(g.id, "unknown")  # step ∉ steps
    with pytest.raises(GoalLifecycleError):
        engine.mark_step_completed(g.id, "a")  # đã hoàn thành


def test_g050_mark_step_state_gate(engine):
    g = engine.propose(_goal(steps=["a"]))
    with pytest.raises(GoalLifecycleError):
        engine.mark_step_completed(g.id, "a")  # PROPOSED — không hợp lệ


def test_g050_history(engine):
    g = engine.propose(_goal())
    engine.validate(g.id)
    hist = engine.get_history(g.id)
    assert hist[-1] == {"state": "validating", "at": hist[-1]["at"], "reason": "validate"}


def test_g050_success_achieved(engine):
    g = engine.propose(_goal(steps=["a"]))
    engine.validate(g.id)
    engine.approve(g.id)
    engine.plan(g.id)
    engine.execute(g.id)
    engine.mark_step_completed(g.id, "a")
    assert engine.success_achieved(g.id)


def test_g050_contract_forbid():
    with pytest.raises(Exception):
        GoalContract(id="x", objective="y", bogus=1)


# ---------------------------------------------------------------------------
# TASK-051 — Autonomous Planner
# ---------------------------------------------------------------------------

@pytest.fixture()
def planner():
    return AutonomousPlanner()


def _goal_for_plan(**kw):
    base = dict(id="g1", objective="fix authentication module and test it")
    base.update(kw)
    return GoalContract(**base)


def test_p051_plan_contract(planner):
    plan = planner.plan(
        _goal_for_plan(success={"coverage": 0.9}),
        capabilities=["python", "filesystem"],
    )
    assert plan.goal_id == "g1"
    assert plan.steps, "steps không rỗng"
    for step in plan.steps:
        assert step.id and step.description and step.capability
        assert step.capability in ("python", "filesystem")
        assert step.dependencies == []
    assert "coverage >= 0.9" in plan.success_conditions
    assert plan.rollback.enabled is True
    assert plan.reasons == []


def test_p051_deterministic(planner):
    g = _goal_for_plan()
    p1 = planner.plan(g, capabilities=["python", "filesystem"])
    p2 = planner.plan(g, capabilities=["python", "filesystem"])
    assert [s.id for s in p1.steps] == [s.id for s in p2.steps]
    assert [s.capability for s in p1.steps] == [s.capability for s in p2.steps]


def test_p051_capabilities_empty_raises(planner):
    with pytest.raises(Exception):
        planner.plan(_goal_for_plan(), capabilities=[])


def test_p051_objective_empty_raises(planner):
    with pytest.raises(Exception):
        planner.plan(_goal_for_plan(objective="  "), capabilities=["python"])


def test_p051_no_keyword_default_step(planner):
    plan = planner.plan(
        _goal_for_plan(objective="improve system stability"),
        capabilities=["python"],
    )
    assert plan.steps[0].id == "default"
    assert plan.steps[0].capability == "python"


def test_p051_filter_capability_fallback(planner):
    plan = planner.plan(
        _goal_for_plan(objective="fix something"),
        capabilities=["docker"],  # fix cần python/filesystem → fallback docker
    )
    assert plan.steps and all(s.capability == "docker" for s in plan.steps)


def test_p051_over_budget(planner):
    g = _goal_for_plan(constraints=GoalConstraints(max_duration_s=10.0))
    plan = planner.plan(g, capabilities=["python", "filesystem"])
    assert plan.over_budget is True


def test_p051_rollback_disabled_on_delete(planner):
    g = _goal_for_plan(permissions=["delete"])
    plan = planner.plan(g, capabilities=["python"])
    assert plan.rollback.enabled is False


def test_p051_replan(planner):
    g = _goal_for_plan()
    p1 = planner.plan(g, capabilities=["python", "filesystem"])
    p2 = planner.replan(g, world=None, plan=p1, reason="world changed",
                        completed_step_ids=["fix"])
    assert p2.reasons == ["world changed"]
    done = [s.id for s in p2.steps if s.completed]
    assert "fix" in done


# ---------------------------------------------------------------------------
# TASK-052 — World Model
# ---------------------------------------------------------------------------

class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture()
def world():
    return WorldModel(clock=FakeClock(), ttl_s=100.0, max_history=3)


def test_w052_observe_and_get(world):
    world.observe(WorldScope.SYSTEM, "status", "ok", source="health")
    fact = world.get_fact(WorldScope.SYSTEM, "status")
    assert fact is not None
    assert fact.value == "ok"
    assert fact.source == "health"
    assert fact.observed_at == 1000.0


def test_w052_freshness_decay(world):
    world.observe(WorldScope.RUNTIME, "cpu", 0.5, source="metric", confidence=1.0)
    assert world.freshness(WorldScope.RUNTIME, "cpu") == pytest.approx(1.0)
    world._clock.now = 1050.0  # 50s / 100s TTL
    assert world.freshness(WorldScope.RUNTIME, "cpu") == pytest.approx(0.5)
    assert world.effective_confidence(WorldScope.RUNTIME, "cpu") == pytest.approx(0.5)
    world._clock.now = 1200.0  # già hơn TTL
    assert world.freshness(WorldScope.RUNTIME, "cpu") == pytest.approx(0.0)


def test_w052_confidence_clamp(world):
    world.observe(WorldScope.SYSTEM, "x", 1, source="s", confidence=1.5)
    assert world.get_fact(WorldScope.SYSTEM, "x").confidence == 1.0
    world.observe(WorldScope.SYSTEM, "y", 1, source="s", confidence=-0.2)
    assert world.get_fact(WorldScope.SYSTEM, "y").confidence == 0.0


def test_w052_scope_key_isolation(world):
    world.observe(WorldScope.SYSTEM, "status", "ok", source="a")
    world.observe(WorldScope.RUNTIME, "status", "busy", source="b")
    assert world.get_fact(WorldScope.SYSTEM, "status").value == "ok"
    assert world.get_fact(WorldScope.RUNTIME, "status").value == "busy"


def test_w052_history_bounded(world):
    for i in range(5):
        world.observe(WorldScope.TASKS, f"t{i}", i, source="loop")
    snap = world.snapshot()
    assert len(snap.history[WorldScope.TASKS.value]) == 3  # max_history


def test_w052_snapshot_groups(world):
    world.observe(WorldScope.SYSTEM, "status", "ok", source="s")
    world.observe(WorldScope.GOALS, "count", 2, source="engine")
    snap = world.snapshot()
    assert snap.system == {"status": "ok"}
    assert snap.goals == {"count": 2}
    assert set(snap.model_dump().keys()) >= {
        "system", "runtime", "goals", "tasks", "environment", "constraints", "history"
    }


def test_w052_latest_wins(world):
    world.observe(WorldScope.SYSTEM, "status", "ok", source="a")
    world._clock.now = 1001.0
    world.observe(WorldScope.SYSTEM, "status", "degraded", source="b")
    assert world.get_fact(WorldScope.SYSTEM, "status").value == "degraded"


# ---------------------------------------------------------------------------
# TASK-054 — Autonomy Governor
# ---------------------------------------------------------------------------

class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture()
def governor():
    return AutonomyGovernor(
        budget=AutonomyBudget(max_steps=10, max_cost=5.0, max_duration_s=100.0,
                              max_tool_calls=20, max_llm_calls=5, max_retries=2,
                              max_parallel_agents=2),
        clock=Clock(),
    )


def test_gov054_continue(governor):
    d = governor.check_action("g1", RiskClass.READ)
    assert d.decision == AutonomyDecision.CONTINUE


def test_gov054_steps_budget(governor):
    governor.start_goal("g1")
    governor.apply_usage("g1", UsageSnapshot(steps=9))
    d = governor.check_action("g1", RiskClass.READ, UsageSnapshot(steps=2))
    assert d.decision == AutonomyDecision.STOP
    assert "budget.steps exceeded" in d.reason


def test_gov054_cost_budget(governor):
    governor.start_goal("g1")
    governor.apply_usage("g1", UsageSnapshot(cost=4.9))
    d = governor.check_action("g1", RiskClass.READ, UsageSnapshot(cost=0.2))
    assert d.decision == AutonomyDecision.STOP
    assert "budget.cost" in d.reason


def test_gov054_duration_budget(governor):
    g = governor
    g._clock.now = 95.0
    governor.start_goal("g1")
    governor._clock.now = 196.0  # 101s > 100s
    d = governor.check_action("g1", RiskClass.READ)
    assert d.decision == AutonomyDecision.STOP
    assert "budget.duration" in d.reason


def test_gov054_tool_llm_retries_budget(governor):
    governor.start_goal("g1")
    governor.apply_usage("g1", UsageSnapshot(tool_calls=20))
    assert governor.check_action("g1", RiskClass.READ).decision == AutonomyDecision.STOP
    governor.end_goal("g1")
    governor.start_goal("g2")
    governor.apply_usage("g2", UsageSnapshot(llm_calls=5))
    assert governor.check_action("g2", RiskClass.READ).decision == AutonomyDecision.STOP
    governor.end_goal("g2")
    governor.start_goal("g3")
    governor.apply_usage("g3", UsageSnapshot(retries=2))
    assert governor.check_action("g3", RiskClass.READ).decision == AutonomyDecision.STOP


def test_gov054_risk_approval(governor):
    d = governor.check_action("g1", RiskClass.COMMIT)
    assert d.decision == AutonomyDecision.ASK_HUMAN


def test_gov054_risk_impossible(governor):
    d = governor.check_action("g1", RiskClass.DELETE)
    assert d.decision == AutonomyDecision.STOP
    assert "impossible" in d.reason


def test_gov054_parallel_pause(governor):
    governor.start_goal("g1")
    governor.apply_usage("g1", UsageSnapshot(parallel_agents=2))
    d = governor.check_action("g1", RiskClass.COMMIT, UsageSnapshot(parallel_agents=1))
    assert d.decision == AutonomyDecision.PAUSE


def test_gov054_end_goal_reset(governor):
    governor.start_goal("g1")
    governor.apply_usage("g1", UsageSnapshot(steps=999))
    assert governor.check_action("g1", RiskClass.READ).decision == AutonomyDecision.STOP
    governor.end_goal("g1")
    assert governor.check_action("g1", RiskClass.READ).decision == AutonomyDecision.CONTINUE


def test_gov054_replan_world_changed(governor):
    g = AutonomyGovernor(clock=Clock(), world_changed=lambda: True)
    d = g.check_action("g1", RiskClass.READ)
    assert d.decision == AutonomyDecision.REPLAN


def test_gov054_usage_snapshot(governor):
    governor.start_goal("g1")
    governor.apply_usage("g1", UsageSnapshot(steps=3, cost=1.5))
    u = governor.usage("g1")
    assert u.steps == 3 and u.cost == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# TASK-053 — Autonomous Loop
# ---------------------------------------------------------------------------

@pytest.fixture()
def loop_goal():
    return GoalContract(
        id="g-loop", objective="fix authentication", steps=["analyze", "fix"],
        permissions=["edit"],
    )


def _loop(governor, world=None, **kw):
    return AutonomousLoop(
        governor=governor,
        world=world or WorldModel(clock=Clock()),
        max_iterations=kw.pop("max_iterations", 10),
        **kw,
    )


def test_loop053_success(loop_goal):
    gov = AutonomyGovernor(clock=Clock())
    calls = {"act": 0, "verify": 0, "learn": 0}

    def act(_plan, _goal, _ctx):
        calls["act"] += 1
        return UsageSnapshot(steps=1)

    def verify(_ctx, _goal):
        calls["verify"] += 1
        return VerificationResult(success=True, score=1.0)

    def learn(_result, _goal):
        calls["learn"] += 1

    loop = _loop(gov, actor=act, verifier=verify, learner=learn)
    result = loop.run_goal(loop_goal)
    assert result.success is True
    assert result.final_state == LoopFinalState.COMPLETED
    assert result.iterations == 1
    assert calls["act"] == 1 and calls["learn"] == 1
    assert result.decisions[0].decision == AutonomyDecision.CONTINUE


def test_loop053_governor_stop_blocks_act(loop_goal):
    gov = AutonomyGovernor(
        budget=AutonomyBudget(max_steps=0), clock=Clock()
    )
    acted = []

    def act(_plan, _goal, _ctx):
        acted.append(True)
        return UsageSnapshot()

    loop = _loop(gov, actor=act)
    result = loop.run_goal(loop_goal)
    assert result.final_state == LoopFinalState.STOPPED
    assert acted == []  # INV-030: STOP → không Act


def test_loop053_ask_human(loop_goal):
    gov = AutonomyGovernor(clock=Clock())
    loop = _loop(gov)
    result = loop.run_goal(loop_goal, step_risk=RiskClass.COMMIT)
    assert result.final_state == LoopFinalState.AWAITING_HUMAN
    assert result.decisions[-1].decision == AutonomyDecision.ASK_HUMAN


def test_loop053_budget_exceeded(loop_goal):
    gov = AutonomyGovernor(
        budget=AutonomyBudget(max_steps=100), clock=Clock()
    )
    calls = {"verify": 0}

    def verify(_ctx, _goal):
        calls["verify"] += 1
        return VerificationResult(success=False, score=0.0)

    loop = _loop(gov, verifier=verify, max_iterations=3)
    result = loop.run_goal(loop_goal)
    assert result.final_state == LoopFinalState.BUDGET_EXCEEDED
    assert result.iterations == 3


def test_loop053_policy_deny(loop_goal):
    gov = AutonomyGovernor(clock=Clock())
    acted = []

    def policy(_cap, _risk):
        return False

    def act(_plan, _goal, _ctx):
        acted.append(True)
        return UsageSnapshot()

    loop = _loop(gov, policy_check=policy, actor=act)
    result = loop.run_goal(loop_goal)
    assert result.final_state == LoopFinalState.STOPPED
    assert acted == []


def test_loop053_order_and_events(loop_goal):
    gov = AutonomyGovernor(clock=Clock())
    order: list[str] = []
    loop = AutonomousLoop(
        governor=gov,
        world=WorldModel(clock=Clock()),
        observer=lambda: order.append("observe") or {},
        understander=lambda _c, _g: order.append("understand") or {},
        actor=lambda _p, _g, _c: order.append("act") or UsageSnapshot(),
        verifier=lambda _c, _g: order.append("verify") or VerificationResult(success=True),
        learner=lambda _r, _g: order.append("learn"),
        max_iterations=5,
    )
    loop.run_goal(loop_goal)
    assert order == ["observe", "understand", "act", "verify", "learn"]


def test_loop053_goal_progress_complete(loop_goal):
    """Loop dừng sớm khi goal progress đạt 1.0 (steps hoàn thành)."""
    gov = AutonomyGovernor(clock=Clock())
    loop = _loop(gov)
    # verifier mặc định success=True → vòng 1 xong
    result = loop.run_goal(loop_goal)
    assert result.success is True


# ---------------------------------------------------------------------------
# TASK-055 — Autonomous Recovery
# ---------------------------------------------------------------------------

from aios_core.autonomous import AutonomousRecovery, CircuitBreaker, RecoveryOutcome, RecoveryStrategy
from aios_core.autonomous.contracts import FailureEvent, STRATEGY_SCORES
from aios_core.autonomous.recovery import fingerprint_of


class RClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture()
def failure():
    return FailureEvent(execution_id="exec-1", error_type="TimeoutError", message="model timeout")


def test_rec055_fingerprint_deterministic():
    a = fingerprint_of("TimeoutError", "model timeout")
    b = fingerprint_of("TimeoutError", "model timeout")
    c = fingerprint_of("TimeoutError", "other")
    assert a == b
    assert a != c
    assert len(a) == 16


def test_rec055_retry_then_success(failure):
    calls = []

    def execute(strategy, _f):
        calls.append(strategy)

    rec = AutonomousRecovery(execute_strategy=execute)
    outcome = rec.recover(failure)
    assert outcome.recovered is True
    assert outcome.strategy == RecoveryStrategy.RETRY
    assert calls == [RecoveryStrategy.RETRY]


def test_rec055_verify_fail_chain(failure):
    calls = []

    def execute(strategy, _f):
        calls.append(strategy)

    rec = AutonomousRecovery(
        execute_strategy=execute,
        verifier=lambda: False,  # verify luôn fail
        max_attempts=2,
    )
    outcome = rec.recover(failure)
    assert outcome.recovered is False
    assert outcome.escalated is True
    assert outcome.attempts == 2
    assert calls == [RecoveryStrategy.RETRY, RecoveryStrategy.FALLBACK]


def test_rec055_policy_deny(failure):
    calls = []

    def execute(strategy, _f):
        calls.append(strategy)

    rec = AutonomousRecovery(
        execute_strategy=execute,
        policy_check=lambda s: s != RecoveryStrategy.RETRY,  # deny retry
    )
    outcome = rec.recover(failure)
    assert outcome.strategy == RecoveryStrategy.FALLBACK
    assert RecoveryStrategy.RETRY not in calls


def test_rec055_circuit_breaker_open(failure):
    rec = AutonomousRecovery(verifier=lambda: False, max_attempts=5)
    # 3 lần fail liên tiếp → circuit OPEN
    for _ in range(3):
        outcome = rec.recover(failure)
        if outcome.escalated:
            break
    assert rec._breaker.is_open(fingerprint_of("TimeoutError", "model timeout"))
    outcome = rec.recover(failure)
    assert outcome.escalated is True
    assert "circuit open" in outcome.reason


def test_rec055_circuit_cooldown(failure):
    clock = RClock()
    breaker = CircuitBreaker(fail_threshold=2, cooldown_s=10.0, clock=clock)
    rec = AutonomousRecovery(breaker=breaker, verifier=lambda: False, max_attempts=5)
    rec.recover(failure)
    rec.recover(failure)
    assert breaker.is_open(fingerprint_of("TimeoutError", "model timeout"))
    clock.now = 11.0  # hết cooldown
    assert breaker.is_open(fingerprint_of("TimeoutError", "model timeout")) is False


def test_rec055_no_strategy_repeat(failure):
    calls = []

    def execute(strategy, _f):
        calls.append(strategy)

    rec = AutonomousRecovery(execute_strategy=execute, verifier=lambda: False, max_attempts=10)
    rec.recover(failure)
    # Lần 2: RETRY đã thử → không lặp vô ích
    rec.recover(failure)
    # Lần 2 sẽ thử FALLBACK → ALTERNATIVE (tried-set per fingerprint)
    assert calls.count(RecoveryStrategy.RETRY) == 1


def test_rec055_strategy_scores():
    assert STRATEGY_SCORES[RecoveryStrategy.RETRY] == 1.0
    assert STRATEGY_SCORES[RecoveryStrategy.ESCALATE] == 0.0
    assert STRATEGY_SCORES[RecoveryStrategy.RETRY] > STRATEGY_SCORES[RecoveryStrategy.FALLBACK]


# ---------------------------------------------------------------------------
# TASK-056 — Long-Horizon Execution
# ---------------------------------------------------------------------------

from aios_core.autonomous import LongHorizonManager
from aios_core.autonomous.contracts import SessionStatus


@pytest.fixture()
def long_horizon(tmp_path: Path):
    return LongHorizonManager(event_service=None, db_path=tmp_path / "longhorizon.db")


def test_lh056_session_create_resume(long_horizon):
    s = long_horizon.create_session(goal_id="g1")
    assert s.status == SessionStatus.ACTIVE
    ckpt = long_horizon.checkpoint(
        s.id, completed=["a", "b"], current="c", pending=["d", "e"],
        state={"step": 3}, notes=["note1"],
    )
    assert ckpt.completed == ["a", "b"]
    resumed = long_horizon.resume(s.id)
    assert resumed.completed == ["a", "b"]
    assert resumed.current == "c"
    assert resumed.pending == ["d", "e"]
    assert resumed.state == {"step": 3}
    assert resumed.notes == ["note1"]


def test_lh056_checkpoint_overwrite(long_horizon):
    s = long_horizon.create_session()
    long_horizon.checkpoint(s.id, completed=["a"], current="b")
    long_horizon.checkpoint(s.id, completed=["a", "b"], current="c")
    resumed = long_horizon.resume(s.id)
    assert resumed.completed == ["a", "b"]
    assert resumed.current == "c"


def test_lh056_cross_instance(tmp_path: Path):
    db = tmp_path / "longhorizon.db"
    m1 = LongHorizonManager(event_service=None, db_path=db)
    s = m1.create_session(goal_id="g1")
    m1.checkpoint(s.id, completed=["a", "b", "c"], current="d")
    m2 = LongHorizonManager(event_service=None, db_path=db)  # restart
    resumed = m2.resume(s.id)
    assert resumed.completed == ["a", "b", "c"]
    assert resumed.current == "d"
    assert m2.get_session(s.id).status == SessionStatus.RESUMED


def test_lh056_terminal_no_resume(long_horizon):
    s = long_horizon.create_session()
    long_horizon.complete_session(s.id)
    with pytest.raises(Exception):
        long_horizon.resume(s.id)
    with pytest.raises(Exception):
        long_horizon.checkpoint(s.id, completed=["a"])


def test_lh056_overlap_raises(long_horizon):
    s = long_horizon.create_session()
    with pytest.raises(Exception):
        long_horizon.checkpoint(s.id, completed=["a"], pending=["a"])


def test_lh056_compact_note(long_horizon):
    s = long_horizon.create_session()
    long_horizon.checkpoint(s.id, completed=["a"], current="b", pending=["c"])
    long_horizon.compact_note(s.id, "compact: context summary")
    resumed = long_horizon.resume(s.id)
    assert resumed.notes == ["compact: context summary"]
    assert resumed.completed == ["a"]  # giữ nguyên progress


def test_lh056_history_bounded(long_horizon):
    s = long_horizon.create_session()
    for i in range(60):
        long_horizon.checkpoint(s.id, completed=[f"s{i}"])
    assert len(long_horizon.checkpoint_history(s.id)) == 50


def test_lh056_list_sessions(long_horizon):
    long_horizon.create_session(goal_id="g1")
    long_horizon.create_session(goal_id="g1")
    long_horizon.create_session(goal_id="g2")
    assert len(long_horizon.list_sessions(goal_id="g1")) == 2
    assert len(long_horizon.list_sessions()) == 3


# ---------------------------------------------------------------------------
# TASK-057 — Autonomous Memory
# ---------------------------------------------------------------------------

from aios_core.autonomous import AutonomousMemory
from aios_core.autonomous.contracts import MemoryEntryKind


@pytest.fixture()
def auto_memory(tmp_path: Path):
    return AutonomousMemory(event_service=None, db_path=tmp_path / "autonomous_memory.db")


def test_mem057_six_kinds():
    assert len(MemoryEntryKind) == 6


def test_mem057_store_retrieve(auto_memory):
    auto_memory.store(MemoryEntryKind.FAILURE, "k1", {"when": "x"}, confidence=0.8)
    entry = auto_memory.retrieve(MemoryEntryKind.FAILURE, "k1")
    assert entry is not None
    assert entry.confidence == 0.8
    assert entry.validated is False


def test_mem057_retrieve_by_kind(auto_memory):
    auto_memory.store(MemoryEntryKind.WORKING, "a", {"v": 1})
    auto_memory.store(MemoryEntryKind.WORKING, "b", {"v": 2})
    entries = auto_memory.retrieve(MemoryEntryKind.WORKING)
    assert len(entries) == 2


def test_mem057_inv034_promote_unvalidated_raises(auto_memory):
    auto_memory.store(MemoryEntryKind.SEMANTIC, "lesson1", {"v": 1}, confidence=0.9)
    with pytest.raises(Exception) as exc:
        auto_memory.promote(MemoryEntryKind.SEMANTIC, "lesson1")
    assert "INV-034" in str(exc.value)


def test_mem057_inv034_promote_low_confidence(auto_memory):
    auto_memory.store(MemoryEntryKind.SEMANTIC, "lesson1", {"v": 1}, confidence=0.2)
    auto_memory.validate("lesson1", MemoryEntryKind.SEMANTIC, 0.2, "evaluation")
    with pytest.raises(Exception) as exc:
        auto_memory.promote(MemoryEntryKind.SEMANTIC, "lesson1")
    assert "confidence" in str(exc.value)


def test_mem057_validate_then_promote(auto_memory):
    auto_memory.store(MemoryEntryKind.SEMANTIC, "lesson1", {"v": 1}, confidence=0.8)
    auto_memory.validate("lesson1", MemoryEntryKind.SEMANTIC, 0.9, "evaluation")
    promoted = auto_memory.promote(MemoryEntryKind.SEMANTIC, "lesson1")
    assert promoted.promoted is True
    assert promoted.validated is True


def test_mem057_validate_requires_source(auto_memory):
    auto_memory.store(MemoryEntryKind.SEMANTIC, "x", {"v": 1}, confidence=0.9)
    with pytest.raises(Exception):
        auto_memory.validate("x", MemoryEntryKind.SEMANTIC, 0.9, "  ")


def test_mem057_learn_full(auto_memory):
    lesson = auto_memory.learn({
        "when": "Oracle migration",
        "failure": "TIMESTAMP mismatch",
        "cause": "timezone",
        "fix": "FROM_TZ(...)",
        "confidence": 0.92,
    })
    assert lesson.key.startswith("lesson:")
    entry = auto_memory.retrieve(MemoryEntryKind.FAILURE, lesson.key)
    assert entry is not None
    assert entry.confidence == 0.92


def test_mem057_learn_incomplete_low_confidence(auto_memory):
    lesson = auto_memory.learn({"when": "x", "failure": "y"})
    entry = auto_memory.retrieve(MemoryEntryKind.FAILURE, lesson.key)
    assert entry.confidence == 0.3  # C1-03 v1


def test_mem057_learn_dedup_increases_confidence(auto_memory):
    data = {"when": "w", "failure": "f", "cause": "c", "fix": "x", "confidence": 0.5}
    lesson1 = auto_memory.learn(data)
    auto_memory.learn(data)
    entry = auto_memory.retrieve(MemoryEntryKind.FAILURE, lesson1.key)
    assert entry.confidence == pytest.approx(0.6)  # 0.5 + 0.1


def test_mem057_persist_cross_instance(tmp_path: Path):
    db = tmp_path / "m.db"
    m1 = AutonomousMemory(event_service=None, db_path=db)
    m1.store(MemoryEntryKind.GOAL, "g1", {"note": "progress 50%"}, confidence=0.9)
    m2 = AutonomousMemory(event_service=None, db_path=db)
    entry = m2.retrieve(MemoryEntryKind.GOAL, "g1")
    assert entry is not None
    assert entry.content == {"note": "progress 50%"}


def test_mem057_goal_note(auto_memory):
    auto_memory.store_goal_note("goal-1", "analysis done")
    entry = auto_memory.retrieve(MemoryEntryKind.GOAL, "goal-1")
    assert entry is not None


# ---------------------------------------------------------------------------
# TASK-061 — Stuck Detection
# ---------------------------------------------------------------------------

from aios_core.autonomous import StuckDetector


@pytest.fixture()
def detector():
    return StuckDetector(window_size=20)


def test_stuck061_repeated_tool_calls(detector):
    for _ in range(3):
        detector.record("TOOL_CALL", "g1", {"tool_id": "python"})
    report = detector.detect("g1")
    assert "repeated_tool_calls" in report.signals
    assert report.verdict == "stuck"


def test_stuck061_repeated_errors(detector):
    for _ in range(3):
        detector.record("ERROR", "g1", {"fingerprint": "fp1"})
    assert "repeated_errors" in detector.detect("g1").signals


def test_stuck061_no_state_change(detector):
    for _ in range(5):
        detector.record("STATE_CHANGE", "g1", {"state": "RUNNING"})
    assert "no_state_change" in detector.detect("g1").signals


def test_stuck061_no_progress(detector):
    for _ in range(5):
        detector.record("TOOL_CALL", "g1", {"tool_id": f"t{_}"})
    assert "no_progress" in detector.detect("g1").signals


def test_stuck061_oscillation(detector):
    for state in ["A", "B", "A", "B"]:
        detector.record("STATE_CHANGE", "g1", {"state": state})
    report = detector.detect("g1")
    assert "oscillation" in report.signals
    assert report.verdict == "stuck"


def test_stuck061_no_oscillation_when_linear(detector):
    for state in ["A", "B", "C", "D"]:
        detector.record("STATE_CHANGE", "g1", {"state": state})
    assert "oscillation" not in detector.detect("g1").signals


def test_stuck061_budget_burn(detector):
    for _ in range(3):
        detector.record("BUDGET", "g1", {"cost": 1.0})
    report = detector.detect("g1")
    assert "budget_burn" in report.signals


def test_stuck061_contradictory_plans(detector):
    for _ in range(3):
        detector.record("REPLAN", "g1", {"reason": "world changed"})
    assert "contradictory_plans" in detector.detect("g1").signals


def test_stuck061_normal(detector):
    detector.record("TOOL_CALL", "g1", {"tool_id": "a"})
    detector.record("PROGRESS", "g1", {"progress": 0.5})
    detector.record("STATE_CHANGE", "g1", {"state": "A"})
    detector.record("STATE_CHANGE", "g1", {"state": "B"})
    report = detector.detect("g1")
    assert report.verdict == "normal"
    assert report.signals == []


def test_stuck061_reset(detector):
    for _ in range(3):
        detector.record("ERROR", "g1", {"fingerprint": "fp"})
    assert detector.detect("g1").verdict == "stuck"
    detector.reset("g1")
    assert detector.detect("g1").verdict == "normal"


def test_stuck061_empty_window(detector):
    assert detector.detect("g1").verdict == "normal"


def test_stuck061_window_bounded(detector):
    d = StuckDetector(window_size=5)
    for i in range(10):
        d.record("TOOL_CALL", "g1", {"tool_id": f"t{i}"})
    report = d.detect("g1")
    assert report.window_size == 5
    assert "repeated_tool_calls" not in report.signals  # window 5 — không đủ 3 lặp


def test_stuck061_progress_clears_no_progress(detector):
    for _ in range(5):
        detector.record("TOOL_CALL", "g1", {"tool_id": f"t{_}"})
    detector.record("PROGRESS", "g1", {"progress": 0.5})
    report = detector.detect("g1")
    assert "no_progress" not in report.signals


# ---------------------------------------------------------------------------
# TASK-058 — Autonomous Experimentation
# ---------------------------------------------------------------------------

from aios_core.autonomous import (
    AutonomousEvaluator,
    AutonomousVerdict,
    EvaluationConfig,
    EvaluationDimensions,
    ExperimentVerdict,
    ExperimentationEngine,
    Hypothesis,
    ProgressEstimator,
)


@pytest.fixture()
def hypothesis():
    return Hypothesis(
        id="h1", statement="retry=5 improves success",
        baseline=0.91, target_metric="success", target_value=0.96,
        direction="higher",
    )


def _engine(evaluate_fn, tmp_path, **kw):
    return ExperimentationEngine(
        evaluate_fn=evaluate_fn,
        db_path=tmp_path / "autonomous.db",
        **kw,
    )


def test_exp058_accepted_higher(hypothesis, tmp_path):
    def evaluate(_h, evidence_hint):
        return {"metric_value": 0.97, "result": "ok"}

    engine = _engine(evaluate, tmp_path)
    exp = engine.run(hypothesis, {"retry": 5})
    assert exp.verdict == ExperimentVerdict.ACCEPTED
    assert exp.metric_value == 0.97
    assert exp.evidence


def test_exp058_rejected_lower(hypothesis, tmp_path):
    def evaluate(_h, evidence_hint):
        return {"metric_value": 0.85}

    engine = _engine(evaluate, tmp_path)
    exp = engine.run(hypothesis, {})
    assert exp.verdict == ExperimentVerdict.REJECTED


def test_exp058_inconclusive_no_evidence(hypothesis, tmp_path):
    engine = _engine(lambda _h, _eh: {}, tmp_path)
    exp = engine.run(hypothesis, {})
    assert exp.verdict == ExperimentVerdict.INCONCLUSIVE


def test_exp058_inconclusive_between(hypothesis, tmp_path):
    def evaluate(_h, _eh):
        return {"metric_value": 0.94}  # giữa baseline 0.91 và target 0.96

    engine = _engine(evaluate, tmp_path)
    exp = engine.run(hypothesis, {})
    assert exp.verdict == ExperimentVerdict.INCONCLUSIVE


def test_exp058_direction_lower(tmp_path):
    h = Hypothesis(id="h2", statement="reduce cost", baseline=0.20,
                   target_metric="cost", target_value=0.10, direction="lower")

    def evaluate(_h, _eh):
        return {"metric_value": 0.08}

    engine = _engine(evaluate, tmp_path)
    assert engine.run(h, {}).verdict == ExperimentVerdict.ACCEPTED


def test_exp058_evaluate_fn_required():
    with pytest.raises(Exception):
        ExperimentationEngine(evaluate_fn=None)


def test_exp058_deploy_only_accepted(hypothesis, tmp_path):
    def evaluate(_h, _eh):
        return {"metric_value": 0.97}

    engine = _engine(evaluate, tmp_path)
    exp = engine.run(hypothesis, {})
    deployed = engine.deploy(exp.id)
    assert deployed.deployed is True
    assert deployed.canary is True


def test_exp058_deploy_rejected_raises(hypothesis, tmp_path):
    def evaluate(_h, _eh):
        return {"metric_value": 0.85}

    engine = _engine(evaluate, tmp_path)
    exp = engine.run(hypothesis, {})
    with pytest.raises(Exception):
        engine.deploy(exp.id)


def test_exp058_persist_cross_instance(hypothesis, tmp_path):
    db = tmp_path / "autonomous.db"
    engine = ExperimentationEngine(lambda _h, _eh: {"metric_value": 0.97}, db_path=db)
    exp = engine.run(hypothesis, {"retry": 5})
    engine2 = ExperimentationEngine(lambda _h, _eh: {"metric_value": 0.97}, db_path=db)
    loaded = engine2.get(exp.id)
    assert loaded.verdict == ExperimentVerdict.ACCEPTED
    assert loaded.params == {"retry": 5}
    assert len(engine2.list_experiments(hypothesis_id="h1")) == 1


def test_exp058_sandbox_used(hypothesis, tmp_path):
    calls = []

    def sandbox(params):
        calls.append(params)
        return {"ran": True}

    def evaluate(_h, _eh):
        return {"metric_value": 0.98, "result": _eh["result"]}

    engine = ExperimentationEngine(evaluate, db_path=tmp_path / "autonomous.db",
                                   sandbox_fn=sandbox)
    exp = engine.run(hypothesis, {"retry": 5})
    assert calls == [{"retry": 5}]
    assert exp.result == {"ran": True}


# ---------------------------------------------------------------------------
# TASK-060 — Autonomous Evaluation
# ---------------------------------------------------------------------------

@pytest.fixture()
def evaluator():
    return AutonomousEvaluator()


def test_ev060_continue(evaluator):
    verdict, estimate = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, quality=0.9, confidence=0.9, progress=0.5))
    assert verdict == AutonomousVerdict.CONTINUE
    assert estimate.completion == 0.5
    assert estimate.confidence == 0.9
    assert estimate.budget_remaining == 1.0


def test_ev060_stop_cost(evaluator):
    verdict, _ = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, cost=1.0))
    assert verdict == AutonomousVerdict.STOP


def test_ev060_ask_human_risk(evaluator):
    verdict, _ = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, risk=0.9))
    assert verdict == AutonomousVerdict.ASK_HUMAN


def test_ev060_retry_low_correctness(evaluator):
    verdict, _ = evaluator.evaluate("g1", EvaluationDimensions(correctness=0.5))
    assert verdict == AutonomousVerdict.RETRY


def test_ev060_replan_stuck(evaluator):
    for _ in range(3):
        evaluator.evaluate("g1", EvaluationDimensions(
            correctness=0.9, progress=0.3))
    verdict, estimate = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, progress=0.3))
    assert verdict == AutonomousVerdict.REPLAN
    assert estimate.progress_stuck is True


def test_ev060_not_stuck_when_progress_moves(evaluator):
    for i in range(3):
        evaluator.evaluate("g1", EvaluationDimensions(
            correctness=0.9, progress=0.1 + i * 0.1))
    verdict, estimate = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, progress=0.4))
    assert estimate.progress_stuck is False
    assert verdict == AutonomousVerdict.CONTINUE


def test_ev060_trajectory_warning(evaluator):
    _, estimate = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, trajectory_evidence={"tool_failures": 2}))
    assert estimate.trajectory_warning is True


def test_ev060_trajectory_clean(evaluator):
    _, estimate = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, trajectory_evidence={}))
    assert estimate.trajectory_warning is False


def test_ev060_confidence_min(evaluator):
    _, estimate = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.8, quality=0.6, confidence=0.9))
    assert estimate.confidence == 0.6  # min(0.8, 0.6, 0.9)


def test_ev060_estimator_reset(evaluator):
    for _ in range(3):
        evaluator.evaluate("g1", EvaluationDimensions(correctness=0.9, progress=0.3))
    evaluator._estimator.reset("g1")
    verdict, estimate = evaluator.evaluate("g1", EvaluationDimensions(
        correctness=0.9, progress=0.3))
    assert estimate.progress_stuck is False
    assert verdict == AutonomousVerdict.CONTINUE


def test_ev060_thresholds_injectable():
    ev = AutonomousEvaluator(config=EvaluationConfig(correctness_min=0.5))
    verdict, _ = ev.evaluate("g1", EvaluationDimensions(correctness=0.6))
    assert verdict == AutonomousVerdict.CONTINUE
