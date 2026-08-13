"""Orchestrator v2 router (TASK-022) — advisor, supervisor, goal reports."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["orchestrator-v2"])


@router.get("/orchestrator-v2/advisor/suggestions")
def advisor_suggestions(request: Request) -> dict:
    advisor = request.app.state.registries["orchestrator_v2"]["advisor"]
    suggestions = advisor.suggest()
    return {
        "data": {
            "suggestions": [
                {
                    "kind": s.kind,
                    "action": s.action,
                    "target": s.target,
                    "reason": s.reason,
                    "evidence": s.evidence,
                }
                for s in suggestions
            ]
        }
    }


@router.get("/orchestrator-v2/supervisor/snapshot")
def supervisor_snapshot(request: Request) -> dict:
    supervisor = request.app.state.registries["orchestrator_v2"]["supervisor"]
    snap = supervisor.snapshot()
    return {
        "data": {
            "running": list(snap.running),
            "recent_completed": snap.recent_completed,
            "recent_failed": snap.recent_failed,
            "queue_size": snap.queue_size,
            "stuck": list(snap.stuck),
        }
    }


@router.get("/orchestrator-v2/goals/report")
def goals_report(request: Request) -> dict:
    reporter = request.app.state.registries["orchestrator_v2"]["goal_reporter"]
    report = reporter.report()
    return {
        "data": {
            "total": report.total,
            "by_status": report.by_status,
            "avg_progress": report.avg_progress,
            "completed_tasks": report.completed_tasks,
            "failed_tasks": report.failed_tasks,
            "goals": list(report.goals),
        }
    }


@router.get("/orchestrator-v2/goals/{goal_id}/report")
def goal_report(request: Request, goal_id: str) -> dict:
    reporter = request.app.state.registries["orchestrator_v2"]["goal_reporter"]
    report = reporter.report_goal(goal_id)
    if report is None:
        raise HTTPException(status_code=404, detail=f"goal not found: {goal_id}")
    return {"data": report}
