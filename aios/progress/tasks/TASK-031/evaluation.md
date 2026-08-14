# Evaluation — TASK-031 (Test & Simulation, M6-H3)

## Tiêu chí chấp nhận (AC) — đối chiếu
| AC | Yêu cầu | Kết quả |
|----|---------|---------|
| AC1 | Contracts: TestLevel 12, Scenario, ExpectedResult, Fault/FaultType, SimulationOutcome/Status | ✅ `harness/testing/contracts.py` — extra=forbid |
| AC2 | ScenarioLoader: dict + json + yaml (safe_load); lỗi → ScenarioError | ✅ `scenarios.py` — INV-020d safe_load |
| AC3 | FaultInjector: 3 loại fault, inject 1 lần, recovery events | ✅ `faults.py` — retry/fallback/queued |
| AC4 | FakeRuntime: injectable + defaults keyword; không side effect | ✅ `simulation.py` — 7 keyword mappings |
| AC5 | FakeTool deterministic, ghi call | ✅ behavior + last_call |
| AC6 | SimulationRunner pipeline; node model luôn đầu; outcome khớp expect | ✅ plan fake + tool_calls cap 100 |
| AC7 | Policy deny → không tool call, no_policy_bypass; expect deny → SUCCESS blocked-as-expected | ✅ P1-02 |
| AC8 | Mismatch → MISMATCH (runner không raise) | ✅ |
| AC9 | TestHarness qua H1: strict raise TestError; persist trước raise; get_outcome | ✅ pattern H2 AC5 |
| AC10 | Fault scenario: recovery → tests_pass true; hết attempts → ERROR | ✅ ERROR qua retry fail (monkeypatch) |
| AC11 | Config + wiring register "test" | ✅ TestingSettings + runtime_kernel |
| AC12 | Arch INV-020a..d; ≥1290 tests; coverage ≥90% | ✅ 1299 tests, 95.26% |

## Review resolution
- R2-1 (check_policy default allow injectable) ✓; R2-2 (testing→coder) ✓; R3-1..03 ✓
- Critique-1: C1-01 (FakeTool dựng theo capability), C1-02 (node model luôn đầu), C1-04 (metrics counts) ✓
- Critique-2: P1-01 (resource tại node đầu), P1-02 (bỏ BLOCKED, deny semantics), P1-03 (executed trước attempt, tool_calls mọi attempt), P2-01..05 ✓

## Metrics
- Tests: 1210 → **1299** (+89); pass rate 100%; coverage 95.26% (giữ nguyên dù +905 LOC module mới)
- Module mới: `harness/testing/` 7 file (~780 LOC)
- Fix quan trọng: target resolution (fault target "model" bị bỏ qua khi resource đứng trước), tuple unpack, input dict trong tool_calls

## Bài học
1. Fault target resolution phải quét cả danh sách ứng viên — thử target đầu tiên làm fault "model" không bao giờ inject
2. Fault raise trước call_fn → attempt không ghi tool_call — test count phải khớp thiết kế
3. Validation phân tầng: model (shape) vs loader (semantic — request bắt buộc)

## Kết luận
**TASK-031 HOÀN TẤT** — 12/12 AC, hard gate đầy đủ (spec v3 → critique ×2 → review → implement → test → evaluate).
