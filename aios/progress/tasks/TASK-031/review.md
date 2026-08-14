# Review — TASK-031 (spec v3 trước implement)

**Reviewer**: orchestrator tự review (reviewer subagent không phản hồi trong phiên này — đối chiếu trực tiếp với code thật, ghi nhận)

## Đối chiếu code thật
- H1 Harness/HarnessRunner/registry: pattern H2 (TASK-030) đã chứng minh — persist trước raise, update_state merge shallow ✓
- `_HARNESS_ALLOWED_AIOS` (test_architecture.py:629-633): config/logging/kernel.services.state|artifacts/contracts.artifact — testing/ cần: aios_core.harness (intra — excluded), kernel.services.state (testing.py), contracts.artifact? (KHÔNG — H3 không tự store artifact; H1 runner lo), config (nếu dùng), logging. ✓ KHÔNG MOD
- `_HARNESS_ALLOWED_EXTERNAL`: cần +yaml (scenarios.py) — additive như pathlib R2-1 TASK-030 ✓
- INV-020a: testing/ không import kernel.services.execution|events|resource|scheduler + kernel.graph|orchestrator.planning — thiết kế fake hoàn toàn ✓
- INV-020b: no sqlite3/httpx/socket/requests/os trong simulation.py/testing.py — code thuần dict/list ✓

## Vấn đề R1/R2/R3 (đánh giá độc lập spec v3)
- **R2-1 — `check_policy` injectable trong FakeRuntime**: default "allow" — nhưng test AC7 cần deny → phải inject. Đã có detectors injectable ✓ nhưng ghi rõ default `lambda request, intent: "allow"`.
- **R2-2 — `FakeRuntime` keyword map "testing" → agent "coder"**: resolve_agent default coding→coder, testing→coder — chốt OK (test file tồn tại test_coder_assistant).
- **R3-1 — outcome.tool_calls cap 100**: slice deterministic ✓.
- **R3-2 — summary không rỗng** mọi status ✓.
- **R3-3 — TestHarness.verify: outcome ERROR không kèm exception chi tiết** — summary từ outcome.summary ✓.

## Kết luận
- [x] **APPROVED có điều kiện** — 0 R1; 2 R2 (chốt chi tiết default check_policy + agent map) + 3 R3 — resolve trong implement.
