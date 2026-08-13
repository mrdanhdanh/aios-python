"""Catalog router (AC5)."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog_list(request: Request) -> dict:
    cat = request.app.state.registries["catalog"]
    return {"data": [_entry_dict(e) for e in cat.search("")]}


@router.get("/catalog/search")
def catalog_search(request: Request, q: str, kind: str | None = None) -> dict:
    cat = request.app.state.registries["catalog"]
    return {"data": [_entry_dict(e) for e in cat.search(q, kind=kind)]}


def _entry_dict(entry) -> dict:
    return {
        "kind": entry.kind,
        "id": entry.id,
        "metadata": entry.metadata,
    }
