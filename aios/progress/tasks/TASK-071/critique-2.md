# TASK-071 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P2) — Doctor không được khởi tạo DB mới lung tung
Một số check (memory/knowledge/audit) tạo DB file — doctor chạy nhiều lần tạo rác.
→ **Resolve**: Dùng db_path mặc định từ settings (không tạo file mới); check chỉ connect + query 1 bảng — file đã tồn tại từ wiring. Nếu chưa tồn tại → WARN (chưa dùng) không FAIL.

### C2-02 (P3) — system status nên gom emergency flag
→ **Resolve**: system status in: version (aios_core.__version__), services count, emergency flag (KillSwitch state), uptime-ish (không bắt buộc).

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
