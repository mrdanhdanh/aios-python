# TASK-025 — Test Results (Model Router)

**Ngày**: 2026-08-14 | **Runner**: pytest (backend/.venv)

## Kết quả tổng
- **Full suite**: `949 passed, 0 failed` (baseline 896 → +53 test mới)
- **Coverage**: 95.13% (threshold 80% cứng — pass)
- **Arch tests**: 26/26 pass (gồm `test_inv_router_import_allowlist` + `test_inv013_no_god_object` + `test_inv013_selection_via_router_only` mới)

## Test mới (53)
| File | Số test | Nội dung |
|------|---------|----------|
| `tests/test_model_router.py` | 48 | capability (12 field, forbid, default provider parse), registry capability API (roundtrip/unknown/duck-typed/overwrite), policy (parse PLAN 4 policies, fail-fast, balanced reserved, default validate), cost (estimate/quality/latency), availability (flag tĩnh), selector (cheap C1-01 số liệu, fast/quality/local/balanced, tie-break, unavailable, deterministic), fallback (excluded/health/rule/all), health (4 trạng thái transition, success reset, cumulative, snapshot sorted), router (select policy, RouterError, chat fallback chain, rate-limit, all fail, max_attempts, offline calls==0), integration (config yaml, env override scalar + dict, typo models, kernel wiring), INV-013 behavioral |
| `tests/test_architecture.py` | +3 | allow-list router/ (R2-1 threading), no_god_object (6 module + không logic cost + không đảo chiều), selection_via_router_only (3 exemption: runtime_kernel/api.wiring/root) |
| `tests/test_runtime_kernel.py` | +1 | `test_model_router_wired` (resolve + select offline) |
| `tests/test_models.py` | (cũ pass) | register 2 tham số backward compatible ✓ |

## Kiểm chứng AC (11/11)
- **AC1** ✅ ModelCapability 12 field PLAN §8.1 + contracts extra=forbid; ValidationError đúng
- **AC2** ✅ Registry capability API additive; duck-typed gọi 1 lần; register cũ không đổi
- **AC3** ✅ Routing Policy fail-fast; balanced reserved; default unknown → ValidationError
- **AC4** ✅ CostEstimator số liệu chính xác (quality 0.85, estimate 0.00075)
- **AC5** ✅ AvailabilityChecker flag tĩnh — không gọi is_available (C2-05)
- **AC6** ✅ Selector: cheap 0.005/5.0/20.0 → 1e-5/0.01/0.04 (C1-01); tie-break name asc; deterministic
- **AC7** ✅ Fallback re-filter rule + health + excluded (defense-in-depth)
- **AC8** ✅ Health 4 trạng thái + cumulative failures (C2-03)
- **AC9** ✅ Router: chat fallback chain timeout + rate-limit (C1-02); max_attempts=1; offline calls==0
- **AC10** ✅ Wiring: config.yaml routing + env override + kernel resolve; 949 pass / 95.13%
- **AC11** ✅ Architecture: 3 arch test mới pass; additive only (base/mock/openai/ollama không đổi)

## Ghi chú / Deviations
1. **Floating point**: `quality_score` round 6 — `0.3+0.3+0.15+0.15 = 0.89999...` < 0.9 → reject nhầm; fix bằng round.
2. **BOM removal**: `knowledge/chunks.py` + `knowledge/knowledge.py` có UTF-8 BOM → ast.parse fail khi scan toàn SRC_ROOT (test_inv013_selection_via_router_only) — bỏ BOM (encoding only, git diff xác nhận).
3. **no_god_object**: router.py import policy qua `.contracts` (policy.py là alias) — test chấp nhận cả 2 nguồn.
4. **register_capability trong wiring**: bỏ (register() đã set default capability availability=True — tránh warning overwrite).
5. **test config.yaml**: dùng `AIOS_CONFIG_PATH` trỏ file repo thật (monkeypatch.chdir(tmp) sẽ không thấy config.yaml).

## Kết luận
- [x] Tất cả 11 AC pass
- [x] Full suite 949 pass, coverage 95.13%
- [x] Deterministic verified (offline, tie-break, 2 lần chạy)
