# TASK-070 — Critique vòng 1

> Critic (tự). Phản biện spec TASK-070.

## Các vấn đề

### C1-01 (P1) — "Check giả": phải chứng minh check kiểm tra cơ chế thật
Nếu check chỉ `return PASS` khi module import được → vô nghĩa.
→ **Resolve**: Mỗi check có evidence cụ thể: (a) module import được, (b) assert một literal/flag trong source (vd `"class CredentialBroker" in src`), (c) config flag enabled. Test AC3 assert evidence non-empty + chứa nội dung cụ thể.

### C1-02 (P2) — FAIL nào là critical (block)?
→ **Resolve**: 4 items critical: secrets, audit, plugin_signing, sandbox — FAIL → blocking=True (Gate B: critical=0, high=0). Còn lại FAIL → warning-level (báo cáo, không block) — ghi rõ trong contracts.

### C1-03 (P2) — SecurityContext nhận gì?
→ **Resolve**: `SecurityContext(kernel=None, settings=None)` — check tự lazy-import cần thiết; kernel chỉ dùng để resolve nếu có. Không bắt buộc DI.

### C1-04 (P3) — Config flag cho identity enabled ở đâu?
→ **Resolve**: EnterpriseSettings.enabled (kiểm tra thực tế field tồn tại) — evidence ghi rõ đường đi field.

## Kết luận
Resolve vào spec v2.
