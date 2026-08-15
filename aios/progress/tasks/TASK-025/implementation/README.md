# TASK-025 — M5 Model Router — Implementation

> 8th hard-gate file (`implementation/`). Actual code lives in the `models/`
> package (single source of truth), not duplicated here. Bổ sung hồi tố 2026-08-15 khi đóng hard gate.

## Source of truth
- `backend/src/aios_core/models/capability.py` — 12 field model capability (PLAN §8.1)
- `backend/src/aios_core/models/registry.py` — +capability API (duck-typed, không gọi is_available)
- `backend/src/aios_core/models/errors.py` — `RouterError` + `ModelRateLimitError`
- `backend/src/aios_core/models/router/` — 8 file:
  - `contracts.py`, `policy.py` (fail-fast), `cost.py` (cost/latency/balanced), `selector.py` (filter→rank→pick + tie-break), `availability.py` (4 trạng thái cumulative), `fallback.py` (re-filter rule), `health.py` (ModelHealth), `router.py` (điều phối + chat fallback loop)
- `backend/src/aios_core/config.py` — `RoutingSettings` + `ModelsSettings` extra=forbid
- `backend/src/aios_core/kernel/runtime_kernel.py` — wiring

## Key behavior
- Routing policy: default balanced; policies cheap/fast/quality/local (deterministic filter)
- Fallback: re-filter theo rule (loại provider lỗi), tuân Policy — không tự ý đổi model
- Router KHÔNG God Object: Router chỉ điều phối (ModelSelector · RoutingPolicy · CostEstimator · AvailabilityChecker · FallbackResolver · ModelHealth)
- INV-013: model selection phải qua Routing Policy (arch test `selection_via_router_only`)

## Verification
- `pytest` full suite: **949 passed, coverage 95.13%, 11/11 AC** (xem `test.md`)
