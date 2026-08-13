"""Tools router (AC8)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["tools"])


@router.get("/tools")
def tools_list(request: Request) -> dict:
    reg = request.app.state.registries["tools"]
    return {"data": [_tool_dict(t) for t in reg.list()]}


@router.get("/tools/{tool_id}")
def tool_detail(tool_id: str, request: Request) -> dict:
    reg = request.app.state.registries["tools"]
    tool = reg.get(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail="tool not found")
    return {"data": _tool_dict(tool)}


def _tool_dict(tool) -> dict:
    return {
        "id": tool.id,
        "name": tool.name,
        "tool_type": tool.tool_type,
        "capabilities": list(tool.capabilities),
        "available": tool.available(),
        "description": tool.description,
    }
