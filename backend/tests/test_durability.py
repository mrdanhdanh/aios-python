"""TASK-066 — Durable Execution 1.0: journal + verify-before-resume + idempotency."""

from __future__ import annotations

import pytest

from aios_core.kernel.durability import (
    DurabilityPolicy,
    ExecutionJournal,
    IdempotencyClassifier,
    JournalError,
    JournaledExecutor,
    OpClass,
    RetryDecision,
    RunReason,
)
from aios_core.kernel.execution_plan import ExecutionPlan, PlanNode


def _plan(nodes: list[str]) -> ExecutionPlan:
    return ExecutionPlan(
        id="p1",
        nodes=[
            PlanNode(id=n, type="task", name=n, depends_on=[])
            for n in nodes
        ],
    )


# ---------------------------------------------------------------------------
# AC1: journal ghi đủ trạng thái + persist
# ---------------------------------------------------------------------------

def test_journal_persist_states(tmp_path):
    j = ExecutionJournal(tmp_path / "j.db")
    j.start_execution("e1", ["a", "b", "c"])
    assert j.get_entry("e1", "a").status.value == "pending"
    j.mark_running("e1", "a")
    assert j.get_entry("e1", "a").status.value == "running"
    j.mark_done("e1", "a", {"result": "ok"})
    entry = j.get_entry("e1", "a")
    assert entry.status.value == "done"
    assert entry.payload["result"] == "ok"
    # persist: mở lại DB mới
    j2 = ExecutionJournal(tmp_path / "j.db")
    assert j2.nodes_done("e1") == ["a"]
    assert j2.exists("e1")
    j.close()
    j2.close()


# ---------------------------------------------------------------------------
# AC2: crash → resume → node done không chạy lại (event count)
# ---------------------------------------------------------------------------

def test_resume_skips_done_nodes(tmp_path):
    j = ExecutionJournal(tmp_path / "j.db")
    executor = JournaledExecutor(j)
    runs: list[str] = []

    def runner(node_id: str, ctx: dict) -> str:
        runs.append(node_id)
        if node_id == "c":
            raise RuntimeError("crash at node c")
        return f"ok:{node_id}"

    plan = _plan(["a", "b", "c", "d"])
    with pytest.raises(RuntimeError):
        executor.execute("e1", plan, runner)

    assert runs == ["a", "b", "c"]  # c crash giữa chừng
    # resume: a,b done → chỉ chạy c (lại) và d
    runs2: list[str] = []
    executor.resume("e1", plan, lambda n, c: runs2.append(n) or f"ok:{n}")
    assert runs2 == ["c", "d"], f"node done bị chạy lại: {runs2}"
    assert j.nodes_done("e1") == ["a", "b", "c", "d"]
    assert j.run_reason("e1") == RunReason.RESUME.value
    j.close()


def test_resume_all_done_no_rerun(tmp_path):
    j = ExecutionJournal(tmp_path / "j.db")
    executor = JournaledExecutor(j)
    plan = _plan(["a", "b"])
    executor.execute("e1", plan, lambda n, c: f"ok:{n}")
    calls: list[str] = []
    executor.resume("e1", plan, lambda n, c: calls.append(n) or "x")
    assert calls == []  # mọi node done → không chạy lại
    j.close()


# ---------------------------------------------------------------------------
# AC3: journal thiếu → fail-closed; verify lệch → fail-closed
# ---------------------------------------------------------------------------

def test_resume_missing_journal_raises(tmp_path):
    j = ExecutionJournal(tmp_path / "j.db")
    executor = JournaledExecutor(j)
    with pytest.raises(JournalError):
        executor.resume("ghost", _plan(["a"]), lambda n, c: None)
    j.close()


def test_resume_verify_mismatch_raises(tmp_path):
    j = ExecutionJournal(tmp_path / "j.db")
    executor = JournaledExecutor(
        j,
        snapshot_verify=lambda eid, done: False,  # journal lệch snapshot
    )
    plan = _plan(["a", "b"])
    with pytest.raises(RuntimeError):
        executor.execute("e1", plan, lambda n, c: (_ for _ in ()).throw(RuntimeError("crash")))
    with pytest.raises(JournalError):
        executor.resume("e1", plan, lambda n, c: None)
    j.close()


# ---------------------------------------------------------------------------
# AC4/AC5: idempotency classification
# ---------------------------------------------------------------------------

def test_classifier_read_and_write():
    clf = IdempotencyClassifier(
        read_ops={"fs.read", "db.select"},
        idempotent_writes={"fs.write_same", "cache.set"},
    )
    assert clf.classify("fs.read") == OpClass.READ
    assert clf.classify("fs.write_same") == OpClass.IDEMPOTENT_WRITE
    # fail-closed: không khai báo = non-idempotent
    assert clf.classify("db.insert_sequence") == OpClass.NON_IDEMPOTENT_WRITE


def test_decision_retry_vs_approve():
    clf = IdempotencyClassifier(read_ops={"r"}, idempotent_writes={"w"})
    assert clf.decision("r") == RetryDecision.RETRY
    assert clf.decision("w") == RetryDecision.RETRY
    # non-idempotent: không tự retry
    assert clf.decision("n") == RetryDecision.APPROVE
    # đã fail → cần compensate trước
    assert clf.decision("n", has_failed=True) == RetryDecision.COMPENSATE


def test_non_idempotent_retry_blocked_by_decision():
    """AC5: op non-idempotent không bao giờ được RetryDecision.RETRY."""
    clf = IdempotencyClassifier()
    for op in ("insert", "send_email", "deploy", "anything"):
        assert clf.decision(op) != RetryDecision.RETRY


# ---------------------------------------------------------------------------
# AC6: policy rerun
# ---------------------------------------------------------------------------

def test_policy_rerun_restarts(tmp_path):
    j = ExecutionJournal(tmp_path / "j.db")
    executor = JournaledExecutor(j, policy=DurabilityPolicy(mode="rerun"))
    plan = _plan(["a", "b"])
    with pytest.raises(RuntimeError):
        executor.execute("e1", plan, lambda n, c: (_ for _ in ()).throw(RuntimeError("x")))
    calls: list[str] = []
    executor.resume("e1", plan, lambda n, c: calls.append(n) or "ok")
    assert calls == ["a", "b"]  # rerun theo policy
    assert j.run_reason("e1") == RunReason.RERUN_BY_POLICY.value
    j.close()


# ---------------------------------------------------------------------------
# AC7: config
# ---------------------------------------------------------------------------

def test_durability_settings_config():
    from aios_core.config import DurabilitySettings, Settings

    s = Settings()
    assert s.durability.enabled is True
    assert s.durability.policy.mode == "resume"
    assert s.durability.policy.require_verify is True
    d = DurabilitySettings(policy={"mode": "rerun"})
    assert d.policy.mode == "rerun"
