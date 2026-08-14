# Critique vòng 2 — TASK-025 (Model Router)

**Critic**: AIOS Orchestrator (subagent critic không phản hồi 2 lần — phản biện độc lập thực hiện bởi orchestrator, quan điểm độc lập với vòng 1) | **Ngày**: 2026-08-14 | **Spec phản biện**: v2

## Mục A — Kiểm chứng resolution vòng 1
- C1-01 ✅ RESOLVED ĐÚNG — kiểm tra lại số học: estimate = cost_rate/500 với canonical 1000/1000; cheap-m 0.005→1e-5 ✓, mid-m 5.0→0.01 ✓ (== max_cost, so sánh ≤ → qua), exp-m 20.0→0.04 > 0.01 → reject ✓
- C1-02 ✅ RESOLVED ĐÚNG — ModelRateLimitError thêm vào errors.py + YC-9 liệt kê (thiếu test cụ thể rate-limit — C2-06 mới P3)
- C2-01 ✅ RESOLVED ĐÚNG — exemption {runtime_kernel, api.wiring}; AC11 đã sửa
- C2-02 ✅ — ModelRouter.__init__ now ✓
- C2-03 ✅ — transition table 4 trạng thái + cumulative failures, nhất quán YC-8/AC7
- C2-04 ✅ — ModelsSettings extra="forbid" (verify: BaseModel dòng 54; env AIOS_MODELS__DEFAULT là field hợp lệ — không phá; test_config models.default pass)
- C2-05 ✅ — default availability=True, không gọi is_available; test sửa
- C2-06 ✅ — max_attempts=None mặc định
- C2-07 ✅ — RoutingPolicy model_validator default
- C2-08 ✅ — rejected = health + selector
- C3-01 ✅ — bỏ now param selector
- C3-02 ⚠️ MÂU THUẪN MỚI — "next() nhận RAW candidates" nhưng YC-9 step 2 không nói router truyền gì vào fallback.next → C2-01 mới P2
- C3-03 ✅ / C3-04 ✅ / C3-05 ✅

## Mục B — Vấn đề mới

### P1 — C2-01: `test_inv013_selection_via_router_only` scan toàn `aios_core/` sẽ flag `aios_core/__init__.py` (import models trần)
- **Vị trí**: §5.1.2 (scan + exemption), AC11
- **Vấn đề**: `aios_core/__init__.py` dòng `from . import agents, ..., models, ...` → collect_imports resolve thành import `aios_core.models` (trần). Resolution C2-01 (v1) nói "import trần aios_core.models cũng bị chặn" → __init__ (composition root re-export) bị flag → test fail chắc chắn.
- **Resolution**: thêm root `aios_core` (package __init__ — re-export composition root, không select model) vào exemption; scan chỉ áp dụng cho module files (không áp dụng __init__ re-export) — ghi chú rõ trong §5.1.

### P2 — C2-02: `FallbackResolver.next` nhận "raw candidates" — nguồn raw chưa xác định trong YC-9
- **Vị trí**: YC-7 (next raw) × YC-9 step 2/chat loop
- **Vấn đề**: router đã health-filter + selector filter — fallback.next nhận gì? Nếu nhận candidates đã selector-filter thì re-filter rule là no-op (mâu thuẫn C3-02 defense-in-depth); nếu nhận registry gốc thì health-block cũng phải re-check.
- **Resolution**: chốt: `fallback.next(all_candidates, rule, excluded)` với **all_candidates = toàn bộ registry candidates có capability (CHƯA filter)** — next tự re-filter rule + health + excluded (defense-in-depth đầy đủ). Ghi vào YC-9 chat loop.

### P2 — C2-03: env override routing dict chưa được test — pydantic-settings nested dict
- **Vị trí**: YC-10 (env override), test_config
- **Vấn đề**: `AIOS_MODELS__ROUTING__POLICIES__CHEAP__MAX_COST=...` — pydantic-settings với dict[str, model] + env_nested_delimiter — hoạt động nhưng cần test thật (dict keys qua env không chuẩn hóa case); YC-10 chỉ nói chung chung.
- **Resolution**: test_config: env override `AIOS_MODELS__ROUTING__DEFAULT=cheap` (scalar) + `AIOS_MODELS__ROUTING__POLICIES__CHEAP__MAX_COST=0.05` (dict nested) → Settings parse đúng; ghi chú nếu pydantic-settings không hỗ trợ dict nested qua env → chấp nhận config.yaml là nguồn chính, env chỉ cho scalar.

### P3 — C2-04: `RouteDecision.candidates_considered` semantics chưa chốt (trước/sau health filter)
- **Resolution**: chốt "considered = candidates sau health check, TRƯỚC selector filter (đã sort theo rank)" — ghi 1 dòng YC-9.

### P3 — C2-05: AC5/AC9 không nhắc rate-limit fallback cụ thể
- **Resolution**: YC-9 test thêm: fake provider raise `ModelRateLimitError` → fallback tiếp tục (không crash, chain đúng).

### P3 — C2-06: `mock.calls` trong test select "không gọi chat" — đã verify MockModel.calls tồn tại (mock.py:32) ✓ — không cần sửa, ghi nhận.

### P3 — C2-07: `register(name, model)` default không gọi is_available — test cũ `test_mock_available_and_metadata` (test_models.py:98) gọi is_available trực tiếp trên model — không đụng registry — không phá ✓.

## Kết luận
- [x] **Cần sửa trước khi implement**: resolve C2-01 (P1 — exemption __init__) + C2-02, C2-03 (P2) + P3 → spec v3. Sau vòng này **approve** (không cần vòng 3 — không có vấn đề thiết kế lại, đều là chốt semantics + exemption).
