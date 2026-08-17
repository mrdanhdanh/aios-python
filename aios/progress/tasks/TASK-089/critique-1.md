# Critique vòng 1 — TASK-089 (M13-P0: Behavioral Conformance)

> Phản biện spec v1 bởi critic agent (độc lập quan điểm) — 2026-08-17
> Đối chiếu code thật: `harness/testing/{simulation,contracts,faults}.py`, `harness/benchmark/{gate,contracts}.py`, `harness/{runner,registry,contracts}.py`, `harness/benchmark/benchmark.py`, `kernel/runtime_kernel.py`, `config.py`, `workflow/cli.py`, `harness/__init__.py`, `tests/test_harness_benchmark.py`, PLAN.md §M13.
> **Mức sẵn sàng v1: 2/5** — 6 P1 + 8 P2 + 9 P3. Tất cả đã RESOLVED (spec v2).

## P1 — Phải sửa (lỗ hổng thật)

### P1-1 — Status logic bỏ qua `outcome.status`: MISMATCH deterministic → PASS (false positive)
- **Vấn đề**: Status chỉ dựa trên ERROR/deterministic/evidence/replay. Scenario expectation sai → MISMATCH mọi iteration → deterministic=True → **PASS**. Behavioral conformance phải chứng minh hành vi **ĐÚNG**, không chỉ **ổn định**. Deterministic-but-wrong = PASS phá mục tiêu P0 + vi phạm tinh thần INV-035.
- **RESOLVED**: thêm điều kiện bắt buộc: mọi outcome không-fault phải `status == SUCCESS`; bất kỳ MISMATCH → `FAIL` + finding. Thêm AC13 (mới).

### P1-2 — ERROR status unreachable với SimulationRunner hiện tại → AC6/AC11 vacuous
- **Vấn đề**: Runner luôn recover (inject 1 lần/target → retry thành công) → nhánh `except` raise SimulationError là dead code → `SimulationStatus.ERROR` không xảy ra. AC6/AC11 không test được.
- **RESOLVED**: mở rộng tối thiểu, backward-compatible: thêm `Fault.recoverable: bool = True` (default True — hành vi cũ giữ nguyên); `FaultInjector.next_for` trả fault mọi lần nếu `recoverable=False` → apply raise mọi lần → runner retry fail → `SimulationError` → `SimulationStatus.ERROR`. Sửa ràng buộc Out: "KHÔNG sửa SimulationRunner/FaultInjector" → "chỉ mở rộng tối thiểu Fault.recoverable + FaultInjector.next_for (backward-compatible)".

### P1-3 — Regression gate vô nghĩa + mapping RunResult sai (false positive cho expected-deny)
- **Vấn đề**: (a) Runner deterministic → gate không thêm thông tin độc lập (chỉ block khi MISMATCH — lúc đó status đã FAIL). (b) `policy_violations = 1 nếu policy != "allow"` — expected-deny hợp lệ bị tính violation → gate block sai. Outcome đã có `verification.no_policy_bypass` (đúng cho expected-deny).
- **RESOLVED**: (a) gate **KHÔNG quyết định status v1** — chỉ tính + expose trong report (tái dùng RegressionGate); gate-as-blocker thuộc M14 (Certified Baseline, nhiều scenario + real metrics). (b) mapping đúng: `policy_violations = 0 if outcome.verification.get("no_policy_bypass") else 1`; `failed = outcome.status != SUCCESS`; `quality = 1.0 if SUCCESS else 0.0`.

### P1-4 — "Replay" mơ hồ, trùng tên `replay_verdict`, trùng chức năng `deterministic`
- **Vấn đề**: Replay = chạy lại scenario 1 lần → luôn True với runner thuần, trùng `deterministic`, nhân đôi chi phí (stress 10k → 20k). Tên gây nhầm với `replay_verdict` (tamper detection).
- **RESOLVED**: đổi tên `replay_ok` → `repeat_ok` (double-run check); **chỉ chạy cho subset** `repeat_samples: int = 3` (iteration đầu) — đủ chứng minh temporal determinism, không nhân đôi 10k. Ghi rõ: repeat ≠ `replay_verdict` (tamper detection thuộc P2 Meta-Harness TASK-091).

