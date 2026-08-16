# TASK-078 — M11-P0: R2 INV-035 Verification Fail-Closed (Core Invariant)

> **Milestone**: M11-P0 (Issue #4) — Verification Integrity
> **Ngày**: 2026-08-16
> **Owner**: AIOS Orchestrator
> **Tham chiếu**: `docs/proposals/m11-creative-engineering.md` §R2, PLAN.md §M11, Issue #4

## 1. Mục tiêu

Biến **Verification Fail-Closed** thành Core Invariant hệ thống (INV-035):

> *Không một verification mechanism nào được phép chuyển trạng thái `UNKNOWN / NOT EXECUTED / MISSING EVIDENCE` thành `PASS`.*

Động lực thực tế: visual test báo "17/17 PASS" nhưng thực chất `toHaveScreenshot` bị skip do thiếu ảnh ref — false-positive có thật đã xảy ra. M10 `aiagent conformance` chưa enforce fail-closed.

## 2. Phạm vi (IN scope)

1. **Verification State Model** — contract chính thức:
   - Terminal success duy nhất: `PASS`
   - Terminal failure: `FAIL | ERROR | BLOCKED`
   - Non-terminal (KHÔNG được coi là success): `UNKNOWN | NOT_EXECUTED | MISSING_EVIDENCE | SKIPPED`
   - Cấm chuyển đổi: `SKIPPED → PASS`, `UNKNOWN → PASS`, `MISSING_EVIDENCE → PASS` (mọi biến thể khác cũng fail-closed)
2. **Verification Kernel** (`backend/src/aios_core/verification/` package mới):
   - `VerificationState` enum + `VerificationOutcome` (verdict + state + evidence)
   - `fail_closed_normalize()` — chuẩn hóa kết quả từ mọi nguồn (skip/error/missing → non-terminal) → verdict fail-closed
   - `VerificationMechanism` contract — mỗi mechanism (id, name, version, `check() -> VerificationOutcome`) đăng ký để gate cover toàn bộ
   - `VerificationOutcome` (pydantic, extra=forbid): `mechanism_id: str`, `state: VerificationState`, `verdict: VerificationVerdict` (PASS/FAIL/ERROR/BLOCKED/INCONCLUSIVE), `evidence: str = ""`, `detail: dict = {}` — gate quy tắc: verdict PASS ⟺ state == PASS; state non-terminal mà verdict PASS → VIOLATION (fail-closed)
   - `VerificationGate` — nhận list mechanism (injectable, default: security-check, contract-check, harness-execution); check từng mechanism → fail-closed nếu bất kỳ mechanism nào có verdict PASS khi state non-terminal; **mechanism check() raise exception → BLOCKED (fail-closed)**
   - **Quy tắc ưu tiên (nguồn sự thật)**: `skipped=True` → KHÔNG pass bất kể `passed`; `error` non-empty → KHÔNG pass bất kể `passed`; `passed=True` chỉ có hiệu lực khi `skipped=False` và `error=""`
3. **Enforcement tích hợp** (INV-035 áp dụng đồng nhất):
   - `harness/execution/contracts.py`: `CheckResult.skipped=True` → KHÔNG được coi là pass (bất kể `passed`); thêm `error: str = ""` — non-empty → không pass; `Verdict.INCONCLUSIVE` không thành PASS; `build_result`: nếu bất kỳ check nào skipped/error → verdict tối đa INCONCLUSIVE (không PASS)
   - `harness/certification/checks.py`: thêm area **`verification`** (INV-035: fail-closed model tồn tại + enforce)
   - `harness/certification/conformance.py`: thêm release gate **`gate_f_verification`** (mọi verification mechanism fail-closed; không có `SKIPPED → PASS`)
   - `security/checks.py`: normalize skip/error → non-terminal (không báo PASS)
   - `contracts/check.py`: ContractChecker report → các check bị skip/error không tính PASS
4. **CLI/DX**:
   - `aiagent conformance` → hiển thị area `verification` + gate `gate_f_verification`
   - `aiagent verify-state` — chạy `VerificationGate` với default mechanisms thật (SecurityChecker, ContractChecker, VerificationHarness config) → in state model + kết quả từng mechanism
5. **Retroactive audit** — rà soát các commit webgame/visual đã merge, ghi nhận vi phạm INV-035 tiềm năng, đưa vào `implementation/audit.md`

## 3. OUT of scope

- R3 DeterministicHarness (TASK-079), R1 VisualEvidence (TASK-080) — phase sau
- Thay đổi Verdict hiện có của H2 (chỉ normalize skip/error boundary)
- Sửa code game/webgame — audit chỉ ghi nhận, không sửa

## 4. Input / Output

- **Input**: các verification mechanism hiện có (harness execution, conformance, security-check, contract-check)
- **Output**: package `verification/` + integration + test + audit doc

## 5. Tiêu chí chấp nhận (AC)

| # | AC | Cách kiểm tra |
|---|----|---------------|
| AC1 | `VerificationState` có đủ 8 trạng thái (PASS, FAIL, ERROR, BLOCKED, UNKNOWN, NOT_EXECUTED, MISSING_EVIDENCE, SKIPPED) + `is_terminal_success` chỉ đúng với PASS | unit test |
| AC2 | `is_non_terminal()` đúng cho 4 non-terminal; `is_failure()` đúng cho 3 failure | unit test |
| AC3 | `fail_closed_normalize()`: SKIPPED/UNKNOWN/NOT_EXECUTED/MISSING_EVIDENCE → KHÔNG PASS (thành INCONCLUSIVE/BLOCKED); PASS → PASS; FAIL/ERROR/BLOCKED giữ nguyên | unit test — bảng chuyển đổi đầy đủ 8×8 |
| AC4 | `VerificationGate.check()` chặn mọi mechanism có verdict PASS khi state non-terminal; default mechanisms (security/contract/harness) đăng ký đủ; mechanism exception → BLOCKED | unit test (mô phỏng skip → PASS bị chặn + exception) |
| AC5 | `CheckResult` (harness execution): `skipped=True` → verdict không PASS; `error` non-empty → không PASS (bất kể `passed`) | unit test |
| AC6 | Conformance area `verification` (INV-035): module importable + gate với mechanism mock non-terminal → verdict không PASS (structural, không hard-code) | chạy `aiagent conformance` thật |
| AC7 | Conformance gate `gate_f_verification` PASS khi hệ thống fail-closed | chạy `aiagent conformance` thật |
| AC8 | SecurityChecker: check bị skip/error không báo PASS (normalize); skipped list bổ sung vào report | unit test + chạy `aiagent security-check` |
| AC9 | ContractChecker: check bị skip/error không tính PASS | unit test + chạy `aiagent contract-check` |
| AC10 | CLI `aiagent verify-state` hiển thị state model + trạng thái fail-closed (gate thật) | chạy CLI thật |
| AC11 | Retroactive audit doc có danh sách commit webgame/visual + đánh giá INV-035 | đọc file |
| AC12 | Full backend suite xanh (không regression) | pytest |

## 6. Nguồn tham khảo

- Proposal M11 §R2 + §7 (P0 scope) + Verification State Model
- M10: `harness/certification/conformance.py`, `harness/execution/verification.py`, `security/checks.py`, `contracts/check.py`
