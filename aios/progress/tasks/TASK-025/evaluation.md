# TASK-025 — Evaluation (Model Router)

**Ngày**: 2026-08-14 | **Trạng thái**: DONE ✅

## Đối chiếu tiêu chí chấp nhận (11/11 AC pass — xem test.md)
AC1..AC11 đều pass với bằng chứng test cụ thể (test_model_router.py 48 test + 3 arch test + 1 wiring test).

## Đánh giá so với PLAN.md §M5-7..10
- **Model Router** (§7): trả lời "Request này nên dùng model nào?" — KHÁC ModelRegistry ("model nào tồn tại"); chỉ chạy khi request cần model (nối pipeline = TASK-026)
- **Routing Policy** (§8): yaml 4 policy PLAN (cheap/fast/quality/local) + balanced default; fail-fast validation (field lạ/balanced reserved/default unknown → ValidationError)
- **Model Capability** (§8.1): 12 field đủ; **lưu ở registry** — không sửa ModelContract/provider (additive tuyệt đối)
- **Fallback** (§9): timeout/rate-limit/unavailable → chain; **tuân Policy** (FallbackResolver re-filter rule mỗi hop — defense-in-depth); ModelRateLimitError mới
- **No God Object** (§10): 6 module nhỏ (selector/policy/cost/availability/health/fallback) + router chỉ điều phối — arch assert 3 lớp
- **INV-013 Model Routing Policy**: behavioral (cheap → rẻ nhất; timeout → fallback đúng thứ tự; offline calls==0) + AST (selection_via_router_only — 3 exemption composition root)

## Bài học
1. **Floating point trong score**: 0.3+0.3+0.15+0.15 = 0.8999... → so sánh min_quality fail — luôn round() khi so sánh ngưỡng
2. **AST scan toàn repo gặp BOM**: chunks.py/knowledge.py có BOM từ trước — scan rộng (test_inv013_selection_via_router_only) phát hiện; bỏ BOM encoding-only
3. **Import path capability**: `capability.py` ở `models/` (không phải `models/router/`) — cost.py import `.capability` sai → `..capability`
4. **register() đã set default capability** — register_capability sau đó tạo warning overwrite thừa; wiring đơn giản hóa
5. **Config test với chdir**: load_settings() theo CWD — phải trỏ AIOS_CONFIG_PATH vào file repo thật

## Đề xuất cho task sau
- **TASK-026 Planning Engine**: inject ModelRouter instance (untyped — INV-005 rule A chặn orchestrator → models); planner có thể dùng router thay vì gọi model trực tiếp
- **L3 compression (TASK-024)**: router cung cấp context_window/cost — nối ở harness M6
- Observability M5 DoD: `RouteDecision` chứa sẵn model selected + fallback chain — metrics gắn sau

## Kết luận
- [x] ĐẠT spec (11/11 AC)
- [x] Không phá architecture (INV-013 3 lớp enforced, additive only)
- [x] Deterministic verified, coverage 95.13% (toàn suite 949 pass)
