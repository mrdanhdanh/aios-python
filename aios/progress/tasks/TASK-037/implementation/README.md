# TASK-037 — E3 Distributed Runtime (M7) — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `enterprise/`
> package (single source of truth), not duplicated here.

## Source of truth
- `backend/src/aios_core/enterprise/runtime.py`
- `backend/src/aios_core/enterprise/contracts.py` (RuntimeNodeInfo, RoutingCriteria)

## Key classes / functions
- `NodeRegistry` (thread-safe register/deregister/get/list/healthy)
- `RuntimeRouter` — deterministic selection: health → `tenant_class` gate (**INV-029 Control Plane Isolation**) → region → capability → capacity → cost → id
- `RuntimeRouter.check_isolation(node_id, tenant_class)` — explicit INV-029 check

## Verification
- `pytest tests/test_enterprise.py` (runtime tests) + `tests/test_architecture.py::test_inv029_control_plane_isolation_router`
- Architecture invariant: `enterprise/` only imports intra-package + pydantic/stdlib.
