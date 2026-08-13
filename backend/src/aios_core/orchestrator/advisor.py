"""Improvement Advisor (TASK-022) — deterministic rule-based suggestions.

No LLM (INV-010). Suggests improvements from evaluation/metrics/prompt data;
suggestions are NEVER auto-applied — a human/orchestrator decides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..observability.evaluation import EvaluationStore
from ..observability.metrics import MetricsService
from ..observability.prompt_history import PromptHistory

#: Ngưỡng rules (deterministic).
MIN_EVALS_QUALITY = 2
LOW_QUALITY = 0.5
MIN_EVALS_FAILURE = 3
FAILURE_RATIO = 0.5
MIN_TOOL_FAILURES = 3
MIN_RENDERS = 3
MIN_SLOW_SAMPLES = 3
SLOW_MS = 10_000.0


@dataclass(frozen=True)
class Suggestion:
    kind: str      # workflow | prompt | skill | capability
    action: str    # create | improve | review
    target: str    # component name ("" when unknown)
    reason: str
    evidence: dict[str, Any]


class ImprovementAdvisor:
    def __init__(
        self,
        evaluation_store: EvaluationStore,
        metrics_service: MetricsService,
        prompt_history: PromptHistory,
    ) -> None:
        self._evals = evaluation_store
        self._metrics = metrics_service
        self._prompts = prompt_history

    def suggest(self) -> list[Suggestion]:
        suggestions: list[Suggestion] = []
        suggestions.extend(self._rule_low_quality())
        suggestions.extend(self._rule_many_failures())
        suggestions.extend(self._rule_tool_failures())
        suggestions.extend(self._rule_unreviewed_prompts())
        suggestions.extend(self._rule_slow_workflows())
        # dedup + deterministic sort
        seen: set[tuple[str, str, str]] = set()
        unique: list[Suggestion] = []
        for s in suggestions:
            key = (s.kind, s.action, s.target)
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return sorted(unique, key=lambda s: (s.kind, s.target, s.action))

    # -- rules ----------------------------------------------------------------

    def _grouped_evaluations(self) -> dict[str, list[Any]]:
        """{workflow_id: [WorkflowEvaluation, ...]} from the full store."""
        grouped: dict[str, list[Any]] = {}
        for row in self._evals.list(limit=10_000):
            grouped.setdefault(row.workflow_id, []).append(row)
        return grouped

    def _rule_low_quality(self) -> list[Suggestion]:
        out: list[Suggestion] = []
        for workflow_id, rows in self._grouped_evaluations().items():
            if len(rows) < MIN_EVALS_QUALITY:
                continue
            scored = [r.quality for r in rows if r.quality is not None]
            if not scored:
                continue  # không có quality → bỏ qua (P1-5 v1)
            avg = sum(scored) / len(scored)
            if avg < LOW_QUALITY:
                out.append(
                    Suggestion(
                        kind="workflow", action="improve", target=workflow_id,
                        reason=f"average quality {avg:.2f} below {LOW_QUALITY}",
                        evidence={"avg_quality": avg, "evaluations": len(rows)},
                    )
                )
        return out

    def _rule_many_failures(self) -> list[Suggestion]:
        out: list[Suggestion] = []
        for workflow_id, rows in self._grouped_evaluations().items():
            if len(rows) < MIN_EVALS_FAILURE:
                continue
            failed = sum(1 for r in rows if not r.success)
            if failed / len(rows) > FAILURE_RATIO:
                out.append(
                    Suggestion(
                        kind="workflow", action="review", target=workflow_id,
                        reason=f"failure ratio {failed}/{len(rows)} above {FAILURE_RATIO}",
                        evidence={"failed": failed, "total": len(rows)},
                    )
                )
        return out

    def _rule_tool_failures(self) -> list[Suggestion]:
        failures = self._metrics.tool_failures()
        if failures >= MIN_TOOL_FAILURES:
            return [
                Suggestion(
                    kind="capability", action="review", target="",
                    reason=f"{failures} tool failures observed",
                    evidence={"tool_failures": failures},
                )
            ]
        return []

    def _rule_unreviewed_prompts(self) -> list[Suggestion]:
        out: list[Suggestion] = []
        counts: dict[str, int] = {}
        for record in self._prompts.list(limit=10_000):
            counts[record.prompt_id] = counts.get(record.prompt_id, 0) + 1
        for prompt_id, count in sorted(counts.items()):
            if count >= MIN_RENDERS:
                out.append(
                    Suggestion(
                        kind="prompt", action="review", target=prompt_id,
                        reason=f"rendered {count} times without evaluation",
                        evidence={"renders": count},
                    )
                )
        return out

    def _rule_slow_workflows(self) -> list[Suggestion]:
        out: list[Suggestion] = []
        by_workflow = self._metrics.duration_by_workflow()
        for plan_id, (avg_ms, count) in sorted(by_workflow.items()):
            if count >= MIN_SLOW_SAMPLES and avg_ms > SLOW_MS:
                out.append(
                    Suggestion(
                        kind="workflow", action="improve", target=plan_id,
                        reason=f"average duration {avg_ms:.0f}ms above {SLOW_MS:.0f}ms",
                        evidence={"avg_duration_ms": avg_ms, "samples": count},
                    )
                )
        return out
