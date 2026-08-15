"""Autonomous Experimentation (TASK-058 — M9-P3, A4).

Hypothesis → Experiment Design → Sandbox → Execute → Evaluate → Compare
baseline → Accept/Reject (PLAN §M9-21). **INV-033: cải thiện tự thân phải qua
Experiment → Harness/Evaluation → Evidence → Decision → Deploy** — không
"LLM-says-better → production". Deploy = đánh dấu canary (KHÔNG tự sửa
production — human/operator thực thi thật).
"""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from ..kernel.events import EventType
from ..kernel.services.events import EventService
from .contracts import Experiment, ExperimentVerdict, Hypothesis
from .errors import ExperimentError

_DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS autonomous_experiments (
    id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    params_json TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT 'null',
    metric_value REAL,
    evidence_json TEXT NOT NULL DEFAULT '{}',
    verdict TEXT NOT NULL,
    deployed INTEGER NOT NULL DEFAULT 0,
    canary INTEGER NOT NULL DEFAULT 0,
    at TEXT NOT NULL
)
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_experiment_id() -> str:
    return f"exp-{uuid.uuid4().hex[:12]}"


class ExperimentationEngine:
    """Pipeline experiment — verdict CHỈ từ evidence (INV-033).

    ``evaluate_fn`` BẮT BUỘC qua constructor (C1-02 v1, fail-fast) —
    experiment phải gọi evaluation (harness API khi wiring); sandbox_fn là
    nơi chạy thử nghiệm (C2-01 v2, không chạy trực tiếp).
    """

    def __init__(
        self,
        evaluate_fn: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
        event_service: EventService | None = None,
        db_path: Path | str = "aios/data/autonomous.db",
        sandbox_fn: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        if evaluate_fn is None:
            raise ExperimentError("evaluate_fn bắt buộc (INV-033 — evidence-first)")
        self._evaluate = evaluate_fn
        self._sandbox = sandbox_fn or (lambda params: params)
        self._events = event_service
        self._db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_db()

    # -- main ------------------------------------------------------------------

    def run(self, hypothesis: Hypothesis, params: dict[str, Any] | None = None) -> Experiment:
        """sandbox → evaluate → compare baseline (direction) → verdict."""
        with self._lock:
            params = dict(params or {})
            if hypothesis.baseline is None or hypothesis.target_value is None:
                raise ExperimentError("hypothesis cần baseline + target_value")
            result = self._sandbox(params)
            # evaluate_fn signature: (hypothesis, evidence_hint) — positional
            evidence = self._evaluate(hypothesis, {"result": result, "params": params})
            # evidence bắt buộc (C2-02 v1): metric_value/result
            metric = evidence.get("metric_value", evidence.get("result"))
            if not evidence or metric is None:
                verdict = ExperimentVerdict.INCONCLUSIVE
            else:
                verdict = self._compare(metric, hypothesis)
            exp = Experiment(
                id=new_experiment_id(),
                hypothesis_id=hypothesis.id,
                params=params,
                result=result,
                metric_value=metric if isinstance(metric, (int, float)) else None,
                evidence=evidence,
                verdict=verdict,
                at=_now_iso(),
            )
            self._persist(exp)
            self._emit(exp)
            return exp

    def deploy(self, experiment_id: str) -> Experiment:
        """Canary deploy — chỉ khi ACCEPTED (C1-03 v1, R2-2 v2)."""
        with self._lock:
            row = self._get_row(experiment_id)
            if row is None:
                raise ExperimentError(f"experiment không tồn tại: {experiment_id}")
            if row["verdict"] != ExperimentVerdict.ACCEPTED.value:
                raise ExperimentError(
                    f"deploy chỉ khi ACCEPTED (verdict={row['verdict']})"
                )
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    "UPDATE autonomous_experiments SET deployed=1, canary=1 WHERE id=?",
                    (experiment_id,),
                )
            return self.get(experiment_id)

    def get(self, experiment_id: str) -> Experiment:
        with self._lock:
            row = self._get_row(experiment_id)
            if row is None:
                raise ExperimentError(f"experiment không tồn tại: {experiment_id}")
            return self._row_to_exp(row)

    def list_experiments(self, hypothesis_id: str | None = None) -> list[Experiment]:
        with self._lock:
            with closing(self._connect()) as conn:
                conn.row_factory = sqlite3.Row
                if hypothesis_id:
                    rows = conn.execute(
                        "SELECT * FROM autonomous_experiments WHERE hypothesis_id=? ORDER BY at",
                        (hypothesis_id,),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM autonomous_experiments ORDER BY at"
                    ).fetchall()
            return [self._row_to_exp(r) for r in rows]

    # -- internals -------------------------------------------------------------

    @staticmethod
    def _compare(metric: float, hypothesis: Hypothesis) -> ExperimentVerdict:
        """Compare deterministic theo direction (C1-01 v1)."""
        if hypothesis.direction == "lower":
            if metric <= hypothesis.target_value:
                return ExperimentVerdict.ACCEPTED
            if metric >= hypothesis.baseline:
                return ExperimentVerdict.REJECTED
            return ExperimentVerdict.INCONCLUSIVE
        # higher (mặc định)
        if metric >= hypothesis.target_value:
            return ExperimentVerdict.ACCEPTED
        if metric <= hypothesis.baseline:
            return ExperimentVerdict.REJECTED
        return ExperimentVerdict.INCONCLUSIVE

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.execute(_DB_SCHEMA)

    def _persist(self, exp: Experiment) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO autonomous_experiments (id, hypothesis_id, params_json,
                    result_json, metric_value, evidence_json, verdict, deployed,
                    canary, at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exp.id,
                    exp.hypothesis_id,
                    json.dumps(exp.params, default=str),
                    json.dumps(exp.result, default=str),
                    exp.metric_value,
                    json.dumps(exp.evidence, default=str),
                    exp.verdict.value,
                    int(exp.deployed),
                    int(exp.canary),
                    exp.at,
                ),
            )

    def _get_row(self, experiment_id: str) -> sqlite3.Row | None:
        with closing(self._connect()) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(
                "SELECT * FROM autonomous_experiments WHERE id=?", (experiment_id,)
            ).fetchone()

    @staticmethod
    def _row_to_exp(row: sqlite3.Row) -> Experiment:
        return Experiment(
            id=row["id"],
            hypothesis_id=row["hypothesis_id"],
            params=json.loads(row["params_json"]),
            result=json.loads(row["result_json"]),
            metric_value=row["metric_value"],
            evidence=json.loads(row["evidence_json"]),
            verdict=ExperimentVerdict(row["verdict"]),
            deployed=bool(row["deployed"]),
            canary=bool(row["canary"]),
            at=row["at"],
        )

    def _emit(self, exp: Experiment) -> None:
        if self._events is None:
            return
        self._events.emit(
            EventType.AUTONOMY_EXPERIMENT,
            {
                "experiment_id": exp.id,
                "hypothesis_id": exp.hypothesis_id,
                "verdict": exp.verdict.value,
            },
            source="autonomous.experimentation",
        )
