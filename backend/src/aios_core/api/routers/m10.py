"""M10 router (TASK-072) — Dashboard 1.0: overview + execution timeline."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["m10"])


@router.get("/m10/overview")
def overview(request: Request) -> dict:
    """Health + SLO + security + contract summary (Dashboard Overview tab)."""
    regs = request.app.state.registries
    out: dict = {}
    # health
    try:
        from ...cli.doctor import DoctorFirstClass

        report = DoctorFirstClass().run()
        out["health_score"] = report.score
        out["health_checks"] = [
            {"item": c.item_id, "status": c.status} for c in report.checks
        ]
    except Exception as exc:  # noqa: BLE001 — không crash khi thiếu component
        out["health_score"] = 0
        out["health_error"] = str(exc)
    # slo
    try:
        from ...observability.slo import SloEngine

        engine = SloEngine()
        metrics = engine.metrics_from_runtime(request.app.state.kernel)
        slo_report = engine.check(metrics)
        out["slo_release_ready"] = slo_report.release_ready
        out["slo_failures"] = [r.slo_id for r in slo_report.failures]
    except Exception as exc:  # noqa: BLE001
        out["slo_release_ready"] = False
        out["slo_error"] = str(exc)
    # security
    try:
        from ...security import SecurityChecker

        sec = SecurityChecker().run()
        out["security_blocking"] = sec.blocking
        out["security_failures"] = [i.id for i in sec.failures]
    except Exception as exc:  # noqa: BLE001
        out["security_blocking"] = True
        out["security_error"] = str(exc)
    # contract
    try:
        from ...contracts.check import ContractChecker

        contract = ContractChecker().check_all()
        out["contract_breaking"] = contract.breaking_count
        out["contract_warnings"] = contract.warning_count
    except Exception as exc:  # noqa: BLE001
        out["contract_breaking"] = -1
        out["contract_error"] = str(exc)
    return {"data": out}


@router.get("/m10/timeline")
def timeline(request: Request, limit: int = 50) -> dict:
    """Execution trace (goal→plan→agent→capability→tool→result→evaluation).

    Nguồn: MetricsService (workflow rows) + EventBus audit (TOOL/ARTIFACT/GOAL).
    DB rỗng → [] (không crash).
    """
    regs = request.app.state.registries
    steps: list[dict] = []
    try:
        metrics_svc = regs["observability"]["metrics"]
        rows = metrics_svc.recent(limit=min(limit, 200))
        seq = 0
        for row in rows:
            execution_id = row.get("execution_id") or "-"
            steps.append({
                "seq": seq, "type": "plan",
                "label": f"plan:{row.get('name') or execution_id}",
                "execution_id": execution_id,
                "ts": row.get("started_at", ""),
            })
            seq += 1
            if row.get("duration_ms") is not None:
                steps.append({
                    "seq": seq, "type": "result",
                    "label": f"result:{row.get('duration_ms'):.0f}ms",
                    "execution_id": execution_id, "ts": "",
                })
                seq += 1
    except Exception:  # noqa: BLE001
        pass
    # tool steps từ metrics (category tool)
    try:
        from ...observability.metrics import MetricsService as _MS

        metrics_svc = regs["observability"]["metrics"]
        for row in metrics_svc.recent(limit=min(limit * 2, 400)):
            if row.get("category") == "tool":
                steps.append({
                    "seq": seq, "type": "tool",
                    "label": f"tool:{row.get('name') or row.get('node_id') or '-'}",
                    "execution_id": row.get("execution_id") or "-", "ts": "",
                })
                seq += 1
    except Exception:  # noqa: BLE001
        pass
    steps.sort(key=lambda s: s["seq"])
    return {"data": steps[:limit * 4]}
