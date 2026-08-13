"""Memory router — artifacts + conversations (AC9, C2-08)."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["memory"])


@router.get("/artifacts")
def artifacts_list(request: Request) -> dict:
    svc = request.app.state.registries["artifact_service"]
    artifacts = svc.list()[:100]
    return {"data": [_artifact_dict(a) for a in artifacts]}


@router.get("/conversations")
def conversations_list(request: Request, session_id: str | None = None) -> dict:
    mem = request.app.state.registries["conversations"]
    ids = mem.list_conversations(session_id) if session_id else []
    data = []
    for cid in ids:
        data.append({"id": cid, "messages": mem.get_messages(cid)})
    return {"data": data}


def _artifact_dict(artifact) -> dict:
    return {
        "id": artifact.id,
        "name": artifact.name,
        "artifact_type": artifact.type.value,
        "metadata": artifact.metadata,
    }
