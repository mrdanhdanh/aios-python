# Critique vòng 2 — TASK-089 (M13-P0: Behavioral Conformance)

> Phản biện spec v2 bởi critic agent (độc lập) — 2026-08-17
> Đối chiếu code thật: `simulation.py`, `contracts.py`, `faults.py`, `scenarios.py`, `gate.py`, `benchmark/contracts.py`, `runner.py`, `registry.py`, `benchmark.py`, `runtime_kernel.py`, `cli.py`, `test_harness_testing.py`, `test_harness_benchmark.py`, PLAN §M13.
> **Mức sẵn sàng v2: 3.5/5** — resolution vòng 1 đa số đúng/khả thi; 2 P1 mới (gate dedup + repeat_consistent) + 5 P2 + 10 P3. Tất cả đã RESOLVED (spec v3).

## Kiểm tra resolution vòng 1 (kết quả)

- **P1-2 (Fault.recoverable + next_for)**: ✅ KHẢ THI — trace qua code thật: default True giữ hành vi cũ, không phá `test_timeout_fault_recovers`/`test_inject_once_then_none`; recoverable=False → apply raise mọi lần → retry fail → SimulationError → ERROR reachable.
- **P1-3 (gate chỉ expose)**: ⚠️ hợp lý về scope nhưng phát hiện **P1-1 mới** (gate dedup) + cần ghi deviation vào PLAN (**P2-5 mới**).
- **P1-4 (repeat_samples)**: ⚠️ tautology với runner thuần (chấp nhận — giá trị thực khi swap runner thật) nhưng mâu thuẫn `repeat_consistent` (**P1-2 mới**).
- **P1-5 (scenarios.load)**: ✅ ĐÚNG — load nhận dict/str/Path, yaml+json, validate input.request + mode=simulation.
- **P1-6 (group harness)**: ✅ KHÔNG xung đột — pattern nested subcommand có sẵn (stop/compat).
- **AC13 (expect sai → MISMATCH)**: ⚠️ khả thi nhưng có bẫy: `expect.tests_pass`/`no_policy_bypass` KHÔNG được runner so sánh (**P2-4 mới**).
- **AC11 (recoverable=False → ERROR)**: ✅ KHẢ THI.
- **AC9 (wiring)**: ⚠️ thiếu test verify raise + report không persist (**P2-1, P2-2 mới**).
- **Q9 (Scenario extra=forbid)**: ✅ KHỚP — CLI build dict scenario.model_dump(mode="json").

## P1 — Phải sửa (mới)

### P1-1 — Regression gate dedup: N iteration sụp về 1 RunResult
- **Vấn đề**: `RegressionGate.evaluate` dedup theo scenario_id (`new_by_id = {r.scenario_id: r}`) → N RunResult cùng id chỉ 1 sống sót (iteration cuối thắng) → gate không xác định. `--save-baseline` cùng vấn đề.
- **RESOLVED**: định nghĩa aggregation rõ trong §3.2 step 4: gộp N iteration → 1 RunResult/scenario — `quality` = tỷ lệ iteration SUCCESS, `failed` = có bất kỳ iteration fail, `policy_violations` = số iteration có policy bypass, cost/tokens/latency = 0. Dùng chung cho `--save-baseline`.

### P1-2 — `repeat_consistent` mâu thuẫn với `repeat_samples`
- **Vấn đề**: `repeat_ok` chỉ tính cho iteration ≤ repeat_samples (3) nhưng `repeat_consistent` = "mọi iteration có repeat_ok=True" → iteration 4..N không được định nghĩa → AC5 fail hoặc hiểu nhầm.
- **RESOLVED**: `repeat_ok: bool | None = None` (None = không repeat); `repeat_consistent` = mọi iteration **được repeat** đều repeat_ok=True; cap `repeat_samples = min(repeat_samples, iterations)` (P3-3).

## P2 — Nên sửa

### P2-1 — Thiếu AC verify fail-closed + `--no-strict`
- **RESOLVED**: thêm AC17: (a) strict=True + report FAIL/ERROR → `BehavioralConformanceError` raise → HarnessRunStatus.FAILED; (b) strict=False → không raise, run COMPLETED.

### P2-2 — Report không được persist
- **Vấn đề**: HarnessRunner chỉ persist run/result/artifacts, không persist payload → report mất sau run (khác TestHarness/BenchmarkHarness có get_outcome/get_report).
- **RESOLVED**: thêm `state_service` vào constructor + `_persist(ctx, report, strict)` (pattern TestHarness) + `get_report(run_id)`; wiring truyền `container.resolve(StateService)`.

### P2-3 — `fault_iterations` out-of-range không được xử lý
- **RESOLVED**: engine raise `BehavioralConformanceError` nếu fault_iterations có index > iterations_total (fail-fast) — không fail im lặng.

### P2-4 — `expect.tests_pass`/`no_policy_bypass` không được runner kiểm tra (bẫy AC13)
- **RESOLVED**: ghi rõ AC13 dùng mismatch loại intent/agent/policy/required_capabilities (những loại runner thực sự kiểm tra); ghi nhận limitation "negative test chưa được runner hỗ trợ (thuộc TASK-031, ngoài scope)".

### P2-5 — PLAN.md cần ghi chú deviation "gate-as-blocker defer M14"
- **RESOLVED**: ghi chú vào PLAN §M13 P0: "v1 gate chỉ expose (tính + finding), gate-as-blocker thuộc M14 (Certified Baseline)" — cập nhật PLAN khi implement.

## P3 — Góp ý (đã tích hợp)

- **P3-1** Out liệt kê FaultInjector (mở rộng tối thiểu) cho nhất quán → RESOLVED
- **P3-2** bỏ "config.yaml" khỏi P2-4 resolution (chỉ CLI) → RESOLVED
- **P3-3** cap repeat_samples = min(repeat_samples, iterations) → RESOLVED (trong P1-2)
- **P3-4** deterministic vacuous khi mọi iteration fault → RESOLVED: ghi chú deterministic chỉ có nghĩa khi có nhóm không-fault
- **P3-5** thêm `harness/behavioral/errors.py` (BehavioralConformanceError) → RESOLVED
- **P3-6** `recovered` cho iteration không-fault → RESOLVED: False (không fault → không recover)
- **P3-7** metrics keys cụ thể → RESOLVED: iterations_total, faults_injected_total, recovery_events_total, repeat_runs, mismatch_count, error_count
- **P3-8** ghi chú JSON size stress=10k → RESOLVED: ghi chú trong CLI section
- **P3-9** `--faults` phải list → RESOLVED: CLI kiểm tra isinstance(list) → parser.error
- **P3-10** AC9 nói rõ HarnessRunStatus.FAILED khi verify raise → RESOLVED (trong P2-1)

## Kết luận

- [x] Cần sửa trước khi implement: P1-1, P1-2 (bắt buộc) + P2-1..P2-5 (nên sửa) — tất cả đã RESOLVED → spec v3.
- Resolution vòng 1 đúng và khả thi (fault-inject trace qua code thật không phá test cũ; scenarios.load/CLI pattern khớp code hiện có).