"""Observability router (TASK-021) — metrics, prompt history, doctor,
arch health, evaluations."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from ...observability.arch_health import ArchitectureHealth
from ...observability.doctor import HealthDoctor
from ...observability.evaluation import EvaluationStore
from ...observability.metrics import MetricsService
from ...observability.prompt_history import PromptHistory

router = APIRouter(tags=["observability"])


@router.get("/observability/metrics")
def metrics(request: Request) -> dict:
    service: MetricsService = request.app.state.registries["observability"]["metrics"]
    return {"data": service.summary()}


@router.get("/observability/prompt-history")
def prompt_history(request: Request, prompt_id: str | None = None, limit: int = 100) -> dict:
    store: PromptHistory = request.app.state.registries["observability"]["prompt_history"]
    records = store.list(prompt_id=prompt_id, limit=min(limit, 1000))
    return {
        "data": {
            "records": [
                {
                    "id": r.id,
                    "prompt_id": r.prompt_id,
                    "version": r.version,
                    "variables": r.variables,
                    "output": r.output,
                    "duration_ms": r.duration_ms,
                    "created_at": r.created_at,
                }
                for r in records
            ]
        }
    }


@router.get("/observability/doctor")
def doctor(request: Request) -> dict:
    doctor_service: HealthDoctor = request.app.state.registries["observability"]["doctor"]
    report = doctor_service.report()
    return {
        "data": {
            "status": report.status.value,
            "checks": [
                {"name": c.name, "status": c.status.value, "message": c.message}
                for c in report.checks
            ],
            "diagnostics": report.diagnostics,
        }
    }


@router.get("/observability/arch-health")
def arch_health(request: Request) -> dict:
    scanner: ArchitectureHealth = request.app.state.registries["observability"]["arch_health"]
    report = scanner.scan()
    return {
        "data": {
            "healthy": report.healthy,
            "violations": [
                {"kind": v.kind, "module": v.module, "message": v.message}
                for v in report.violations
            ],
        }
    }


@router.get("/observability/evaluations")
def evaluations(
    request: Request, workflow_id: str | None = None, limit: int = 100
) -> dict:
    store: EvaluationStore = request.app.state.registries["observability"]["evaluations"]
    rows = store.list(workflow_id=workflow_id, limit=min(limit, 1000))
    return {
        "data": {
            "evaluations": [
                {
                    "execution_id": r.execution_id,
                    "workflow_id": r.workflow_id,
                    "success": r.success,
                    "duration_ms": r.duration_ms,
                    "quality": r.quality,
                    "feedback": r.feedback,
                    "created_at": r.created_at,
                }
                for r in rows
            ],
            "counts": store.counts(),
            "average_quality": store.average_quality(workflow_id=workflow_id),
        }
    }


@router.post("/observability/evaluations/{execution_id}/feedback")
def evaluation_feedback(request: Request, execution_id: str, body: dict) -> dict:
    store: EvaluationStore = request.app.state.registries["observability"]["evaluations"]
    quality = body.get("quality")
    feedback = body.get("feedback", "")
    if not isinstance(quality, (int, float)) or not (0.0 <= float(quality) <= 1.0):
        raise HTTPException(status_code=422, detail="quality must be a number in [0, 1]")
    try:
        store.evaluate(execution_id, float(quality), str(feedback))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"data": {"execution_id": execution_id, "quality": float(quality), "feedback": feedback}}
