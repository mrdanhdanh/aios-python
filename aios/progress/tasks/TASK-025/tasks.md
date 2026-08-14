# TASK-025 — Tasks Breakdown

**Trạng thái**: spec v3 đã qua critique ×2 (15 + 7 vấn đề resolved) — sẵn sàng review → implement

## Checklist

- [ ] **T1. ModelCapability** — `models/capability.py`: 12 field PLAN §8.1, extra=forbid, field_validator (cost ≥ 0, context_window ≥ 0), `default(model_id, availability=True)` — provider từ split(":")
- [ ] **T2. Registry capability API** — `models/registry.py` additive: `register(name, model, capability=None)` (duck-typed `model.capability()` → `ModelCapability.default` — KHÔNG gọi is_available C2-05), `register_capability` (overwrite warn), `capability` (unknown → ModelError), `capabilities()` sorted
- [ ] **T3. Errors** — `models/errors.py`: `RouterError(ModelError)` + `ModelRateLimitError(ModelError)` (C1-02)
- [ ] **T4. Contracts** — `models/router/contracts.py`: `PolicyRule` (max_cost/max_latency_ms/min_quality/providers), `RoutingPolicy` (+model_validator default C2-07, balanced reserved), `RouteRequest`, `RouteDecision`, `RejectedCandidate`, `HealthStatus` (4 state), `HealthConfig`, `ModelRouterConfig` (max_attempts=None C2-06)
- [ ] **T5. Policy + Cost + Availability** — `policy.py` (from_settings), `cost.py` (estimate_cost = cost_rate/500 canonical; quality_score 0.3/0.3/0.15/0.15/0.1; latency_ms fast=1000/medium=5000/slow=15000; cost_score COST_SCALE 0.1; balanced_score 0.5/0.3/0.2), `availability.py` (flag tĩnh — không gọi is_available)
- [ ] **T6. ModelHealth** — `health.py`: state machine 4 trạng thái (1 fail → DEGRADED, 2 → COOLDOWN, ≥3 → DISABLED; success → OK + reset; cooldown hết hạn → OK lazy KHÔNG reset failures cumulative), clock injectable, snapshot sorted, lock
- [ ] **T7. ModelSelector** — `selector.py`: filter (cost ≤, latency ≤, quality ≥, providers; unavailable reject) → rank theo policy (cheap cost asc / fast latency asc / quality desc / local+balanced balanced desc) → pick + tie-break name asc; `SelectorResult` (rejected + ranking)
- [ ] **T8. FallbackResolver** — `fallback.py`: `next(all_candidates_raw, rule, excluded)` — re-filter rule + health + excluded (C2-02 v2)
- [ ] **T9. ModelRouter** — `router.py` (chỉ điều phối): `__init__` (6 module DI + now C2-02 v1), `select` (policy resolve → health check → availability → selector; rejected gom C2-08; candidates_considered semantics C2-04 v2), `chat` (loop fallback, max_attempts cap, copy decision C3-03, rate-limit C1-02, last_decision lock)
- [ ] **T10. Config + wiring** — `config.py` (RoutingRuleSettings/RoutingSettings mirror extra=forbid; ModelsSettings extra="forbid" C2-04 v1; routing field), `config.yaml` (models.routing 4 policy), `runtime_kernel.py` (register_capability mock + register_instance ModelRouter), `models/__init__.py` re-export (order base→errors→capability→registry→router C3-04)
- [ ] **T11. Unit tests** — `tests/test_model_router.py`: contracts, registry capability, policy validate (fail-fast, balanced reserved, default unknown), cost số liệu chính xác, health 4 trạng thái + cumulative, selector (cheap số liệu C1-01, fast/quality/local/balanced, tie-break), fallback (excluded/health/rule cấm), router (select policy, RouterError, chat fallback chain timeout + rate-limit, max_attempts=1, mock.calls==0)
- [ ] **T12. Arch tests** — `test_architecture.py`: `test_inv_router_import_allowlist` + `test_inv013_no_god_object` + `test_inv013_selection_via_router_only` (3 exemption: runtime_kernel, api.wiring, root aios_core — C2-01 v2); `test_models.py` (registry capability API)
- [ ] **T13. Config + wiring tests** — `test_config.py` (routing parse + env override scalar + dict nested C2-03 v2 + typo models key → ValidationError C2-04 v1), `test_runtime_kernel.py` (resolve ModelRouter + select offline)
- [ ] **T14. Full suite + coverage** — pytest toàn bộ, coverage ≥ 80% cứng (95% mục tiêu); git diff verify additive only
- [ ] **T15. test.md + evaluation.md** — đối chiếu 11 AC

## Bước kế tiếp
Review → implement → test → evaluate → commit
