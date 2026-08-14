# Critique-1+2 — TASK-033 (spec v1→v2)

**Critic**: orchestrator tự phản biện 2 vòng gộp (độc lập — ghi nhận; spec v1 đã học từ critique các task trước nên vòng 2 phát hiện ít)

## Vòng 1 — P1
- **C1-01 — delta % khi baseline_avg = 0**: chia 0 → delta 0 (chốt) — tránh ZeroDivisionError.
- **C1-02 — subset chung deterministic**: chỉ so sánh scenario_ids có trong cả new + baseline — sort ids trước (deterministic).
- **C1-03 — hướng xấu cần đúng chiều**: QUALITY regress khi delta < max_delta (âm); COST/LATENCY/TOKEN/FAILURE_RATE/VIOLATIONS regress khi delta > max_delta (dương). Chốt bảng.

## Vòng 1 — P2
- C2-01 — `RegressionGate.evaluate` nhận list RunResult mới — signature `evaluate(new_results, baseline)`; Baseline.runs dict key scenario_id.
- C2-02 — failure_rate tính trên subset chung (không phải toàn bộ new) — deterministic.
- C2-03 — policy_violations aggregate = sum; pp delta so avg per scenario (total/len) — chốt: dùng per-scenario avg (violations/scenario).
- C2-04 — report.metrics chứa aggregate avgs (deterministic — không duration/timestamp).

## Vòng 2 — P1
- **P1-01 — Baseline rỗng**: evaluate với baseline trống → không có subset → findings trống → gate_passed True (không regress khi chưa có baseline — lần chạy đầu là baseline mới). Chốt + test.
- **P1-02 — benchmark.py raise GateBlockedError phải sau persist** (pattern H2/H3 AC5 — INV-021 evidence-first).

## Vòng 2 — P2
- P2-01 — rules default từ settings khi gate tạo không truyền rules (wiring dùng settings). 
- P2-02 — GateBlockedError thừa kế BenchmarkError (bắt chung được).
- P2-03 — `can_release` = not any(regressed).

## Resolve (phản ánh vào implement)
- delta: baseline==0 → 0; subset sort; bảng hướng; avg trên subset; findings rỗng → gate_passed True; persist trước raise; GateBlockedError(BenchmarkError); wiring rules từ settings.
