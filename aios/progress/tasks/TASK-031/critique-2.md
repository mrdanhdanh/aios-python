# Critique-2 — TASK-031 (spec v2)

**Critic**: orchestrator tự phản biện vòng 2 (độc lập với vòng 1 — ghi nhận)

## P1 (blocker)
- **P1-01 — Runner `apply` resource fault vô nghĩa**: §3.5 bước 4 "resource → áp lên delay/queue trước tool call" — chưa chốt thứ tự/ý nghĩa. Chốt: target "resource" áp lên NODE model đầu tiên (như EXHAUSTED trước node đầu) — deterministic: fault resource inject tại node đầu tiên của plan (model), ghi "queued" + retry; nếu attempts hết → ERROR. Bỏ khái niệm "delay/queue" mơ hồ.
- **P1-02 — `expect.policy=None` nhưng check_policy default "allow"**: Scenario không khai expect.policy → so sánh bỏ qua ✓. NHƯNG nếu runtime policy deny (inject fake) mà expect.policy=None → runner vẫn BLOCKED (bước 2) nhưng matches không có key policy → status? BLOCKED không phải MISMATCH. Chốt: khi policy deny: nếu expect.policy == "deny" → SUCCESS (BLOCKED nhưng expected — đổi status SUCCESS với summary "blocked-as-expected"); nếu expect.policy == "allow" → MISMATCH; nếu None → MISMATCH (vì scenario không khai mà runtime deny = lệch giả định). Loại bỏ status BLOCKED khỏi outcome? Giữ enum nhưng runner chỉ trả SUCCESS/MISMATCH/ERROR + verification.no_policy_bypass + summary ghi blocked — đơn giản hóa test.
- **P1-03 — FailFast: faults trong node giữa chừng**: node 2 fault không recover → raise → ERROR, nhưng node 1 đã chạy — executed_nodes phải ghi phần đã chạy. Chốt: executed_nodes append trước khi chạy mỗi node (attempt đầu), tool_calls ghi mọi attempt (kể cả fail). Đảm bảo replay/evidence đủ.

## P2 (major)
- **P2-01 — `SimulationRunner(runtime)` vs TestHarness ctx.config runners**: wiring runtime_kernel dùng FakeRuntime default — user scenario không inject được intent map. Acceptable v1 (deterministic) + TestHarness cho phép `ctx.config["runtime"]` override (unit test dùng). Ghi rõ.
- **P2-02 — `testing` state key conflict**: H1 runner persist keys run/result/artifacts; H2 dùng "verification"; H3 dùng "testing" — không xung đột ✓. Nhưng get_outcome phải đọc state[run_id]["testing"] — nếu chạy qua H1 runner, key "testing" persist trong run() hook (trước verify) — sống sót như H2 ✓. Xác nhận lại pattern.
- **P2-03 — tests_pass khi có fault nhưng recovery thành công**: tests_pass = recovery_events không rỗng — nhưng nếu fault target tool.python FAILURE → fallback result ok=False → node output ok=False → tests_pass nên False? Chốt: tests_pass = (mọi node output ok) ∧ (fault có recovery thành công). FAILURE fault với fallback ok=False → tests_pass False → TestHarness strict → FAIL. Đúng nghĩa "fault recover nhưng kết quả xấu vẫn fail".
- **P2-04 — strict=False chỉ warning**: summary prefix "WARNING:" — nhưng verify không raise → H1 run COMPLETED với verdict warning. OK — chốt summary + state lưu strict flag.
- **P2-05 — Scenario.environment mode**: validate environment.get("mode") == "simulation" (hoặc "live" bị từ chối v1 — ScenarioError).

## P3 (minor)
- **P3-01 — `level` default WORKFLOW — OK**; load_many preserve order.
- **P3-02 — Fault params dùng chung schema: attempts ghi rõ `retries` default từ TestingSettings.default_retries** khi params không có.
- **P3-03 — Tool call dict shape**: {node, tool, input (request snippet), ok, status, attempt}. Deterministic.
- **P3-04 — node "model" output**: {"ok": True, "kind": "model"} — không gọi LLM thật.
- **P3-05 — TestHarness.get_outcome trả SimulationOutcome đầy đủ (reconstruct) hay dict?** Chốt: trả dict (compact lưu trữ) — không cần reconstruct model.
- **P3-06 — Arch INV-020c literal `TestError(`** — testing.py phải raise TestError — đảm bảo import + raise.
