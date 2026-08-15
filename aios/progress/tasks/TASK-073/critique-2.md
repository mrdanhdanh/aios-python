# TASK-073 — Critique vòng 2

> Critic vòng 2 (độc lập, sau resolve vòng 1).

## Các vấn đề

### C2-01 (P1) — 20 GS trong test riêng + conformance — đừng trùng code
→ **Resolve**: GS definitions (check_fn) ở `golden.py`; `tests/test_certification.py` gọi từng GS; conformance gọi cùng GS registry — 1 nguồn, 2 consumer.

### C2-02 (P2) — Area checks dùng chung component với GS — phân vai rõ
→ **Resolve**: Area = "hệ thống có đúng cơ chế" (structural); GS = "hành vi chạy đúng" (behavioral). Area checks ngắn (doctor/checker/registry), GS sâu (component thật).

### C2-03 (P3) — Verdict conformance: READY chỉ khi cả 9 areas + 5 gates
→ **Resolve**: Verdict = "AIOS 1.0 READY" khi areas all PASS + gates all PASS; else NOT READY + danh sách fail.

## Kết luận
Resolve — **spec v2 đạt, được phép implement**.
