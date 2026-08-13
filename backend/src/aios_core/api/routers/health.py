"""Health router (AC2) — mapping C2-02: ok = status != UNHEALTHY,
score = 1 - weight/2 (healthy=1.0, degraded=0.5, unhealthy=0.0)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from ...healthcheck import HealthStatus, _STATUS_WEIGHT

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    reg = request.app.state.registries["health"]
    reports = reg.get_all()
    components = [
        {
            "name": r.name,
            "ok": r.status != HealthStatus.UNHEALTHY,
            "status": r.status.value,
            "detail": r.message,
        }
        for r in reports
    ]
    score = 0.0
    if reports:
        score = sum(1.0 - _STATUS_WEIGHT[r.status] / 2 for r in reports) / len(reports)
    return {"data": {"components": components, "health_score": round(score, 2)}}
