# TASK-073 — M10-F8: Certification Suite 1.0 (task lớn nhất M10)

## Mục tiêu
PLAN §M10-31..33: 13 categories test + Golden Scenarios GS-001..020 + `aiagent conformance` (9 areas PASS → AIOS 1.0 READY) + 5 release gates (A Architecture / B Security / C Contract / D Reliability / E Autonomous).

## Phạm vi
- `harness/certification/`:
  - `contracts.py`: `CertificationArea` (9: Architecture/Contracts/Runtime/Policy/Security/Autonomy/Harness/Enterprise/Ecosystem) + `AreaResult` (area, status PASS/FAIL, evidence) + `ConformanceReport` (areas + ready) + `GoldenScenario` (id GS-xxx, name, category, check_fn(ctx)->bool + evidence)
  - `checks.py`: 9 area checks dùng component thật: Architecture (arch_health scanner 0 violations + DoctorFirstClass), Contracts (ContractChecker breaking=0), Runtime (DoctorFirstClass runtime/events pass), Policy (PolicyService pre-check allow), Security (SecurityChecker không blocking), Autonomy (Governor gate + KillSwitch preflight), Harness (harness_registry 6), Enterprise (EnterpriseManager present), Ecosystem (plugin/ecosystem registry)
  - `golden.py`: 20 GoldenScenario GS-001..020 (chat, coding, workflow, tool fail, agent fail, policy deny, human approval, checkpoint-resume, autonomous goal, long-horizon, multi-agent, plugin install, incompat, upgrade, rollback, security violation, arch violation, memory learning, self-improvement, emergency stop) — check deterministic qua component thật/harness
  - `conformance.py`: `ConformanceRunner.run()` → ConformanceReport + `release_gates()` → 5 GateResult (A–E)
- CLI: `aiagent conformance` (9 areas + gates + verdict READY/NOT READY)
- Golden Scenarios chạy như test riêng (`tests/test_certification.py`) — mỗi GS là 1 test

## Ngoài phạm vi
- Không tạo hệ thống test mới (dùng pytest + harness hiện có)
- Không chạy LLM thật

## Input
- `observability/arch_health.py`, `contracts/check.py`, `security/`, `observability/slo.py`, `cli/doctor.py`, `kernel/kill_switch.py`, `harness/registry`, `autonomous/safety.py`

## Output
- `backend/src/aios_core/harness/certification/{__init__,contracts,checks,golden,conformance}.py` + CLI + `tests/test_certification.py`

## Tiêu chí chấp nhận (AC)
| # | Tiêu chí | Cách kiểm tra |
|---|----------|---------------|
| AC1 | 9 CertificationArea đủ tên | Test |
| AC2 | 9 area checks chạy thật (component thật, không hard-code) — mọi area PASS trên hệ thống hiện tại | Test + CLI |
| AC3 | 20 GoldenScenario GS-001..020 đủ id + chạy được (check_fn deterministic) | Test 20 GS |
| AC4 | ConformanceReport.ready = mọi area PASS | Test |
| AC5 | 5 release gates đúng định nghĩa (A: INV=0; B: critical=0+high=0; C: breaking=0; D: critical scenario failures=0; E: bypass=0) | Test từng gate |
| AC6 | `aiagent conformance` in 9 areas + 5 gates + verdict | CLI thật |
| AC7 | Regression full suite | pytest |
| AC8 | Đóng DoD | checklist |

## Ghi chú
- Golden Scenarios = "release phải pass" — chạy trong conformance (deterministic subset) + test riêng.
- Gate E: policy_bypass (SLO), budget bypass (Governor), kill-switch bypass (KillSwitch.preflight chưa từng deny ngoài emergency).
