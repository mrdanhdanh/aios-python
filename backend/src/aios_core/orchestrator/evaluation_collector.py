"""Evaluation Collector (TASK-022) — runs evaluators on workflow outcomes.

Auto-record is done by EvaluationStore via the bus (TASK-021); this collector
adds the evaluator layer on top (quality/feedback). Best-effort: evaluator
errors AND missing rows (KeyError) are swallowed.
"""

from __future__ import annotations

from typing import Any

from ..observability.evaluation import EvaluationStore, Evaluator, EvaluationVerdict


class EvaluationCollector:
    def __init__(
        self,
        evaluation_store: EvaluationStore,
        evaluator: Evaluator | None = None,
    ) -> None:
        self._store = evaluation_store
        self._evaluator = evaluator

    def collect_workflow(self, workflow_id: str, execution_id: str, result: dict[str, Any]) -> None:
        """Run the evaluator (if wired) and attach quality/feedback. Never raises."""
        if self._evaluator is None:
            return
        try:
            verdict: EvaluationVerdict = self._evaluator.evaluate(workflow_id, execution_id, result)
            if verdict.quality is not None:
                self._store.evaluate(execution_id, verdict.quality, verdict.feedback)
        except KeyError:
            return  # store chưa có row (restart giữa chừng) — best-effort (P1-4)
        except Exception:  # noqa: BLE001 — evaluator lỗi không crash collector
            return

    def collect_all(self) -> dict[str, dict[str, Any]]:
        """Aggregate stats per workflow: {workflow_id: {count, success, failed, avg_quality}}."""
        grouped: dict[str, list[Any]] = {}
        for row in self._store.list(limit=10_000):
            grouped.setdefault(row.workflow_id, []).append(row)
        out: dict[str, dict[str, Any]] = {}
        for workflow_id in sorted(grouped):
            rows = grouped[workflow_id]
            scored = [r.quality for r in rows if r.quality is not None]
            out[workflow_id] = {
                "count": len(rows),
                "success": sum(1 for r in rows if r.success),
                "failed": sum(1 for r in rows if not r.success),
                "avg_quality": (sum(scored) / len(scored)) if scored else None,
            }
        return out
