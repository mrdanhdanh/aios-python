# TASK-078 — Tasks breakdown (checklist)

> Bắt buộc đủ: spec v2 (resolved critique ×2) → implement → test → evaluate.

## Khảo sát (trước implement)

- [ ] K1. Khảo sát `harness/execution/contracts.py` + `pipeline.py` (build_result): usage `CheckResult.skipped`, `Verdict`
- [ ] K2. Khảo sát `security/contracts.py` + `checks.py`: report structure, có khái niệm skip không
- [ ] K3. Khảo sát `contracts/check.py` (ContractChecker): report structure
- [ ] K4. Khảo sát CLI: chỗ đăng ký subcommand (`workflow/cli.py` hoặc `cli/*`), naming conflict `verify-state`
- [ ] K5. Khảo sát tests hiện có dùng `skipped=True` hoặc `INCONCLUSIVE` (regression risk — C1-03)

## Implement

- [ ] I1. Tạo `backend/src/aios_core/verification/__init__.py` + `state.py` (VerificationState + VerificationVerdict + helpers)
- [ ] I2. `fail_closed_normalize()` — bảng chuyển đổi 8×8
- [ ] I3. `VerificationOutcome` (pydantic extra=forbid) + `VerificationMechanism` contract
- [ ] I4. `VerificationGate` — check mechanisms, exception → BLOCKED, violation detect
- [ ] I5. Harness execution: `CheckResult.error: str = ""` + quy tắc ưu tiên skipped/error (build_result normalize)
- [ ] I6. Security: normalize skip/error → không PASS + bổ sung skipped vào report (nếu chưa có)
- [ ] I7. Contract-check: check bị skip/error không tính PASS
- [ ] I8. Conformance: area `verification` (structural — module + gate chạy mock non-terminal) + gate `gate_f_verification`
- [ ] I9. CLI `aiagent verify-state` (chạy gate thật) + conformance format update
- [ ] I10. Constitution/compliance nhỏ: metadata version bump (AIOS 1.0 → M11, ghi chú) — tách commit riêng
- [ ] I11. Retroactive audit: `git log --all` lọc commit webgame/visual → `implementation/audit.md` (đánh giá INV-035, không sửa code game)

## Test

- [ ] T1. Unit test state model (AC1, AC2)
- [ ] T2. Unit test normalize bảng 8×8 (AC3)
- [ ] T3. Unit test gate: violation skip→PASS bị chặn + exception → BLOCKED (AC4)
- [ ] T4. Unit test CheckResult skipped/error → không PASS (AC5)
- [ ] T5. Unit test security + contract normalize (AC8, AC9)
- [ ] T6. Chạy `aiagent conformance` thật (AC6, AC7)
- [ ] T7. Chạy `aiagent verify-state` + `security-check` + `contract-check` thật (AC10, AC8, AC9)
- [ ] T8. Full backend suite (AC12) — không regression

## Evaluate

- [ ] E1. Đối chiếu 12 AC
- [ ] E2. Cập nhật LOG.md + PROGRESS.md + commit
