# Critique vòng 1 — TASK-025 (Model Router)

**Critic**: subagent critic | **Ngày**: 2026-08-14 | **Spec phản biện**: v1

## Đánh giá chung
Spec chặt chẽ về kiến trúc (INV-013 2 lớp, allow-list, No God Object, additive-only), bám PLAN §7-10/§22-23 tốt. Kiểm chứng code thật: baseline 896/95.21% ✓, doctor không import ModelRegistry ✓, CLI không import ✓. 2 P1 (số học test sai; thiếu error rate-limit) + 8 P2 + 5 P3.

## P1 — Blockers

### C1-01: Test YC-6 "cheap → chỉ cheap-m qua" sai số học với canonical 1000/1000
- estimate = cost_rate/500; cheap-m 0.005→1e-5, mid-m 0.05→1e-4, exp-m 0.5→1e-3 — CẢ BA ≤ max_cost 0.01 → test fail.
- **Resolution**: sửa số liệu: cheap-m cost_rate 0.005 / mid-m 5.0 / exp-m 20.0 → estimate 1e-5 / 0.01 / 0.04; chốt so sánh `≤` (mid-m == max_cost → qua); ghi chú canonical 1000/1000 là fallback (budget chính xác khi request truyền tokens — TASK-024), thêm test tính toán lại cho cả 2.

### C1-02: Chain fallback PLAN §9 có "rate limit" nhưng không có ModelRateLimitError
- **Resolution**: thêm `ModelRateLimitError(ModelError)` vào `models/errors.py` (additive) + test fallback khi provider raise rate-limit.

## P2 — Major
- **C2-01**: Exemption INV-013 sai — `observability.doctor` KHÔNG import ModelRegistry (grep thật). → **Resolution**: exemption = {`aios_core.kernel.runtime_kernel`, `aios_core.api.wiring`} duy nhất; bỏ doctor; scan dùng `module_imports` 2 chiều (import trần `aios_core.models` cũng bị chặn — phải import submodule).
- **C2-02**: `RouteDecision.created_at` + test determinism cần clock injectable. → **Resolution**: `ModelRouter.__init__` nhận `now: Callable[[], datetime]` (default `datetime.now(timezone.utc)`) — dùng cho created_at.
- **C2-03**: DEGRADED dead state + transition không đầy đủ. → **Resolution**: table: `failures==1 → DEGRADED`, `2 → COOLDOWN`, `≥ max_failures → DISABLED`; `record_success → OK + reset failures`; cooldown hết hạn → OK (lazy, KHÔNG reset failures cumulative); test phủ 4 trạng thái.
- **C2-04**: `ModelsSettings` thiếu `extra="forbid"` → typo nested silent ignore. → **Resolution**: thêm `extra="forbid"` cho ModelsSettings (config.yaml hiện chỉ có `default` — safe) + test typo key trong block models → ValidationError.
- **C2-05**: default path `register()` gọi `model.is_available()` (Ollama = HTTP) — trái offline-first. → **Resolution**: default path KHÔNG gọi is_available — `ModelCapability.default(availability=True)`; unavailable phải register_capability tường minh; update test.
- **C2-06**: `max_attempts=3` ngầm cắt chain. → **Resolution**: mặc định `max_attempts=None` → thử toàn bộ chain; max_attempts là cap an toàn; test chain > cap chốt hành vi cắt.
- **C2-07**: `RoutingPolicy.default` không validate tại parse. → **Resolution**: model_validator: `default ∈ {"balanced"} ∪ policies.keys()` → ValidationError.
- **C2-08**: Ai gộp rejected "health"? → **Resolution**: router chạy health check TRƯỚC selector; gom `rejected(name, "health")`; `RouteDecision.rejected = health_rejected + selector_result.rejected`.

## P3 — Minor
- **C3-01**: Bỏ `now` param khỏi `ModelSelector.select` (health ở router).
- **C3-02**: `FallbackResolver.next()` nhận RAW candidates và tự re-filter mỗi hop (defense-in-depth thật; test rule cấm → None đúng).
- **C3-03**: `chat()` tạo RouteDecision MỚI (copy + update chain/model) — không mutate decision từ select().
- **C3-04**: `models/__init__.py` thứ tự import: base → errors → capability → registry → router (tránh cycle).
- **C3-05**: `register_capability` overwrite — caller chịu trách nhiệm đồng bộ model↔capability (không tự validate).

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C1-01, C1-02 (P1) + C2-01..C2-08 (P2) + P3 → spec v2, rồi critique vòng 2.
