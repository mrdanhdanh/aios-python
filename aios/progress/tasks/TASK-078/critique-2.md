# TASK-078 — Critique vòng 2 (spec)

> **Critic**: AIOS Orchestrator (vòng 2 — phản biện độc lập sau khi resolve vòng 1)
> **Ngày**: 2026-08-16
> **Trạng thái**: resolved (đầy đủ)

## P1 — Phải sửa trước khi implement

### C2-01. `VerificationOutcome` chưa định nghĩa schema — mechanism check() trả về gì?
Spec nói `check() -> VerificationOutcome` nhưng chưa có field cụ thể. Nếu mechanism trả lỏng lẻo thì gate không đáng tin.
→ **Resolve**: `VerificationOutcome` (pydantic, extra=forbid): `mechanism_id: str`, `state: VerificationState`, `verdict: VerificationVerdict` (PASS/FAIL/ERROR/BLOCKED/INCONCLUSIVE), `evidence: str = ""`, `detail: dict = {}`. Gate quy tắc: verdict PASS ⟺ state == PASS (nếu state non-terminal mà verdict PASS → VIOLATION, fail-closed).

### C2-02. Gate F conformance: nếu một mechanism không chạy được (exception) thì sao?
→ **Resolve**: mechanism `check()` raise exception → gate coi như BLOCKED (fail-closed, không PASS). Đây chính là tinh thần INV-035. Thêm test.

### C2-03. Chưa rõ `aiagent verify-state` lấy trạng thái fail-closed từ đâu (state thật hay cấu hình)
→ **Resolve**: CLI chạy `VerificationGate` với default mechanisms thật (SecurityChecker, ContractChecker, VerificationHarness config) → in state model + kết quả từng mechanism. Không cần cấu hình riêng.

## P2 — Nên sửa

### C2-04. Conformance area `verification` cần check cái gì cụ thể (structural)?
→ **Resolve**: area check = (1) module `verification` importable + có `VerificationGate`, (2) gate với mechanism mock non-terminal → verdict không PASS (chạy thật component, không hard-code PASS — theo R1 conformance). Đủ mạnh, deterministic.

### C2-05. `CheckResult.error` field mới — pydantic extra=forbid sẽ vỡ nếu code cũ dựng CheckResult không có error?
→ **Resolve**: thêm field với default `""` (backward compatible); không vi phạm extra=forbid vì field được khai báo. Test hiện có vẫn pass.

### C2-06. SecurityChecker normalize: hiện tại report có `failures` list — skip/error nằm ở đâu?
→ **Resolve**: khảo sát `security/contracts.py` khi implement; nếu không có khái niệm skipped → bổ sung `skipped: list[str]` vào report (fail-closed: skipped không được đếm là pass). Ghi vào tasks.md.

## P3 — Ghi nhận

### C2-07. Audit retroactive: có cần tạo action CI fail-closed gate?
→ Resolve: P0 scope có "CI fail-closed gate" — hiện repo chưa có CI test workflow cho visual; ghi nhận vào audit doc như đề xuất (không thêm workflow mới trong task này — vượt scope, để P4 R7 static deploy xử lý CI). Ghi rõ trong evaluation.

### C2-08. Version bump AIOS 1.0 → M11?
→ Resolve: metadata version bump là compliance M11 (Constitution amendment) — làm trong task này như phần nhỏ (update metadata version), chi tiết trong tasks.md.

## Kết luận
Spec v2 sau resolve C2-01..06 + P3 ghi nhận → **APPROVED — được phép implement** (đủ 2 vòng critique).
