# TASK-073 — Test + Evaluation (Certification Suite 1.0 — task lớn nhất M10)

## Test — `tests/test_certification.py` **9/9 pass**
- 9 CertificationArea đủ (AC1)
- 9 area checks thật — mọi area PASS (AC2)
- 20 GoldenScenario đủ id + chạy component thật (AC3)
- ConformanceReport.ready (AC4) + 5 gates đúng định nghĩa (AC5)
- CLI conformance (AC6)

## CLI thật: `aiagent conformance`
```
✓ architecture (scanner violations=0) · ✓ autonomy · ✓ contracts (breaking=0)
✓ ecosystem · ✓ enterprise · ✓ harness (6) · ✓ policy · ✓ runtime (100/100) · ✓ security
Golden Scenarios: 20/20 PASS
✓ gate_a_architecture ✓ gate_b_security ✓ gate_c_contract
✓ gate_d_reliability ✓ gate_e_autonomous
Result: AIOS 1.0 READY
```

## Full suite: **1939 passed** (AC7).

## Evaluation — 8/8 AC ĐẠT
| AC | Kết quả |
|----|---------|
| AC1 9 areas | ✅ |
| AC2 area checks thật | ✅ |
| AC3 20 GS | ✅ |
| AC4 ready | ✅ |
| AC5 5 gates | ✅ |
| AC6 CLI | ✅ |
| AC7 regression | ✅ |
| AC8 DoD | ✅ |

## Bài học
1. **Certification cần layer rule riêng** (harness/certification) — hệ thống kiểm chứng toàn cục phải đọc mọi component; rule mới + exempt trong scanner.
2. API thật khác spec giả định: PluginManager(db_path, event_sink), GoalContract(permissions list), ExperimentationEngine(evaluate_fn bắt buộc), agents dict dùng "id".
3. GS là "release phải pass" — 1 nguồn, 2 consumer (conformance + pytest).
