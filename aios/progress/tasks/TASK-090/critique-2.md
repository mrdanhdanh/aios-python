# Critique vòng 2 — TASK-090 (M13-P1: Harness Coverage)

> Phản biện spec v2 bởi critic agent (độc lập) — 2026-08-17
> Đối chiếu code thật: `harness/contracts.py`, `harness/lifecycle.py` (TRANSITIONS 12 edges/8 keys), `harness/registry.py`, `harness/execution/contracts.py`, `harness/certification/golden.py` (20 GS), `verification/state.py` (VerificationState 8 + VerificationVerdict 5), `harness/runner.py` (emit phase = status.value 6), `kernel/runtime_kernel.py`, `tests/test_harness_kernel.py`.
> **Mức sẵn sàng v2: 3.5/5** — resolution vòng 1 đúng (số liệu 0.896/0.5/0.75 khớp); 2 P1 mới + 8 P2 + 10 P3. Tất cả đã RESOLVED (spec v3).

## P1 — Phải sửa (mới)

### P1-A — Evidence path `path:tests/test_architecture.py` phụ thuộc cwd
- **Vấn đề**: File chỉ tồn tại ở `backend/tests/` — Path("tests/...") = False khi cwd=repo root → VIOLATION rơi xuống covered=False → AC6 fail + AC13 determinism phụ thuộc cwd — chính trust model lại có evidence không tin cậy.
- **RESOLVED**: quy ước evidence cwd-independent: module evidence ưu tiên; path evidence **anchor vào backend root** = `Path(aios_core.__file__).resolve().parents[2] / "tests" / ...` (parents: aios_core→src→backend). VIOLATION dùng path anchored `backend/tests/test_architecture.py`.

### P1-B — AC11 sai trạng thái terminal (DIAGNOSED)
- **Vấn đề**: Runner default `diagnose_on_failure=True` → verify raise → FAILED → on_failure → diagnose → **DIAGNOSED** (test_harness_kernel::test_failure_diagnosed xác nhận). AC11 assert FAILED sẽ fail.
- **RESOLVED**: AC11 → `HarnessRunStatus.DIAGNOSED` (default) / FAILED (nếu `diagnose_on_failure=False`) — test cả 2 nhánh.

## P2 — Nên sửa

### P2-A — Event dimension khai báo không khớp event stream thật
- **RESOLVED**: Event = 6 phase thật runner emit (`status.value`): preparing/validating/running/verifying/completed/failed.

### P2-B — Artifact dimension khai báo không khớp artifact thật
- **RESOLVED**: Artifact = events/report (runner `_build_evidence` tạo 2 kind) — declared 2.

### P2-C — Production dimension formula khi available=True không định nghĩa
- **RESOLVED**: ghi rõ "v1: production = 0.0 bất kể available (chưa có nguồn evidence — M13.1/M16); gate future-proofing"; CLI `--production-tests` luôn dẫn NOT_READY trong v1 (ghi trong help).

### P2-D — Cơ chế persist coverage report chưa rõ
- **RESOLVED**: `_persist` trong verify() (pattern TASK-089/benchmark) — `state_service.update_state(run_id, coverage_report={...})` + `get_report(run_id)`.

### P2-E — Evidence cho item không-negative chưa định nghĩa
- **RESOLVED**: mọi CoverageItem có evidence module-based ưu tiên (`module:aios_core.harness.X`) hoặc path anchored backend root — áp chung quy ước P1-A.

### P2-F — Thiếu AC: covered=False → evidence phải rỗng
- **RESOLVED**: thêm AC18: covered=False → evidence == "".

### P2-G — Thiếu AC exclude-self thực tế
- **RESOLVED**: AC3 làm rõ: register coverage vào registry → build → component vẫn 7.

### P2-H — Thiếu AC validation tham số scorer/CLI
- **RESOLVED**: thêm AC19: min_overall/min_replay ngoài (0,1] → ValueError.

## P3 — Góp ý (đã tích hợp)

- **P3-A** Transition total chưa xác định → **RESOLVED**: total = 12 edges (TRANSITIONS count).
- **P3-B** Failure-mode 3/5 errors tùy ý → **RESOLVED**: include cả 5 errors → failure-mode = 3 fault + 5 errors = 8 items.
- **P3-C** VerificationVerdict (5) loại trừ → **RESOLVED**: ghi chú loại trừ (verification-path dùng Verdict harness 4 + VerificationState INV-035 8; VerificationVerdict thuộc verification/ layer).
- **P3-D** Failure formula mơ hồ → **RESOLVED**: mean(4): failure_mode.ratio, FAIL, EXCEPTION, TIMEOUT.
- **P3-E** Replay coupling verification_path → **RESOLVED**: ghi chú lý do (replay = recompute verdict từ evidence — cùng đường verification).
- **P3-F** reproducible content → **RESOLVED**: {aios_version, registry_harness_ids (sorted), python_version}.
- **P3-G** hard_gates list[dict] → **RESOLVED**: tái dùng `HardGate` từ doctor/contracts.
- **P3-H** "JSON 1 dòng" → **RESOLVED**: "1 JSON document" (indent=2 precedent TASK-089).
- **P3-I** `--production-tests` footgun → **RESOLVED**: help ghi rõ "v1 luôn NOT_READY".
- **P3-J** INV-020b scope coverage/ → **RESOLVED**: không mở rộng scope; os ban tự nguyện.

## Kết luận

- [x] Cần sửa trước khi implement: P1-A, P1-B (bắt buộc) + P2-A..H + P3-A..J — tất cả đã RESOLVED → spec v3.