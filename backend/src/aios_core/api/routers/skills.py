"""Skills router (AC7)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["skills"])


@router.get("/skills")
def skills_list(request: Request, state: str | None = None) -> dict:
    sm = request.app.state.registries["skills"]
    from ...skills import SkillState

    if state is not None:
        try:
            skills = sm.list_by_state(SkillState(state))
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid skill state")
    else:
        skills = sm.list()
    return {"data": [_skill_dict(s) for s in skills]}


@router.get("/skills/{skill_id}")
def skill_detail(skill_id: str, request: Request) -> dict:
    sm = request.app.state.registries["skills"]
    skill = sm.get(skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="skill not found")
    return {"data": _skill_dict(skill)}


def _skill_dict(skill) -> dict:
    return {
        "id": skill.id,
        "name": skill.name,
        "version": skill.version,
        "state": skill.state.value,
        "source": skill.source.value,
        "manifest": skill.manifest,
    }
