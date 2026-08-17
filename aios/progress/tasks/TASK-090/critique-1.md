# Critique vòng 1 — TASK-090 (M13-P1: Harness Coverage)

> Phản biện spec v1 bởi critic agent (độc lập) — 2026-08-17
> Đối chiếu code thật: `harness/{contracts,lifecycle,registry,runner}.py`, `harness/execution/contracts.py`, `harness/certification/golden.py`, `verification/state.py`, `kernel/runtime_kernel.py`, `tests/test_harness_kernel.py`.
> **Mức sẵn sàng v1: 3/5** — 3 P1 + 6 P2 + 3 P3. Tất cả đã RESOLVED (spec v2 → v3).

## P1 — Phải sửa

### P1-1 — Fail-closed NOT_READY KHÔNG kích hoạt với ngưỡng mặc định
- **Vấn đề**: Tính với default: Replay = mean(1.0, 0.0) = 0.5; overall = 0.911 > 0.8 → **READY luôn đạt** dù 2 negative-path chưa cover — mâu thuẫn fail-closed.
- **RESOLVED**: chọn **(a) fail-closed thật** — hard gate `replay >= 0.75`: v1 Replay=0.5 → **NOT_READY** (CLI exit 1). READY chỉ sau TASK-091. AC8 sửa: default → overall 0.896 nhưng Replay=0.5 < 0.75 → NOT_READY.

### P1-2 — Hard gate `production >= 0.5` vô nghĩa (placeholder luôn pass)
- **Vấn đề**: Production = mean(artifact, state) = 1.0 → gate luôn pass.
- **RESOLVED**: production = **0.0** khi chưa có production tests + gate conditional + production **excluded khỏi overall** v1. AC7 sửa.

### P1-3 — Self-counting: coverage harness đếm chính nó trong Component
- **Vấn đề**: `CoverageHarness` đăng ký vào chính registry nó đọc → 8 items (gồm coverage) — không deterministic + tự chứng nhận.
- **RESOLVED**: builder **exclude** id="coverage". AC3: 7 items cố định.

## P2 — Nên sửa

### P2-1 — Event/Artifact thiếu nguồn sự thật (str tự do, không enum)
- **RESOLVED**: declared list rõ: Event = lifecycle phases; Artifact = evidence/report/verdict (sau vòng 2 chỉnh còn events/report — phase thật).

### P2-2 — Contract dimension mơ hồ nguồn enumeration
- **RESOLVED**: liệt kê cụ thể 21 contract classes (Check, CheckResult, VerificationTask, Verdict, Scenario, ExpectedResult, Fault, SimulationOutcome, GoldenScenario, ConformanceConfig, ConformanceReport, DoctorResult, ReadinessReport, Baseline, RunResult, BenchmarkReport, HarnessRun, HarnessResult, HarnessReport, HarnessArtifact, HarnessEvent).

### P2-3 — Tham số `doctor` chết
- **RESOLVED**: bỏ tham số doctor khỏi `HarnessReadinessScorer.score()` (reserved M13.1/M16).

### P2-4 — Thiếu AC (determinism, metrics, status 2 điều kiện, round-trip, edge case, JSON, CoverageError hierarchy, đủ keys)
- **RESOLVED**: thêm AC13 (determinism cross-run), AC14 (metrics + summary), AC15 (status), AC16 (round-trip + hierarchy + keys), AC17 (registry rỗng không div0 + JSON 1 document).

### P2-5 — Evidence negative-path không được kiểm chứng tồn tại
- **RESOLVED**: AC6 bổ sung: evidence non-empty + tồn tại (importlib.util.find_spec / pathlib.Path.exists anchored backend root — không dùng os INV-020b).

### P2-6 — Verdict double-count (State + Verification-path)
- **RESOLVED**: Verdict chỉ thuộc Verification-path; State = HarnessRunStatus + ConformanceStatus + SimulationStatus.

## P3 — Góp ý (đã tích hợp)

- **P3-1** id="coverage" trùng ngữ nghĩa → docstring/CLI help phân biệt rõ.
- **P3-2** 2 status song song → bỏ status khỏi HarnessCoverageReport (readiness quyết định).
- **P3-3** min_negative_ratio 0.75 biên giới → kế hoạch tăng 1.0 sau TASK-091.

## Kết luận

- [x] Cần sửa trước khi implement — tất cả đã RESOLVED → spec v3.
- Quyết định chốt: **fail-closed thật** — v1 coverage trả NOT_READY (replay gate 0.5 < 0.75) cho tới khi TASK-091 cover đủ negative-path + replay.