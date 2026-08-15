"""Durable Execution 1.0 — M10-F2 (TASK-066).

Execution journal + verify-before-resume + idempotency classification.
Crash → load journal → verify → resume từ node chưa done (KHÔNG chạy lại
node đã xong, trừ khi policy rerun). Fail-closed: journal lệch → raise.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field


class JournalError(RuntimeError):
    """Journal không thể resume (thiếu/lệch/corrupt)."""


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"


class RunReason(str, Enum):
    FIRST_RUN = "first_run"
    RESUME = "resume"
    RERUN_BY_POLICY = "rerun_by_policy"


class OpClass(str, Enum):
    READ = "read"                    # an toàn retry
    IDEMPOTENT_WRITE = "idempotent_write"  # retry được
    NON_IDEMPOTENT_WRITE = "non_idempotent_write"  # không tự retry → approve


class RetryDecision(str, Enum):
    RETRY = "retry"
    APPROVE = "approve"   # cần human approval
    COMPENSATE = "compensate"


class IdempotencyClassifier:
    """Phân loại operation. Fail-closed: op không khai báo = non-idempotent."""

    def __init__(
        self,
        read_ops: set[str] | None = None,
        idempotent_writes: set[str] | None = None,
    ) -> None:
        self._reads = read_ops or set()
        self._writes = idempotent_writes or set()

    def classify(self, op: str) -> OpClass:
        if op in self._reads:
            return OpClass.READ
        if op in self._writes:
            return OpClass.IDEMPOTENT_WRITE
        return OpClass.NON_IDEMPOTENT_WRITE

    def decision(self, op: str, has_failed: bool = False) -> RetryDecision:
        """Quyết định khi op fail (hoặc cần chạy lại).

        read → RETRY; idempotent_write → RETRY; non_idempotent_write →
        APPROVE (tuyệt đối không tự retry). has_failed=True (đã fail 1 lần)
        với non-idempotent → COMPENSATE (cần bù trừ trước khi chạy lại).
        """
        cls = self.classify(op)
        if cls == OpClass.READ:
            return RetryDecision.RETRY
        if cls == OpClass.IDEMPOTENT_WRITE:
            return RetryDecision.RETRY
        # non-idempotent: không tự retry
        return RetryDecision.COMPENSATE if has_failed else RetryDecision.APPROVE


@dataclass
class JournalEntry:
    node_id: str
    status: NodeStatus
    payload: dict[str, Any] = field(default_factory=dict)


class ExecutionJournal:
    """SQLite journal — mỗi node write atomic (transaction)."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_journal (
                execution_id TEXT NOT NULL,
                node_id      TEXT NOT NULL,
                status       TEXT NOT NULL,
                payload      TEXT NOT NULL DEFAULT '{}',
                run_reason   TEXT NOT NULL DEFAULT 'first_run',
                updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (execution_id, node_id)
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def start_execution(self, execution_id: str, nodes: list[str],
                        reason: RunReason = RunReason.FIRST_RUN) -> None:
        with self._conn:
            self._conn.execute(
                "DELETE FROM execution_journal WHERE execution_id = ?",
                (execution_id,),
            )
            self._conn.executemany(
                "INSERT INTO execution_journal "
                "(execution_id, node_id, status, run_reason) VALUES (?, ?, 'pending', ?)",
                [(execution_id, n, reason.value) for n in nodes],
            )

    def mark_running(self, execution_id: str, node_id: str) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE execution_journal SET status = 'running' "
                "WHERE execution_id = ? AND node_id = ?",
                (execution_id, node_id),
            )

    def mark_done(self, execution_id: str, node_id: str,
                  payload: dict[str, Any] | None = None) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE execution_journal SET status = 'done', payload = ? "
                "WHERE execution_id = ? AND node_id = ?",
                (json.dumps(payload or {}), execution_id, node_id),
            )

    def get_entry(self, execution_id: str, node_id: str) -> JournalEntry | None:
        row = self._conn.execute(
            "SELECT node_id, status, payload FROM execution_journal "
            "WHERE execution_id = ? AND node_id = ?",
            (execution_id, node_id),
        ).fetchone()
        if row is None:
            return None
        return JournalEntry(node_id=row[0], status=NodeStatus(row[1]),
                            payload=json.loads(row[2]))

    def nodes_done(self, execution_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT node_id FROM execution_journal "
            "WHERE execution_id = ? AND status = 'done' ORDER BY rowid",
            (execution_id,),
        ).fetchall()
        return [r[0] for r in rows]

    def exists(self, execution_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM execution_journal WHERE execution_id = ? LIMIT 1",
            (execution_id,),
        ).fetchone()
        return row is not None

    def run_reason(self, execution_id: str) -> str:
        row = self._conn.execute(
            "SELECT run_reason FROM execution_journal "
            "WHERE execution_id = ? LIMIT 1",
            (execution_id,),
        ).fetchone()
        return row[0] if row else "unknown"

    def set_run_reason(self, execution_id: str, reason: RunReason) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE execution_journal SET run_reason = ? "
                "WHERE execution_id = ?",
                (reason.value, execution_id),
            )