### P1-5 — Thiếu nguồn scenario: engine không build được Scenario từ scenario_id
- **Vấn đề**: `scenario_id` không đủ — thiếu input/expect. Không có scenario registry.
- **RESOLVED**: config mang full `Scenario` object (`ConformanceConfig.scenario: Scenario`); CLI nhận `--scenario-file <yaml/json>` → `scenarios.load()`; `scenario_id` lấy từ `scenario.id`. Thêm AC14 (resolve scenario từ file).

### P1-6 — CLI `aiagent harness conformance` không khớp CLI hiện có
- **Vấn đề**: cli.py KHÔNG có subcommand `harness`; `conformance` top-level đã dùng cho certification. `--faults <json>` parse inline không có precedent.
- **RESOLVED**: thêm subcommand group `harness` MỚI (pattern mới — mô tả rõ parser + dispatch + hàm `_harness_behavioral()`); lệnh `aiagent harness behavioral ...` (tránh nhầm `aiagent conformance` certification). JSON inline parse qua `json.loads` + try/except → `parser.error`.

## P2 — Nên sửa

### P2-1 — Thiếu AC temporal determinism cross-run
- **RESOLVED**: thêm AC15: chạy engine 2 lần cùng config → report giống hệt (trừ duration/run_id).

### P2-2 — `ConformanceIteration.duration_ms` mâu thuẫn C1-04 "không timing"
- **RESOLVED**: bỏ `duration_ms` khỏi iteration (metrics chỉ counts).

### P2-3 — `SOAK_MAX_ITERATIONS` trùng lặp + soak không thực sự soak
- **RESOLVED**: engine nhận cap qua constructor `soak_max_iterations: int = 10000` (không hardcode 2 nơi); ghi chú thành thật: soak v1 = loop-stability test (runner thuần không resource/timing — leak/latency thật thuộc M13.1).

### P2-4 — `ConformanceSettings` gần như thừa + wiring không rõ
- **RESOLVED**: bỏ `ConformanceSettings` khỏi config.py; engine nhận tham số constructor; config qua CLI/config.yaml.

### P2-5 — `fault_iterations` thiếu validation
- **RESOLVED**: thêm `field_validator` trong `ConformanceConfig`: index trong [1, iterations_total] (nếu biết), dedup, `fault_iterations` non-empty → `faults` phải non-empty.

### P2-6 — Memory: giữ full outcome cho stress=10k
- **RESOLVED**: aggregate streaming — iteration chỉ giữ summary (index, status, digest, repeat_ok, fault_injected, recovered); KHÔNG giữ full outcome. Deterministic so bằng digest.

### P2-7 — AC6 không test `fault_iterations` cụ thể
- **RESOLVED**: thêm test riêng: `fault_iterations=[k]` → chỉ iteration k có fault, các iteration khác deterministic.

### P2-8 — Namespace collision `harness/conformance/` vs `harness/certification/conformance.py`
- **RESOLVED**: đặt package `harness/behavioral/` (không trùng); class prefix `Behavioral*`; harness id="behavioral"; CLI `aiagent harness behavioral`.

## P3 — Góp ý

- **P3-1** seed dead config → **RESOLVED**: bỏ seed (runner không dùng PRNG); reproducible không ghi seed.
- **P3-2** reproducible thiếu faults → **RESOLVED**: reproducible ghi faults + fault_iterations + baseline version.
- **P3-3** `--iterations` + soak mâu thuẫn → **RESOLVED**: iterations override thắng; soak chỉ dùng khi iterations None.
- **P3-4** `--save-baseline` không AC → **RESOLVED**: thêm AC16: `--save-baseline` ghi Baseline JSON đúng format.
- **P3-5** strict 3 nơi → **RESOLVED**: strict chỉ trong `ConformanceConfig` (default True); CLI `--no-strict` set config.strict=False.
- **P3-6** evidence_consistent trùng deterministic → **RESOLVED**: gộp — deterministic = digest giống nhau (digest là cơ chế so sánh); bỏ field evidence_consistent riêng.
- **P3-7** Report không expose per-iteration → **RESOLVED**: report thêm `iterations: list[ConformanceIterationSummary]` (summary nhỏ).
- **P3-8** SimulationRunner instance → **RESOLVED**: engine tạo SimulationRunner riêng (default FakeRuntime) — độc lập TestHarness.
- **P3-9** fault_recovery_rate denominator → **RESOLVED**: recovery_rate = recovered / faults_injected (chỉ trên iteration có fault); 0 nếu không fault.

## Kết luận

- [x] Cần sửa trước khi implement — tất cả P1/P2/P3 đã RESOLVED → spec v2.