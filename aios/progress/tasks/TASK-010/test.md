# Test — TASK-010

## Kết quả thực tế

| Hạng mục | Kết quả |
|----------|---------|
| Kết quả | **402 passed** (56 mới + 346 baseline) |
| Coverage | **94.96%** (ngưỡng 80%) |
| Git sạch | ✅ |

Test mới (7 file): test_normalizer (6), test_rule_engine (7), test_workflow_matcher (6), test_planner (8), test_orchestrator (9), test_agent_selector (2) + test_import.

## Lỗi phát hiện + fix (2)
1. **"crud generator" bị rule "crud" bắt trước** (resolved_by="rule") — đúng thiết kế; test matcher path dùng "please make a generator tool" (token "generator" không nằm rule)
2. **BrokenModel raise RuntimeError** — Planner chỉ catch ModelError (đúng spec) → fake model phải raise ModelError

## Đối chiếu AC (10 AC)
**10/10 PASS** — AC1 normalizer 6 case; AC2 rule 7 mẫu + word-boundary + priority/longest/tie; AC3 matcher macro/full/token/stopword; AC4 planner stub/thật/timeout/parse-fail/calls; AC5 pipeline 6 case (rule+workflow_name, normalizer, matcher, planner); AC6 **100 requests → llm_calls == 10 (offline-first 90%)**; AC7 selector; AC8 system knowledge (plural mapping, graph catch); AC9 imports + coverage; AC10 offline.

## Kết luận
- [x] **TẤT CẢ PASS (10/10 AC)** — sẵn sàng đánh giá cuối.
