# Critique-1 — TASK-031 (spec v1)

**Critic**: orchestrator tự phản biện (critic subagent không phản hồi — ghi nhận, resolve độc lập)

## P1 (blocker)
- **C1-01 — FakeTool semantics chưa chốt**: §3.5 FakeTool "behavior: dict" mơ hồ — node "capability:X" chạy qua FakeTool nào? Chốt: `SimulationRunner` tự dựng FakeTool theo tên (`tool:{capability}`) với behavior mặc định `{"ok": True}`, FaultInjector áp dụng theo `fault.target` (match "tool.{capability}" hoặc "resource" khi target=resource áp lên delay/queue). Bổ sung §3.5.
- **C1-02 — Fault "model" target không có node model mặc định**: nếu required_capabilities rỗng, plan không có node "model" → fault target model không bao giờ inject → test fault sẽ fail giả. Chốt: plan mặc định thêm node `model` khi scenario.faults có target "model" (hoặc luôn thêm node "model" đầu tiên — deterministic).
- **C1-03 — `_HARNESS_ALLOWED_EXTERNAL` cần `os`?** scenarios.py dùng Path — không cần os. Nhưng `load` file path cần đọc file: `Path.read_text` OK. Không cần os. Đảm bảo không import os.
- **C1-04 — Metrics deterministic**: SimulationOutcome.metrics chỉ counts (nodes, tool_calls, faults, recovery) — không duration/timestamp (pattern R3-7 TASK-030). Ghi rõ.

## P2 (major)
- **C2-01 — `expect.policy` default**: ExpectedResult.policy None → chưa chốt so sánh. Chốt: policy resolved phải == expect.policy; nếu expect.policy None → bỏ qua so sánh policy (matches không có key policy). Nhưng scenario deny test cần expect.policy="deny" tường minh.
- **C2-02 — no_policy_bypass semantics**: khi policy=deny, tool_calls phải rỗng — chốt runner assert (không raise, ghi match false).
- **C2-03 — verification dict so khớp thế nào**: §3.5 bước 7 "scenario.verification dict so khớp literal" mơ hồ. Chốt: chỉ 2 key chuẩn `tests_pass`/`no_policy_bypass` (bool) trong `verification` của ExpectedResult (không phải Scenario.verification — đang trùng). Sửa contracts: bỏ `Scenario.verification`, giữ trong ExpectedResult. Fault recovery → tests_pass true; nếu recovery thất bại → tests_pass false.
- **C2-04 — retries semantics**: Fault.params.retries — "số lần thử lại sau lần đầu" (retries=1 → 2 lần gọi tổng). Chốt wording: `attempts = retries + 1`.
- **C2-05 — TestHarness strict=False**: không raise nhưng outcome vẫn MISMATCH — persist "warning". OK, nhưng summary phải rõ. Chốt summary prefix.
- **C2-06 — get_outcome lưu gì**: compact outcome (không tool_calls đầy đủ?) — tool_calls có thể lớn; chốt lưu counts + matches + faults + recovery (cắt tool_calls). Đảm bảo replay-ish cho evaluation sau này (TASK-032 dùng trajectory → cần tool_calls!). Chốt: lưu tool_calls tối đa 100 entries (deterministic cap).
- **C2-07 — Loader yaml unsafe**: PyYAML `safe_load` bắt buộc (không full_load). Ghi rõ.

## P3 (minor)
- **C3-01 — SimulationStatus ERROR vs MISMATCH**: ERROR = fault không recover được / runner exception; MISMATCH = expectation mismatch. Test phân biệt.
- **C3-02 — FakeRuntime default keyword map**: chốt 6+ mappings deterministic (review→coding, write→writing, test→testing, plan→planning, summarize→writing, other→general) — agent map: coding→coder, testing→test-runner? PLAN: coder agent tồn tại (test_coder_assistant). Dùng "coder" cho testing luôn? Chốt: coding→coder, testing→test-runner (có test file?), viết: writer→writer, planning→generalist, general→generalist. Kiểm tra agent names hiện có — coder assistant tồn tại; giữ map đơn giản: coding/testing→coder, writing→writer, khác→generalist.
- **C3-03 — tag/tags**: Scenario.tags list[str] default [].
- **C3-04 — load_many yaml list**: yaml file có thể là list trực tiếp hoặc `scenarios:` key — hỗ trợ cả 2.
- **C3-05 — FaultInjector next_for trả fault một lần cho mỗi lần gọi target** — dùng bộ đếm; thread-safe không cần (simulation đơn luồng).
- **C3-06 — SimulationRunner không cần state service** — outcome do TestHarness persist. Runner thuần.
