"""Goals router (AC6)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["goals"])


@router.get("/goals")
def goals_list(request: Request, status: str | None = None, limit: int = 100) -> dict:
    gm = request.app.state.registries["goals"]
    from ...orchestrator.goals import GoalStatus

    goal_status = None
    if status is not None:
        try:
            goal_status = GoalStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid goal status")
    return {"data": [_goal_dict(g) for g in gm.list_goals(status=goal_status, limit=limit)]}


@router.get("/goals/{goal_id}")
def goal_detail(goal_id: str, request: Request) -> dict:
    gm = request.app.state.registries["goals"]
    goal = gm.get_goal(goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="goal not found")
    return {"data": _goal_dict(goal)}


def _goal_dict(goal) -> dict:
    return {
        "id": goal.id,
        "title": goal.title,
        "status": goal.status.value,
        "progress": goal.progress,
        "tasks": [
            {"id": t.id, "title": t.title, "workflow_name": t.workflow_name,
             "status": t.status.value}
            for t in goal.tasks
        ],
    }