class DurabilityPolicy(BaseModel):
    """Chính sách resume sau crash (PLAN §M10-13)."""

    model_config = ConfigDict(extra="forbid")

    mode: str = "resume"  # 'resume' | 'rerun'
    require_verify: bool = True  # verify journal ↔ snapshot trước khi resume


class JournaledExecutor:
    """Wrapper: chạy plan với journal per-node; resume không chạy lại node done.

    Không sửa ExecutionService — nhận `node_runner: Callable[[str, dict], Any]`
    (node_id, ctx) do caller cung cấp. Node chạy lại bị chặn bằng journal.
    """

    def __init__(
        self,
        journal: ExecutionJournal,
        policy: DurabilityPolicy | None = None,
        snapshot_verify: Callable[[str, list[str]], bool] | None = None,
    ) -> None:
        self.journal = journal
        self.policy = policy or DurabilityPolicy()
        # snapshot_verify(execution_id, done_nodes) → bool — mặc định True.
        self._snapshot_verify = snapshot_verify or (lambda _eid, _done: True)

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def topo_order(plan: Any) -> list[str]:
        """Topological order từ plan nodes (dependencies)."""
        nodes = {n.id: set(n.depends_on or []) for n in plan.nodes}
        ordered: list[str] = []
        visited: set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            for dep in nodes.get(node_id, ()):
                visit(dep)
            ordered.append(node_id)

        for nid in nodes:
            visit(nid)
        return ordered

    # -- main API ------------------------------------------------------------
    def execute(self, execution_id: str, plan: Any,
                node_runner: Callable[[str, dict[str, Any]], Any],
                context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Chạy plan từ đầu (first run)."""
        nodes = self.topo_order(plan)
        self.journal.start_execution(
            execution_id, nodes, RunReason.FIRST_RUN
        )
        return self._run_nodes(execution_id, nodes, node_runner, context or {})

    def resume(self, execution_id: str, plan: Any,
               node_runner: Callable[[str, dict[str, Any]], Any],
               context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Resume sau crash: verify → chạy node chưa done (fail-closed)."""
        if not self.journal.exists(execution_id):
            raise JournalError(
                f"execution {execution_id} không có journal — không resume được"
            )
        done = self.journal.nodes_done(execution_id)
        if self.policy.require_verify and not self._snapshot_verify(execution_id, done):
            raise JournalError(
                f"execution {execution_id}: journal lệch snapshot (nodes done: {done})"
            )
        if self.policy.mode == "rerun":
            # policy yêu cầu chạy lại từ đầu (ghi rõ lý do — C2-02)
            nodes = self.topo_order(plan)
            self.journal.start_execution(
                execution_id, nodes, RunReason.RERUN_BY_POLICY
            )
            return self._run_nodes(execution_id, nodes, node_runner, context or {})
        nodes = self.topo_order(plan)
        done = set(self.journal.nodes_done(execution_id))
        pending = [n for n in nodes if n not in done]
        if not pending:
            # mọi node đã xong — không chạy lại (durable)
            return {n: None for n in done}
        self.journal.set_run_reason(execution_id, RunReason.RESUME)
        return self._run_nodes(execution_id, pending, node_runner, context or {},
                               skip=done)

    def _run_nodes(self, execution_id: str, nodes: list[str],
                   node_runner: Callable[[str, dict[str, Any]], Any],
                   context: dict[str, Any],
                   skip: set[str] | None = None) -> dict[str, Any]:
        skip = skip or set()
        results: dict[str, Any] = {}
        for node_id in nodes:
            if node_id in skip:
                continue
            self.journal.mark_running(execution_id, node_id)
            try:
                payload = node_runner(node_id, context)
            except Exception:
                # crash giữa node — journal giữ 'running' → resume tiếp node này
                raise
            results[node_id] = payload
            self.journal.mark_done(execution_id, node_id, {"result": repr(payload)})
        return results
