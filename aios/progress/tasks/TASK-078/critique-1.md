# TASK-078 — Critique vòng 1 (spec)

> **Critic**: AIOS Orchestrator (vòng phản biện độc lập)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved (đầy đủ)

## P1 — Phải sửa trước khi implement

### C1-01. Thiếu định nghĩa "verification mechanism" & cơ chế đăng ký
Spec nói "VerificationGate chặn mọi mechanism" nhưng không định nghĩa mechanism là gì, đăng ký ở đâu, làm sao biết toàn bộ mechanism được cover.
→ **Resolve**: thêm `VerificationMechanism` contract (id, name, version, `check() -> VerificationOutcome`); `VerificationGate` nhận list mechanism (injectable, default: security-check, contract-check, harness-execution); conformance gate F gọi gate với đủ mechanism mặc định. AC6/AC7 đã đúng hướng — bổ sung chi tiết vào spec §2.2.

### C1-02. Mâu thuẫn tiềm ẩn: `CheckResult.skipped=True` hiện tại vẫn có `passed` field — ai là nguồn sự thật?
`harness/execution/contracts.py::CheckResult` có cả `passed: bool` và `skipped: bool`. Nếu `passed=True, skipped=True` → fail-closed phải ưu tiên skipped. Spec chưa nói rõ quy tắc ưu tiên.
→ **Resolve**: quy tắc ưu tiên: `skipped=True` → KHÔNG pass bất kể `passed` (fail-closed); `error` → thêm field `error: str = ""` — nếu error non-empty → không pass. Ghi vào spec §2.3.

### C1-03. Chưa xác định tác động tới test hiện có (regression risk)
Full suite 1939 tests — đổi normalize có thể làm vỡ các test mong đợi `skipped` không ảnh hưởng verdict. Cần khảo sát trước.
→ **Resolve**: thêm bước "khảo sát usage `skipped` trong tests" vào tasks.md; nếu có test cũ phụ thuộc hành vi cũ → update test (fail-closed là đúng theo INV-035). Đưa vào AC12 (full suite xanh).

## P2 — Nên sửa

### C2-01. INCONCLUSIVE handling trong H2 VerificationResult chưa đầy đủ
`Verdict.INCONCLUSIVE` tồn tại — fail-closed nghĩa là INCONCLUSIVE không bao giờ được map thành PASS. Spec có nói "INCONCLUSIVE không thành PASS" ở AC nhưng chưa nói verdict mới sinh ra từ đâu.
→ **Resolve**: `fail_closed_normalize` là nơi duy nhất sinh verdict từ state; `build_result` H2 giữ nguyên nhưng thêm normalize check: nếu bất kỳ `CheckResult` nào `skipped=True` → verdict không thể PASS (tối đa INCONCLUSIVE). Ghi rõ vào spec §2.3.

### C2-02. CLI tên `verify-state` có thể xung đột naming với `verification` harness
→ **Resolve**: đổi thành `aiagent verify-state` vẫn OK (subcommand mới trong cli, không trùng). Giữ nguyên, ghi chú trong tasks.md kiểm tra tên không trùng.

### C2-03. Audit retroactive: nguồn dữ liệu commit webgame ở đâu?
→ **Resolve**: audit dùng `git log --all --oneline` lọc commit liên quan webgame (games/yuniebel*, skills/*, PR #1/#4) + ghi nhận findings; chỉ cần chứng minh quy trình, không cần exhaustive.

## P3 — Ghi nhận

### C3-01. Nên thêm test cho "mọi biến thể" chuyển đổi bị cấm (SKIP→PASS, UNKNOWN→PASS, MISSING→PASS, NOT_EXECUTED→PASS, PASS→FAIL?)
→ Resolve: bảng chuyển đổi đầy đủ 8×8 trong unit test (AC3) — có lợi cho maintenance.

### C3-02. Verdict model H2 có `PASS_WITH_WARNING` — có nên giữ?
→ Resolve: giữ nguyên (không đụng); fail-closed chỉ áp dụng cho SKIPPED/error boundary.

### C3-03. Docs cần cập nhật (Constitution 1.0 amendment INV-035)?
→ Resolve: ghi nhận — cập nhật `docs/architecture/AIOS-1.0.md` + constitution doc trong phase implement (thuộc M11 compliance).

## Kết luận
Spec khả thi sau khi resolve C1-01..03 + C2-01..03 → chuyển vòng 2.
