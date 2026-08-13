"""Prompts + models + sandbox routers (AC10, C2-09)."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["prompts-models-sandbox"])


@router.get("/prompts")
def prompts_list(request: Request) -> dict:
    reg = request.app.state.registries["prompts"]
    data = []
    for pid in reg.list():
        prompt = reg.get(pid)
        data.append({
            "id": prompt.id,
            "name": prompt.name,
            "version": prompt.version,
            "description": prompt.description,
        })
    return {"data": data}


@router.get("/models")
def models_list(request: Request) -> dict:
    reg = request.app.state.registries["models"]
    data = []
    for name in reg.list():
        model = reg.get(name)
        data.append({"name": name, "available": model.is_available()})
    return {"data": data}


@router.get("/sandbox")
def sandbox_stats(request: Request) -> dict:
    pool = request.app.state.registries["sandbox"]
    return {"data": pool.health()}
